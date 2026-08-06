"""
Vercel Python serverless entry point for the Letter Generator.

A single Flask WSGI app serving every /api/letters/* route. It reuses the
existing Python engine in ../engine (imported, not shelled out to), so the PDF
output is byte-identical to local/Render. Deployed via vercel.json:
  { "src": "api/index.py", "use": "@vercel/python", "config": { "includeFiles": "engine/**" } }

Locally the app keeps using the Nitro routes in server/ (nuxt dev); this file
is only used in the Vercel build.
"""
import os
import sys
import io
import re
import json
import base64
import zipfile
import tempfile

from flask import Flask, request, Response, jsonify

# Make the engine importable and let its assets resolve via __file__.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'engine'))

import cli          # noqa: E402  group/cmd_parse/cmd_render/_build_party_pdf
import pdf_letter   # noqa: E402  build_pdf
import store        # noqa: E402  letter-history persistence (Supabase)

app = Flask(__name__)

ENGINE_ASSETS = os.path.join(ROOT, 'engine', 'assets')
FORM_NAMES = {
    'wlth': 'WLTH Linked Account Nomination Form.pdf',
    'mma': 'Mortgage Mart Linked Account Nomination Form.pdf',
}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _save_uploads():
    """Write the uploaded funder .docx files to a temp dir; return their paths
    in upload order (matching the Nitro handler's behaviour)."""
    tmpdir = tempfile.mkdtemp(prefix='lg-')
    paths = []
    for i, fs in enumerate(request.files.getlist('files')):
        safe = re.sub(r'[^\w.-]', '_', fs.filename or f'funder_{i}.docx')
        p = os.path.join(tmpdir, f'funder_{i}_{safe}')
        fs.save(p)
        paths.append(p)
    return paths


def _form(name, default=''):
    return request.form.get(name, default)


def _json(payload, status=200):
    return Response(json.dumps(payload, ensure_ascii=False), status=status,
                    mimetype='application/json; charset=utf-8')


# --------------------------------------------------------------------------
# routes
# --------------------------------------------------------------------------
@app.get('/api/health')
def health():
    return _json({'ok': True})


# --------------------------------------------------------------------------
# letter history (Supabase) — read side for the dashboard
# --------------------------------------------------------------------------
@app.get('/api/letters/recent')
def letters_recent():
    try:
        limit = int(request.args.get('limit', '20'))
    except ValueError:
        limit = 20
    return _json({'letters': store.recent_letters(min(max(limit, 1), 100))})


@app.get('/api/letters/file')
def letters_file():
    letter_id = (request.args.get('id') or '').strip()
    if not letter_id:
        return _json({'error': 'Missing id'}, 400)
    url = store.signed_url(letter_id)
    if not url:
        return _json({'error': 'Not found'}, 404)
    return _json({'url': url})


@app.post('/api/letters/parse')
def parse():
    paths = _save_uploads()
    if not paths:
        return _json({'error': 'No .docx files found'}, 400)
    try:
        return _json(cli.cmd_parse(paths))
    except Exception as e:  # noqa: BLE001
        return _json({'error': str(e)}, 500)


@app.post('/api/letters/render')
def render():
    paths = _save_uploads()
    if not paths:
        return _json({'error': 'No .docx files found'}, 400)
    try:
        out = cli.cmd_render(_form('brand', 'wlth'), _form('ddBsb'), _form('ddAccount'), paths)
        return _json(out)
    except Exception as e:  # noqa: BLE001
        return _json({'error': str(e)}, 500)


@app.post('/api/letters/pdf')
def pdf():
    paths = _save_uploads()
    if not paths:
        return _json({'error': 'No .docx files found'}, 400)
    try:
        data = cli._build_party_pdf(
            _form('brand', 'wlth'), _form('ddBsb'), _form('ddAccount'),
            int(_form('partyIndex', '0') or 0), paths)
        name = (_form('name', 'Welcome Letter') or 'Welcome Letter').strip()
        return Response(data, mimetype='application/pdf', headers={
            'Content-Disposition': f'attachment; filename="{name}.pdf"',
        })
    except Exception as e:  # noqa: BLE001
        return _json({'error': str(e)}, 500)


