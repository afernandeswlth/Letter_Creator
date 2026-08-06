"""
Letter history store (Supabase).

Colocated in engine/ so it ships with the Vercel Python bundle (vercel.json
includeFiles: "engine/**"). This is the *web persistence* layer, not PDF logic:
whenever a letter is generated for download or an email draft, we record its
metadata in a Supabase Postgres table and upload the PDF to a Supabase Storage
bucket, so the dashboard's "Recent Letters" can list (and re-download) them.

Everything here is BEST-EFFORT and fail-safe: if Supabase isn't configured, or a
call fails, we log and carry on — persistence must never break letter delivery.

Config (server-side env vars — never exposed to the browser):
  SUPABASE_URL                e.g. https://xxxx.supabase.co
  SUPABASE_SERVICE_ROLE_KEY   the service_role secret (bypasses RLS)
  SUPABASE_LETTERS_TABLE      default 'letters'
  SUPABASE_LETTERS_BUCKET     default 'letters'
"""
import os
import sys
import uuid

LABELS = {
    'welcome': 'Welcome Letter',
    'approval': 'Formal Approval Letter',
    'commencement': 'Commencement Letter',
    'pre-approval': 'Pre-Approval Letter',
    'conditional-approval': 'Conditional Approval Letter',
    'discharge': 'Discharge Confirmation Letter',
    'custom': 'Custom Letter',
}


def _cfg():
    url = (os.environ.get('SUPABASE_URL') or '').rstrip('/')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or ''
    if not url or not key:
        return None
    return {
        'url': url,
        'key': key,
        'table': os.environ.get('SUPABASE_LETTERS_TABLE', 'letters'),
        'bucket': os.environ.get('SUPABASE_LETTERS_BUCKET', 'letters'),
    }


def is_configured():
    return _cfg() is not None


def _headers(cfg, extra=None):
    h = {'apikey': cfg['key'], 'Authorization': 'Bearer ' + cfg['key']}
    if extra:
        h.update(extra)
    return h


def _warn(msg):
    print('[store] ' + msg, file=sys.stderr)


def _strip_title(name):
    import re
    return re.sub(r'^(mr|mrs|ms|miss|dr)\.?\s+', '', (name or '').strip(), flags=re.I)


def form_meta(letter_type, brand, values):
    """Derive display metadata for a form-driven letter from its field values."""
    v = values or {}
    customer = (v.get('borrowers') or v.get('recipientName') or v.get('customerNames')
                or v.get('builderName') or '').strip()
    reference = (v.get('loanAccountNumber') or v.get('applicationNumber')
                 or v.get('accountNumbers') or '').strip()
    return {
        'letter_type': letter_type,
        'type_label': LABELS.get(letter_type, 'Letter'),
        'brand': brand,
        'customer': _strip_title(customer),
        'reference': reference or None,
    }


def save_letter(meta, pdf_bytes, filename, status):
    """Upload the PDF and insert a metadata row. Best-effort; returns the id or
    None. Never raises."""
    cfg = _cfg()
    if not cfg:
        return None
    try:
        import requests
        rec_id = str(uuid.uuid4())
        pdf_path = rec_id + '.pdf'

        up = requests.post(
            '{url}/storage/v1/object/{bucket}/{path}'.format(url=cfg['url'], bucket=cfg['bucket'], path=pdf_path),
            headers=_headers(cfg, {'Content-Type': 'application/pdf', 'x-upsert': 'true'}),
            data=pdf_bytes, timeout=20)
        if not up.ok:
            _warn('storage upload failed {}: {}'.format(up.status_code, up.text[:200]))
            return None

        row = {
            'id': rec_id,
            'letter_type': meta.get('letter_type'),
            'type_label': meta.get('type_label'),
            'brand': meta.get('brand'),
            'customer': meta.get('customer') or None,
            'reference': meta.get('reference') or None,
            'status': status,
            'filename': filename,
            'pdf_path': pdf_path,
        }
        ins = requests.post(
            '{url}/rest/v1/{table}'.format(url=cfg['url'], table=cfg['table']),
            headers=_headers(cfg, {'Content-Type': 'application/json', 'Prefer': 'return=minimal'}),
            json=row, timeout=15)
        if not ins.ok:
            _warn('row insert failed {}: {}'.format(ins.status_code, ins.text[:200]))
            return None
        return rec_id
    except Exception as e:  # noqa: BLE001
        _warn('save_letter error: {}'.format(e))
        return None


def recent_letters(limit=20):
    """Return the most recent letter rows (newest first). [] if unconfigured."""
    cfg = _cfg()
    if not cfg:
        return []
    try:
        import requests
        r = requests.get(
            '{url}/rest/v1/{table}'.format(url=cfg['url'], table=cfg['table']),
            headers=_headers(cfg),
            params={'select': '*', 'order': 'created_at.desc', 'limit': str(limit)},
            timeout=15)
        if not r.ok:
            _warn('recent select failed {}: {}'.format(r.status_code, r.text[:200]))
            return []
        return [_public_row(x) for x in r.json()]
    except Exception as e:  # noqa: BLE001
        _warn('recent_letters error: {}'.format(e))
        return []


def _public_row(x):
    return {
        'id': x.get('id'),
        'letterType': x.get('letter_type'),
        'typeLabel': x.get('type_label'),
        'brand': x.get('brand'),
        'customer': x.get('customer'),
        'reference': x.get('reference'),
        'status': x.get('status'),
        'filename': x.get('filename'),
        'createdAt': x.get('created_at'),
    }


def signed_url(letter_id, expires_in=3600):
    """A short-lived download URL for a stored letter's PDF, or None."""
    cfg = _cfg()
    if not cfg:
        return None
    try:
        import requests
        r = requests.get(
            '{url}/rest/v1/{table}'.format(url=cfg['url'], table=cfg['table']),
            headers=_headers(cfg),
            params={'select': 'pdf_path,filename', 'id': 'eq.' + str(letter_id), 'limit': '1'},
            timeout=15)
        rows = r.json() if r.ok else []
        if not rows:
            return None
        path = rows[0].get('pdf_path')
        if not path:
            return None
        s = requests.post(
            '{url}/storage/v1/object/sign/{bucket}/{path}'.format(url=cfg['url'], bucket=cfg['bucket'], path=path),
            headers=_headers(cfg, {'Content-Type': 'application/json'}),
            json={'expiresIn': expires_in}, timeout=15)
        if not s.ok:
            _warn('sign failed {}: {}'.format(s.status_code, s.text[:200]))
            return None
        signed = s.json().get('signedURL') or s.json().get('signedUrl')
        if not signed:
            return None
        # The API returns a path like "/object/sign/<bucket>/<file>?token=…"
        # (without the "/storage/v1" prefix); prepend it to form a fetchable URL.
        if not signed.startswith('/storage/v1'):
            signed = '/storage/v1' + (signed if signed.startswith('/') else '/' + signed)
        return cfg['url'] + signed
    except Exception as e:  # noqa: BLE001
        _warn('signed_url error: {}'.format(e))
        return None
