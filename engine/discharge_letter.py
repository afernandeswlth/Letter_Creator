"""
Render a Discharge Confirmation letter as a branded PDF, matching the WLTH /
Mortgage Mart "Discharge Confirmation" template. It reuses the Custom-letter
letterhead (header band + corner mark, 4-column footer) with a structured
discharge body and a centred, per-brand legal block.

Form-driven: field ids match app/utils/letterTypes.ts. The body copy is fixed;
the caller supplies the recipient, loan/account details, dates and security.
"""
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer

import pdf_letter as PL
from custom_letter import (
    _page, _address_lines, BRANDS, PAGE_W, PAGE_H, LM, RM, CONTENT_W, FONT, BOLD, INK, HEAD_H,
)

MANAGER = {'wlth': 'WLTH', 'mma': 'Mortgage Mart'}
PHONE = {'wlth': '13 95 84', 'mma': '1300 650 200'}
LEGAL = {
    'wlth': [
        'WLTH PTY LTD',
        'ABN 98 639 591 245 Australian Credit Licence Number 382606',
        'Address: Level 2, 15 James Street, Fortitude Valley, QLD 4006',
        'Email: hello@wlth.com',
    ],
    'mma': [
        'MORTGAGE MART',
        'ACN 100 038 391 Australian Credit Licence Number 382606',
        'Address: 3B/105 UPTON STREET BUNDALL QLD 4217 Telephone: 1300650200',
        'Email: mmacustomersupport@mortgage-mart.com.au',
    ],
}
PROGRAM_MANAGER = ('Program Manager: Columbus Capital Pty Limited trading as Origin Mortgage '
                   'Management Services ACN 119 531 252, Australian Credit Licence Number 337303')


def build_discharge_pdf(brand_id, v):
    brand = BRANDS.get(brand_id, BRANDS['wlth'])
    esc = PL.esc

    def g(key, default=''):
        val = v.get(key)
        val = val.strip() if isinstance(val, str) else val
        return val if val else default

    body = ParagraphStyle('b', fontName=FONT, fontSize=10.5, leading=14, textColor=INK)
    boldp = ParagraphStyle('bd', parent=body, fontName=BOLD)
    legal = ParagraphStyle('lg', parent=body, fontSize=9, leading=12,
                           alignment=TA_CENTER, textColor=colors.HexColor('#6b7480'))

    frame = Frame(LM, 72, CONTENT_W, PAGE_H - HEAD_H - 22 - 72,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=(PAGE_W, PAGE_H))
    doc.addPageTemplates([PageTemplate(id='dc', frames=[frame],
                                       onPage=lambda c, d: _page(c, d, brand))])

    flow = []
    # Recipient block
    if g('recipientName'):
        flow.append(Paragraph(esc(g('recipientName')), body))
    for ln in _address_lines(g('recipientAddress')):
        flow.append(Paragraph(esc(ln), body))

    flow.append(Spacer(1, 16))
    flow.append(Paragraph(esc(g('date')), boldp))
    flow.append(Spacer(1, 22))
    flow.append(Paragraph(f'Dear {esc(g("recipientName"))}' if g('recipientName') else 'Dear', body))

    # Re: block
    flow.append(Spacer(1, 14))
    flow.append(Paragraph('<b>Re: Discharge Confirmation</b>', body))
    flow.append(Paragraph(f'<b>Mortgage Manager:</b> {esc(MANAGER.get(brand_id, "WLTH"))}', body))
    flow.append(Paragraph(
        '<b>Program Manager</b>: Columbus Capital Pty Limited ACN 119 531 252 trading as Origin '
        'Mortgage Management Services, Australian Credit Licence 337303', body))

    # Confirmation
    product = g('productName')
    prod = f'{esc(product)} Loan' if product else 'Loan'
    flow.append(Spacer(1, 16))
    flow.append(Paragraph(
        f'This letter serves as a confirmation that the {prod} with Account Number: '
        f'{esc(g("accountNumbers"))} have been fully settled and discharged. The release of the '
        f'mortgage for the security listed below has been granted on {esc(g("dischargeDate"))}.', body))

    flow.append(Spacer(1, 12))
    flow.append(Paragraph(f'<b>Security Address</b>: {esc(g("securityAddress"))}', body))

    flow.append(Spacer(1, 12))
    flow.append(Paragraph(
        f'All home finance, offset and/or debit card accounts related to Loan '
        f'{esc(g("accountNumbers"))} have been closed on the same day.', body))

    flow.append(Spacer(1, 12))
    flow.append(Paragraph(
        f'If you have any questions, you may contact us on {esc(g("phone", PHONE.get(brand_id, "13 95 84")))} '
        'during business hours.', body))

    flow.append(Spacer(1, 26))
    flow.append(Paragraph('Yours sincerely', body))
    flow.append(Paragraph('<b>The Discharge Team</b>', body))

    # Centred legal block
    flow.append(Spacer(1, 30))
    for ln in LEGAL.get(brand_id, LEGAL['wlth']):
        flow.append(Paragraph(esc(ln), legal))
    flow.append(Spacer(1, 10))
    flow.append(Paragraph(esc(PROGRAM_MANAGER), legal))

    doc.build(flow)
    return buf.getvalue()


if __name__ == '__main__':
    import sys, json
    sys.stdout.buffer.write(build_discharge_pdf(sys.argv[1], json.loads(sys.argv[2])))