@app.post('/api/letters/preview')
def preview():
    paths = _save_uploads()
    if not paths:
        return _json({'error': 'No .docx files found'}, 400)
    try:
        import fitz
        data = cli._build_party_pdf(
            _form('brand', 'wlth'), _form('ddBsb'), _form('ddAccount'),
            int(_form('partyIndex', '0') or 0), paths)
        doc = fitz.open(stream=data, filetype='pdf')
        pages = []
        for pg in doc:
            png = pg.get_pixmap(dpi=130).tobytes('png')
            pages.append('data:image/png;base64,' + base64.b64encode(png).decode())
        return _json({'pages': pages})
    except Exception as e:  # noqa: BLE001
        return _json({'error': str(e)}, 500)


@app.post('/api/letters/zip')
def zip_letters():
    paths = _save_uploads()
    if not paths:
        return _json({'error': 'No .docx files found'}, 400)
    try:
        brand = _form('brand', 'wlth')
        dd_bsb, dd_account = _form('ddBsb'), _form('ddAccount')
        docs, _loan_type, smsf_number = cli.group(paths)
        label = 'MMA' if brand == 'mma' else 'WLTH'
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
            for _p, d in docs:
                data = pdf_letter.build_pdf(
                    d, brand, dd_bsb, dd_account,
                    smsf_number=None if d['is_entity'] else smsf_number)
                name = re.sub(r'^(mr|mrs|ms|miss|dr)\.?\s+', '', d['recipient_name'], flags=re.I)
                fname = f'{label} Welcome Letter - {name}'
                z.writestr(f'{fname}.pdf', data)
                # Record each party's letter in the history (best-effort).
                store.save_letter({
                    'letter_type': 'welcome', 'type_label': store.LABELS['welcome'],
                    'brand': brand, 'customer': name,
                    'reference': d.get('loan_facility_number') or None,
                }, data, fname, 'Completed')
        return Response(buf.getvalue(), mimetype='application/zip', headers={
            'Content-Disposition': 'attachment; filename="letters.zip"',
        })
    except Exception as e:  # noqa: BLE001
        return _json({'error': str(e)}, 500)


@app.post('/api/letters/email')
def email():
    paths = _save_uploads()
    to = _form('to').strip()
    if not paths:
        return _json({'error': 'No .docx files found'}, 400)
    if not to:
        return _json({'error': 'Missing borrower email address'}, 400)

    brand = _form('brand', 'wlth')
    offset = 'no' if _form('offset') == 'no' else 'yes'
    filename = (_form('filename', 'Welcome Letter') or 'Welcome Letter').strip()

    try:
        pdf_bytes = cli._build_party_pdf(
            brand, _form('ddBsb'), _form('ddAccount'),
            int(_form('partyIndex', '0') or 0), paths)
    except Exception as e:  # noqa: BLE001
        return _json({'error': f'Engine error: {e}'}, 500)

    subject, html = welcome_email(
        brand_id=brand,
        borrower_name=_form('name') or to,
        offset=offset,
        is_trust=_form('isTrust') == 'true',
        trust_name=_form('trustName'),
        account_number=_form('accountNumber'),
    )

    attachments = [(f'{filename}.pdf', pdf_bytes)]
    if offset == 'no':
        form_path = os.path.join(ENGINE_ASSETS, brand, 'nomination-form.pdf')
        try:
            with open(form_path, 'rb') as fh:
                attachments.append((FORM_NAMES.get(brand, 'Linked Account Nomination Form.pdf'), fh.read()))
        except OSError as e:
            return _json({'error': f'Could not read nomination form: {e}'}, 500)

    webhook = os.environ.get('ZAPIER_EMAIL_WEBHOOK_URL')
    if not webhook:
        return _json({'error': 'Email is not configured. Set ZAPIER_EMAIL_WEBHOOK_URL.'}, 500)

    try:
        import requests
        data = {'to': to, 'subject': subject, 'body': html, 'filename': attachments[0][0]}
        files = {}
        for i, (fn, content) in enumerate(attachments):
            key = 'attachment' if i == 0 else f'attachment{i + 1}'
            files[key] = (fn, content, 'application/pdf')
        res = requests.post(webhook, data=data, files=files, timeout=30)
        if not res.ok:
            return _json({'error': f'Zapier webhook returned {res.status_code}. {res.text[:200]}'}, 502)
    except Exception as e:  # noqa: BLE001
        return _json({'error': str(e)}, 502)

    store.save_letter({
        'letter_type': 'welcome', 'type_label': store.LABELS['welcome'],
        'brand': brand, 'customer': store._strip_title(_form('name') or to),
        'reference': _form('accountNumber') or None,
    }, pdf_bytes, filename, 'Draft')
    return _json({'ok': True, 'via': 'zapier',
                  'link': 'https://mail.google.com/mail/u/0/#drafts', 'to': to})


