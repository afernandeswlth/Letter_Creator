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


def cmd_zip(brand, dd_bsb, dd_account, paths):
    """Build every party's PDF and write a ZIP of them all to stdout."""
    import io
    import re
    import sys as _sys
    import zipfile
    from pdf_letter import build_pdf
    docs, _loan_type, smsf_number = group(paths)
    label = 'MMA' if brand == 'mma' else 'WLTH'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for _, d in docs:
            pdf = build_pdf(d, brand, dd_bsb, dd_account,
                            smsf_number=None if d['is_entity'] else smsf_number)
            name = re.sub(r'^(mr|mrs|ms|miss|dr)\.?\s+', '', d['recipient_name'], flags=re.I)
            z.writestr(f'{label} Welcome Letter - {name}.pdf', pdf)
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
    if cmd == 'preview':
        brand, dd_bsb, dd_account, party_index, *paths = rest
        return cmd_preview(brand, dd_bsb, dd_account, party_index, paths)
    if cmd == 'zip':
        brand, dd_bsb, dd_account, *paths = rest
        return cmd_zip(brand, dd_bsb, dd_account, paths)
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
