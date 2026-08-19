#!/usr/bin/env python3
"""
Welcome-letter engine CLI — called by the Nuxt server (Nitro).

Commands
--------
  parse   <funder.docx> [<funder.docx> ...]
      Group the funder docs into one loan, detect the loan type
      (Standard / SMSF-Trust), and return the parties as JSON:
        { "loanType", "smsfNumber", "parties": [ { name, role, customerNumber, isEntity } ] }

  render  <brand> <dd_bsb> <dd_account> <funder.docx> [<funder.docx> ...]
      Same grouping, then render each party's full letter text:
        { "loanType", "parties": [ { name, role, customerNumber, isEntity, text } ] }

The funder sends one .docx per party. For an SMSF/Trust the entity's own
customer number is used as every individual's "Customer SMSF Number".
BSB + account are the only values a human supplies; they apply to every party.
"""
import sys
import json

import wlth_letter as WL

TRUST_MARKERS = ('pty ltd', ' atf ', 'superannuation fund', 'super fund', 'trust')


def _role(d):
    return 'Entity' if d['is_entity'] else 'Member'


def group(paths):
    """Parse every funder doc and work out the loan structure."""
    docs = [(p, WL.parse_funder(p)) for p in paths]
    entity = next((d for _, d in docs if d['is_entity']), None)
    smsf_number = entity['customer_number'] if entity else None
    is_smsf = entity is not None or any(
        m in (d.get('borrowers_names', '') or '').lower() for m in TRUST_MARKERS
        for _, d in docs
    )
    loan_type = 'SMSF / Trust' if is_smsf else 'Standard'
    return docs, loan_type, smsf_number


def cmd_parse(paths):
    docs, loan_type, smsf_number = group(paths)
    parties = [{
        'name': d['recipient_name'],
        'role': _role(d),
        'customerNumber': d.get('customer_number'),
        'isEntity': d['is_entity'],
        'loanFacilityNumber': d.get('loan_facility_number'),
    } for _, d in docs]
    return {'loanType': loan_type, 'smsfNumber': smsf_number, 'parties': parties}


def cmd_render(brand, dd_bsb, dd_account, paths):
    docs, loan_type, smsf_number = group(paths)
    parties = []
    for _, d in docs:
        text = WL.render_text(
            d, brand, dd_bsb, dd_account,
            smsf_number=None if d['is_entity'] else smsf_number,
        )
        parties.append({
            'name': d['recipient_name'],
            'role': _role(d),
            'customerNumber': d.get('customer_number'),
            'isEntity': d['is_entity'],
            'text': text,
        })
    return {'loanType': loan_type, 'parties': parties}


# --- form-driven letter types (no funder upload) ---------------------------
def build_form_pdf(letter_type, brand, values):
    """Render a form-driven letter type (e.g. Formal Approval) to PDF bytes."""
    import approval_letter
    import custom_letter
    import commencement_letter
    import preapproval_letter
    import conditional_letter
    import discharge_letter
    import cam_letter
    renderers = {
        'approval': approval_letter.build_approval_pdf,
        'credit-approval-memorandum': cam_letter.build_cam_pdf,
        'custom': custom_letter.build_custom_pdf,
        'commencement': commencement_letter.build_commencement_pdf,
        'pre-approval': preapproval_letter.build_preapproval_pdf,
        'conditional-approval': conditional_letter.build_conditional_pdf,
        'discharge': discharge_letter.build_discharge_pdf,
    }
    fn = renderers.get(letter_type)
    if fn is None:
        raise ValueError(f'no renderer for letter type "{letter_type}"')
    return fn(brand, values)


def build_form_docx(letter_type, brand, values):
    """Render a form-driven letter type to an editable Word (.docx) — the branded
    template filled with the same values as the PDF."""
    import docx_letter
    return docx_letter.build_form_docx(letter_type, brand, values)


def parse_form_source(letter_type, brand, path):
    """Extract field values from an uploaded source doc (e.g. a Schedule 4)."""
    if letter_type == 'approval':
        import approval_schedule4
        return approval_schedule4.parse_schedule4(path, brand)
    return {}


def cmd_form_parse(letter_type, brand, path):
    print(json.dumps({'values': parse_form_source(letter_type, brand, path)}, ensure_ascii=False))
    return 0


def cmd_form_pdf(letter_type, brand, values_json):
    import sys as _sys
    _sys.stdout.buffer.write(build_form_pdf(letter_type, brand, json.loads(values_json)))
    return 0


def cmd_form_docx(letter_type, brand, values_json):
    import sys as _sys
    _sys.stdout.buffer.write(build_form_docx(letter_type, brand, json.loads(values_json)))
    return 0


def cmd_form_preview(letter_type, brand, values_json):
    import base64
    import fitz
    pdf = build_form_pdf(letter_type, brand, json.loads(values_json))
    doc = fitz.open(stream=pdf, filetype='pdf')
    pages = ['data:image/png;base64,' + base64.b64encode(pg.get_pixmap(dpi=130).tobytes('png')).decode()
             for pg in doc]
    print(json.dumps({'pages': pages}))
    return 0