# --------------------------------------------------------------------------
# form-driven letter types (Formal Approval, etc.) — JSON body, no upload
# --------------------------------------------------------------------------
@app.post('/api/forms/parse-source')
def form_parse_source():
    fs = request.files.get('file')
    if fs is None:
        return _json({'error': 'No file uploaded'}, 400)
    letter_type = request.form.get('letterType', '')
    brand = request.form.get('brand', 'wlth')
    tmpdir = tempfile.mkdtemp(prefix='lg-s4-')
    path = os.path.join(tmpdir, re.sub(r'[^\w.-]', '_', fs.filename or 'source'))
    fs.save(path)
    try:
        return _json({'values': cli.parse_form_source(letter_type, brand, path)})
    except Exception as e:  # noqa: BLE001
        return _json({'error': str(e)}, 500)


@app.post('/api/forms/pdf')
def form_pdf():
    data = request.get_json(force=True, silent=True) or {}
    letter_type = data.get('letterType', '')
    brand = data.get('brand', 'wlth')
    values = data.get('values') or {}
    try:
        pdf_bytes = cli.build_form_pdf(letter_type, brand, values)
        name = (data.get('filename') or 'Letter').strip()
        # Blank template downloads (no field values) are not real letters — skip.
        if values:
            store.save_letter(store.form_meta(letter_type, brand, values), pdf_bytes, name, 'Completed')
        return Response(pdf_bytes, mimetype='application/pdf', headers={
            'Content-Disposition': f'attachment; filename="{name}.pdf"',
        })
    except Exception as e:  # noqa: BLE001
        return _json({'error': str(e)}, 500)


@app.post('/api/forms/preview')
def form_preview():
    import fitz
    data = request.get_json(force=True, silent=True) or {}
    try:
        pdf_bytes = cli.build_form_pdf(data.get('letterType', ''), data.get('brand', 'wlth'), data.get('values') or {})
        doc = fitz.open(stream=pdf_bytes, filetype='pdf')
        pages = ['data:image/png;base64,' + base64.b64encode(pg.get_pixmap(dpi=130).tobytes('png')).decode()
                 for pg in doc]
        return _json({'pages': pages})
    except Exception as e:  # noqa: BLE001
        return _json({'error': str(e)}, 500)


@app.post('/api/forms/email')
def form_email():
    data = request.get_json(force=True, silent=True) or {}
    to = (data.get('to') or '').strip()
    if not to:
        return _json({'error': 'Missing recipient email address'}, 400)
    cc = (data.get('cc') or '').strip()
    brand = data.get('brand', 'wlth')
    letter_type = data.get('letterType', '')
    values = data.get('values') or {}
    try:
        pdf_bytes = cli.build_form_pdf(letter_type, brand, values)
    except Exception as e:  # noqa: BLE001
        return _json({'error': f'Engine error: {e}'}, 500)

    filename = (data.get('filename') or 'Letter').strip()
    subject, html = form_email_content(letter_type, brand, values)

    # A letter type with a dedicated sender drafts from a separate inbox, so it
    # uses its OWN Zap — never the shared (welcome) webhook.
    form_senders = {'commencement': 'construction@wlth.com'}
    sender = form_senders.get(letter_type)
    if sender:
        webhook = os.environ.get('ZAPIER_CONSTRUCTION_WEBHOOK_URL')
        missing = 'ZAPIER_CONSTRUCTION_WEBHOOK_URL'
    else:
        webhook = os.environ.get('ZAPIER_EMAIL_WEBHOOK_URL')
        missing = 'ZAPIER_EMAIL_WEBHOOK_URL'
    if not webhook:
        return _json({'error': f'Email is not configured. Set {missing}.'}, 500)

    # The letter, plus (for commencement) the brand's Progress Payment Guidelines.
    files = [('attachment', (f'{filename}.pdf', pdf_bytes, 'application/pdf'))]
    if letter_type == 'commencement':
        bkey = 'mma' if brand == 'mma' else 'wlth'
        gpath = os.path.join(ENGINE_ASSETS, bkey, 'progress-payment-guidelines.pdf')
        if os.path.exists(gpath):
            glabel = 'Mortgage Mart' if brand == 'mma' else 'WLTH'
            with open(gpath, 'rb') as fh:
                files.append(('attachment2', (f'{glabel} Progress Payment Guidelines.pdf',
                                              fh.read(), 'application/pdf')))

    try:
        import requests
        d = {'to': to, 'subject': subject, 'body': html, 'filename': f'{filename}.pdf'}
        if cc:
            d['cc'] = cc
        if sender:
            d['from'] = sender
        res = requests.post(webhook, data=d, files=files, timeout=30)
        if not res.ok:
            return _json({'error': f'Zapier webhook returned {res.status_code}. {res.text[:200]}'}, 502)
    except Exception as e:  # noqa: BLE001
        return _json({'error': str(e)}, 502)
    store.save_letter(store.form_meta(letter_type, brand, values), pdf_bytes, filename, 'Draft')
    return _json({'ok': True, 'via': 'zapier',
                  'link': 'https://mail.google.com/mail/u/0/#drafts',
                  'to': to, 'cc': cc or None, 'from': sender})


_FORM_LABELS = {'approval': 'Formal Approval', 'commencement': 'Commencement'}


def form_email_content(letter_type, brand, values):
    b = _BRAND_EMAIL.get(brand, _BRAND_EMAIL['wlth'])
    label = _FORM_LABELS.get(letter_type, 'Letter')
    # For a commencement letter the subject "borrower" is the customer(s), not
    # the builder (the builder is only greeted in the body).
    if letter_type == 'commencement':
        who = values.get('customerNames') or ''
    else:
        who = values.get('borrowers') or values.get('recipientName') or ''
    first = (_strip_title(who).split() or ['there'])[0]
    acct = values.get('loanAccountNumber') or values.get('applicationNumber') or ''
    subject = f"{b['label']} {label} Letter"
    if who:
        subject += f": {_strip_title(who)}"
    if acct:
        subject += f" - {acct}"

    if letter_type == 'commencement':
        builder = (values.get('builderName') or '').strip() or 'there'
        body = f"""
    <p>Hi {builder},</p>
    <p>Welcome to the {b['label']} Construction Journey!</p>
    <p>We want to let you know that we can start releasing progress payments for our mutual customers.
       You can find the Commencement Letter for the above clients attached to this email for your
       attention and action. This means you can now commence the construction or renovations.</p>
    <p>Also attached are our Progress Payment Guidelines, which outline the requirements for a drawdown
       request. All invoices must be signed by all borrowers; digital signatures are accepted. Kindly
       send all construction drawdown requests and supporting documents to
       <a href="mailto:construction@wlth.com">construction@wlth.com</a></p>
    <p>Please note, we require a progress valuation at every stage of the construction. These reports
       can take up to 5 business days to be compiled by the valuation firm. We encourage you to take
       this into consideration when submitting a request.</p>
    <p>Once we have all the supporting documents, payment is usually posted within 2-3 business days.</p>
    <p>If you have any questions or concerns along the way, please do not hesitate to reach out.</p>
    <p>Kind regards,<br/>{b['label']}</p>"""
    else:
        body = f"""
    <p>Hi {first},</p>
    <p>Please find attached your {b['label']} {label} letter.</p>
    <p>If you have any questions, please reach out to us {b['contact_short']}</p>
    <p>Warm regards,<br/>{b['team']}</p>"""
    signature = f'<br/><br/>{SIGNATURE_HTML}' if SIGNATURE_HTML else ''
    html = f"""<div style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #1e2430; line-height: 1.5;">{body}{signature}</div>""".strip()
    return subject, html