def _build_party_pdf(brand, dd_bsb, dd_account, party_index, paths):
    from pdf_letter import build_pdf
    docs, _loan_type, smsf_number = group(paths)
    _, d = docs[int(party_index)]
    return build_pdf(d, brand, dd_bsb, dd_account,
                     smsf_number=None if d['is_entity'] else smsf_number)


def cmd_pdf(brand, dd_bsb, dd_account, party_index, paths):
    """Write one party's branded PDF as raw bytes to stdout."""
    import sys as _sys
    pdf = _build_party_pdf(brand, dd_bsb, dd_account, party_index, paths)
    _sys.stdout.buffer.write(pdf)
    return 0


def _build_party_docx(brand, dd_bsb, dd_account, party_index, paths):
    import docx_letter
    docs, _loan_type, smsf_number = group(paths)
    _, d = docs[int(party_index)]
    return docx_letter.build_welcome_docx(
        d, brand, dd_bsb, dd_account, smsf_number=None if d['is_entity'] else smsf_number)


def cmd_docx(brand, dd_bsb, dd_account, party_index, paths):
    """Write one party's Welcome letter as an editable Word doc to stdout."""
    import sys as _sys
    _sys.stdout.buffer.write(_build_party_docx(brand, dd_bsb, dd_account, party_index, paths))
    return 0


def cmd_zip(brand, dd_bsb, dd_account, paths, fmt='both'):
    """Build every party's letter and write a ZIP to stdout. fmt = pdf|docx|both."""
    import io
    import re
    import sys as _sys
    import zipfile
    from pdf_letter import build_pdf
    import docx_letter
    docs, _loan_type, smsf_number = group(paths)
    label = 'MMA' if brand == 'mma' else 'WLTH'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for _, d in docs:
            smsf = None if d['is_entity'] else smsf_number
            name = re.sub(r'^(mr|mrs|ms|miss|dr)\.?\s+', '', d['recipient_name'], flags=re.I)
            base = f'{label} Welcome Letter - {name}'
            if fmt in ('pdf', 'both'):
                z.writestr(f'{base}.pdf', build_pdf(d, brand, dd_bsb, dd_account, smsf_number=smsf))
            if fmt in ('docx', 'both'):
                z.writestr(f'{base}.docx', docx_letter.build_welcome_docx(d, brand, dd_bsb, dd_account, smsf_number=smsf))
    _sys.stdout.buffer.write(buf.getvalue())
    return 0


def cmd_preview(brand, dd_bsb, dd_account, party_index, paths):
    """Rasterise one party's PDF to page images (data URLs) for on-screen preview."""
    import base64
    import fitz
    pdf = _build_party_pdf(brand, dd_bsb, dd_account, party_index, paths)
    doc = fitz.open(stream=pdf, filetype='pdf')
    pages = []
    for pg in doc:
        png = pg.get_pixmap(dpi=130).tobytes('png')
        pages.append('data:image/png;base64,' + base64.b64encode(png).decode())
    print(json.dumps({'pages': pages}))
    return 0


def main(argv):
    if not argv:
        print(json.dumps({'error': 'no command'}))
        return 1
    cmd, rest = argv[0], argv[1:]
    if cmd == 'pdf':
        brand, dd_bsb, dd_account, party_index, *paths = rest
        return cmd_pdf(brand, dd_bsb, dd_account, party_index, paths)
    if cmd == 'docx':
        brand, dd_bsb, dd_account, party_index, *paths = rest
        return cmd_docx(brand, dd_bsb, dd_account, party_index, paths)
    if cmd == 'preview':
        brand, dd_bsb, dd_account, party_index, *paths = rest
        return cmd_preview(brand, dd_bsb, dd_account, party_index, paths)
    if cmd == 'zip':
        brand, dd_bsb, dd_account, fmt, *paths = rest
        return cmd_zip(brand, dd_bsb, dd_account, paths, fmt)
    if cmd == 'form-pdf':
        letter_type, brand, values_json = rest
        return cmd_form_pdf(letter_type, brand, values_json)
    if cmd == 'form-docx':
        letter_type, brand, values_json = rest
        return cmd_form_docx(letter_type, brand, values_json)
    if cmd == 'form-preview':
        letter_type, brand, values_json = rest
        return cmd_form_preview(letter_type, brand, values_json)
    if cmd == 'form-parse':
        letter_type, brand, path = rest
        return cmd_form_parse(letter_type, brand, path)
    if cmd == 'parse':
        out = cmd_parse(rest)
    elif cmd == 'render':
        brand, dd_bsb, dd_account, *paths = rest
        out = cmd_render(brand, dd_bsb, dd_account, paths)
    else:
        print(json.dumps({'error': f'unknown command {cmd}'}))
        return 1
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