# --------------------------------------------------------------------------
# email template (Python port of server/utils/emailTemplate.ts + signature.ts)
# --------------------------------------------------------------------------
_BRAND_EMAIL = {
    'wlth': {
        'label': 'WLTH',
        'letter_name': 'WLTH Welcome Letter',
        'loan_details': 'new Home Loan details',
        'contact_short': 'on 13WLTH thats 13 95 84, email hello@wlth.com or contact your Mortgage Broker/ Lending Specialist.',
        'contact_long': 'on 13WLTH, email hello@wlth.com or contact your Mortgage Broker/ Lending Specialist.',
        'team': 'The WLTH Team',
    },
    'mma': {
        'label': 'Mortgage Mart',
        'letter_name': 'Mortgage Mart Welcome Letter',
        'loan_details': 'new Loan details',
        'contact_short': 'on 1300 650 200, email hello@wlth.com, or contact your Mortgage Broker.',
        'contact_long': 'on 1300 650 200, email hello@wlth.com, or contact your Mortgage Broker.',
        'team': 'The Mortgage Mart Team',
    },
}


def _strip_title(name):
    return re.sub(r'^(mr|mrs|ms|miss|dr)\.?\s+', '', name or '', flags=re.I)


def welcome_email(brand_id, borrower_name, offset, is_trust, trust_name, account_number):
    brand = _BRAND_EMAIL.get(brand_id, _BRAND_EMAIL['wlth'])
    stripped = _strip_title(borrower_name)
    first = (stripped.split() or [''])[0]
    subject_name = trust_name if is_trust else stripped
    subject = f"{brand['label']} Welcome Letter: {subject_name} - {account_number}"

    intro = f"""
    <p>Hi {first},</p>
    <p>Congratulations again on your settlement!</p>
    <p>Please find attached your {brand['letter_name']}. This includes your repayment information &amp;
       confirmation of your {brand['loan_details']} including loan account number, loan repayment date and
       direct debit and credit information.</p>"""

    linking_block = """
    <p>We note that you have not yet linked your SMSF Cash Management Account to your Offset Account.</p>
    <p>Linking an account enables the Redraw function, allowing you to transfer funds from your offset
       account directly to your linked external account. This is the only way to withdraw funds from your
       SMSF Offset Account other than BPAY, and it's possible to transfer up to $250,000 at a time!</p>
    <p>To link an external account with your offset account, simply complete and return the attached
       Linked Account Nomination Form.</p>
    <p>To increase your Redraw limits past the default, please contact us on 13 95 84. 2 Factor
       Authentication must be enabled to increase your daily limit.</p>
    <p><strong>Redraw Daily Limits:</strong></p>
    <p style="margin:0">Default: $10,000.00<br/>Default with 2FA Enabled: $50,000.00<br/>Maximum: $250,000.00</p>
    <p><strong>Important points when linking your account:</strong></p>
    <ul>
      <li>If you're linking an offset account, please enter your offset account number in the
          'Loan Account No(s)' section of the form.</li>
      <li>All borrowers/guarantors will need to sign the forms. If signing digitally, please include the
          electronic certificate of completion/audit trail.</li>
      <li>Return the completed form/s by replying to this email, along with a bank account statement
          (or bank letter) for your nominated account. This statement must clearly show the SMSF name,
          bank account details, and the bank's logo. It should be no older than six months.</li>
    </ul>"""

    contact = brand['contact_long'] if offset == 'no' else brand['contact_short']
    body = f"""
    {intro}
    {linking_block if offset == 'no' else ''}
    <p>If you have any questions, please reach out to us {contact}</p>
    <p>Warm regards,<br/>{brand['team']}</p>"""

    signature = f'<br/><br/>{SIGNATURE_HTML}' if SIGNATURE_HTML else ''
    html = f"""
    <div style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #1e2430; line-height: 1.5;">
      {body}
      {signature}
    </div>""".strip()
    return subject, html


# The real hello@wlth.com signature (verbatim from server/utils/signature.ts).
SIGNATURE_HTML = '''<div dir="ltr"><table border="0" cellpadding="0" cellspacing="0" style="border-collapse:collapse;color:rgb(0,0,0);font-family:Times;font-size:medium;width:600px;text-align:center"><tbody><tr><td style="border-collapse:collapse;direction:ltr;font-size:0px;padding:0px;text-align:center"><div style="width:600px;max-width:100%;line-height:0;text-align:left;display:inline-block;direction:ltr"><div style="width:300px;max-width:50%;direction:ltr;display:inline-block;vertical-align:top"><table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse"><tbody><tr><td style="border-collapse:collapse;vertical-align:top;padding:0px"><table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse"><tbody><tr><td style="border-collapse:collapse;word-break:break-word"><div style="height:52px;line-height:52px"> </div></td></tr><tr><td style="border-collapse:collapse;padding:0px 32px;word-break:break-word;text-align:left"><table border="0" cellpadding="0" cellspacing="0" style="border-collapse:collapse;border-spacing:0px"><tbody><tr><td style="border-collapse:collapse;width:95px"><img alt="" src="http://assets.wlth.com/cms/wp-content/uploads/2025/03/Logo.png" width="95" height="22" style="border:0px;height:22px;line-height:13px;outline:currentcolor;display:block;width:95px;font-size:13px"></td></tr></tbody></table></td></tr><tr><td style="border-collapse:collapse;word-break:break-word"><div style="height:18px;line-height:18px"> </div></td></tr><tr><td style="border-collapse:collapse;padding:0px 32px;word-break:break-word;text-align:left"><table border="0" cellpadding="0" cellspacing="0" style="border-collapse:collapse;border-spacing:0px"><tbody><tr><td style="border-collapse:collapse;width:178px"><img alt="" src="http://assets.wlth.com/cms/wp-content/uploads/2025/03/MMA_Horizontal_Full_Text.png" width="178" height="21" style="border:0px;height:21.67px;line-height:13px;outline:currentcolor;display:block;width:178px;font-size:13px"></td></tr></tbody></table></td></tr><tr><td style="border-collapse:collapse;word-break:break-word"><div style="height:26.5px;line-height:26.5px"> </div></td></tr><tr><td style="border-collapse:collapse;padding:0px 16px 0px 32px;word-break:break-word;text-align:center"><p style="margin:0px auto;border-top-width:1px;border-top-style:solid;border-top-color:rgb(222,226,229);font-size:1px;width:252px"></p></td></tr><tr><td style="border-collapse:collapse;padding:0px 16px 0px 32px;word-break:break-word;text-align:left"><div style="font-family:SuisseIntl-Medium,Helvetica,Arial,sans-serif;font-size:12px;letter-spacing:0.6px;line-height:21.526px"><p style="margin:13px 0px">THE <span style="color:rgb(17,69,199)">NATURAL</span> EVOLUTION OF MONEY</p></div></td></tr><tr><td style="border-collapse:collapse;padding:0px 16px 0px 32px;word-break:break-word;text-align:center"><p style="margin:0px auto;border-top-width:1px;border-top-style:solid;border-top-color:rgb(222,226,229);font-size:1px;width:252px"></p></td></tr><tr><td style="border-collapse:collapse;word-break:break-word"><div style="height:34.5px;line-height:34.5px"> </div></td></tr><tr><td style="border-collapse:collapse;padding:10px 25px;word-break:break-word;text-align:left"><table cellpadding="0" cellspacing="0" width="160" border="0" style="border-collapse:collapse;font-family:Ubuntu,Helvetica,Arial,sans-serif;font-size:13px;line-height:22px;table-layout:auto;width:160px;border:medium"><tbody><tr style="width:160px;height:32px"><td style="border-collapse:collapse;width:40px"><img src="http://assets.wlth.com/cms/wp-content/uploads/2025/03/Social-Media-Icon.png" width="32px" height="32px" style="border:0px;height:auto;line-height:13px;outline:currentcolor"></td><td style="border-collapse:collapse;width:40px"><img src="http://assets.wlth.com/cms/wp-content/uploads/2025/03/Social-Media-Icon-1.png" width="32px" height="32px" style="border:0px;height:auto;line-height:13px;outline:currentcolor"></td><td style="border-collapse:collapse;width:40px"><img src="http://assets.wlth.com/cms/wp-content/uploads/2025/03/Social-Media-Icon-2.png" width="32px" height="32px" style="border:0px;height:auto;line-height:13px;outline:currentcolor"></td><td style="border-collapse:collapse;width:40px"><img src="http://assets.wlth.com/cms/wp-content/uploads/2025/03/Social-Media-Icon-3.png" width="32px" height="32px" style="border:0px;height:auto;line-height:13px;outline:currentcolor"></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></div> <div style="width:300px;max-width:50%;direction:ltr;display:inline-block;vertical-align:top"><table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse"><tbody><tr><td style="border-collapse:collapse;background-color:rgb(76,90,104);vertical-align:top;padding-top:44px;padding-bottom:0px"><table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse"><tbody><tr><td style="border-collapse:collapse;padding:0px 36px 0px 44px;word-break:break-word;text-align:left"><table border="0" cellpadding="0" cellspacing="0" style="line-height:0px"><tbody><tr><td bgcolor="#4C5A68" valign="middle" style="border-collapse:collapse;border:medium;border-radius:3px;background-image:none;background-position:0% 0%;background-repeat:repeat;text-align:center"><a href="tel:139584" style="display:inline-block;background-image:none;background-position:0% 0%;background-repeat:repeat;color:rgb(255,255,255);font-family:SuisseIntl,Helvetica,Arial,sans-serif;font-size:14px;line-height:20px;letter-spacing:0.5px;margin:0px;text-decoration:none;padding:0px;border-radius:3px" target="_blank">13 WLTH</a></td></tr></tbody></table></td></tr><tr><td style="border-collapse:collapse;padding:0px 36px 0px 44px;word-break:break-word;text-align:left"><table border="0" cellpadding="0" cellspacing="0" style="line-height:0px"><tbody><tr><td bgcolor="#4C5A68" valign="middle" style="border-collapse:collapse;border:medium;border-radius:3px;background-image:none;background-position:0% 0%;background-repeat:repeat;text-align:center"><a href="mailto:hello@wlth.com" style="display:inline-block;background-image:none;background-position:0% 0%;background-repeat:repeat;color:rgb(255,255,255);font-family:SuisseIntl,Helvetica,Arial,sans-serif;font-size:14px;line-height:20px;letter-spacing:0.5px;margin:0px;text-decoration:none;padding:0px;border-radius:3px" target="_blank">hello@wlth.com</a></td></tr></tbody></table></td></tr><tr><td style="border-collapse:collapse;padding:0px 36px 0px 44px;word-break:break-word;text-align:left"><table border="0" cellpadding="0" cellspacing="0" style="line-height:0px"><tbody><tr><td bgcolor="#4C5A68" valign="middle" style="border-collapse:collapse;border:medium;border-radius:3px;background-image:none;background-position:0% 0%;background-repeat:repeat;text-align:center"><a href="http://wlth.com" style="display:inline-block;background-image:none;background-position:0% 0%;background-repeat:repeat;color:rgb(255,255,255);font-family:SuisseIntl,Helvetica,Arial,sans-serif;font-size:14px;line-height:20px;letter-spacing:0.5px;margin:0px;text-decoration:none;padding:0px;border-radius:3px" target="_blank">wlth.com</a></td></tr></tbody></table></td></tr><tr><td style="border-collapse:collapse;padding:0px 36px 0px 44px;word-break:break-word;text-align:left"><table border="0" cellpadding="0" cellspacing="0" style="line-height:0px"><tbody><tr><td bgcolor="#4C5A68" valign="middle" style="border-collapse:collapse;border:medium;border-radius:3px;background-image:none;background-position:0% 0%;background-repeat:repeat;text-align:center"><a href="http://mortgage-mart.com.au" style="display:inline-block;background-image:none;background-position:0% 0%;background-repeat:repeat;color:rgb(255,255,255);font-family:SuisseIntl,Helvetica,Arial,sans-serif;font-size:14px;line-height:20px;letter-spacing:0.5px;margin:0px;text-decoration:none;padding:0px;border-radius:3px" target="_blank">mortgage-mart.com.au</a></td></tr></tbody></table></td></tr><tr><td style="border-collapse:collapse;word-break:break-word"><div style="height:18px;line-height:18px"> </div></td></tr><tr><td style="border-collapse:collapse;padding:0px 16px 0px 44px;word-break:break-word;text-align:center"><p style="margin:0px auto;border-top-width:1px;border-top-style:solid;border-top-color:rgb(222,226,229);font-size:1px;width:240px"></p></td></tr><tr><td style="border-collapse:collapse;word-break:break-word"><div style="height:18px;line-height:18px"> </div></td></tr><tr><td style="border-collapse:collapse;padding:0px 36px 0px 44px;word-break:break-word;text-align:left"><div style="font-family:SuisseIntl,Helvetica,Arial,sans-serif;font-size:14px;letter-spacing:0.5px;line-height:20px;color:rgb(255,255,255)">Brisbane HQ</div></td></tr><tr><td style="border-collapse:collapse;padding:0px 36px 0px 44px;word-break:break-word;text-align:left"><div style="font-family:SuisseIntl,Helvetica,Arial,sans-serif;font-size:14px;letter-spacing:0.5px;line-height:20px;color:rgb(255,255,255)">Level 2, 15 James Street</div></td></tr><tr><td style="border-collapse:collapse;padding:0px 36px 0px 44px;word-break:break-word;text-align:left"><div style="font-family:SuisseIntl,Helvetica,Arial,sans-serif;font-size:14px;letter-spacing:0.5px;line-height:20px;color:rgb(255,255,255)">Fortitude Valley, QLD 4006</div></td></tr><tr><td style="border-collapse:collapse;word-break:break-word"><div style="height:18px;line-height:18px"> </div></td></tr><tr><td style="border-collapse:collapse;padding:10px 25px 10px 44px;word-break:break-word;text-align:left"><table cellpadding="0" cellspacing="0" width="160" border="0" style="border-collapse:collapse;font-family:Ubuntu,Helvetica,Arial,sans-serif;font-size:13px;line-height:22px;table-layout:auto;width:160px;border:medium"><tbody><tr style="width:160px;height:32px"><td style="border-collapse:collapse;width:44px"><a href="https://www.facebook.com/wlthmoney/" style="text-decoration:none;width:32px;height:32px" target="_blank"><img src="http://assets.wlth.com/cms/wp-content/uploads/2025/03/Facebook.png" width="32px" height="32px" style="border:0px;height:auto;line-height:13px;outline:currentcolor"></a></td><td style="border-collapse:collapse;width:44px"><a href="https://www.instagram.com/wlthmoney/" style="text-decoration:none;width:32px;height:32px" target="_blank"><img src="http://assets.wlth.com/cms/wp-content/uploads/2025/03/Instagram-1.png" width="32px" height="32px" style="border:0px;height:auto;line-height:13px;outline:currentcolor"></a></td><td style="border-collapse:collapse;width:44px"><a href="https://au.linkedin.com/company/wlthmoney" style="text-decoration:none;width:32px;height:32px" target="_blank"><img src="http://assets.wlth.com/cms/wp-content/uploads/2025/03/Linkdin.png" width="32px" height="32px" style="border:0px;height:auto;line-height:13px;outline:currentcolor"></a></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></div></div></td></tr></tbody></table><img src="https://email.wlth.com.au/hubfs/WLTH%20-%20Email%20Signature/wlth_email_sig.gif" width="600px" style="border:0px;height:auto;line-height:16px;outline:currentcolor;color:rgb(0,0,0);font-family:Times;font-size:medium"><br></div>'''
