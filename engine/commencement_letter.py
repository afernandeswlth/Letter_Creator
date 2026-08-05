"""
Render a Commencement letter as a branded PDF, matching the WLTH / Mortgage Mart
"Commencement Letter" template: A4 page, brand mark top-right, the builder's
name/address block, date, "Dear {builder}", a fixed progress-payments body with
a brand-coloured "What you need to know" table, and the WLTH ACL footer.

Form-driven: the caller supplies the builder details and the four table values;
the body copy is fixed. Field ids match app/utils/letterTypes.ts.

Font note: the template is set in Arial; we use Helvetica (metric-compatible).
"""
import io
import os

from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
)

import pdf_letter as PL
from custom_letter import _address_lines

HERE = os.path.dirname(__file__)
PAGE_W, PAGE_H = 596, 842  # A4
LM = RM = 28
CONTENT_W = PAGE_W - LM - RM  # 540

FONT, BOLD = 'Helvetica', 'Helvetica-Bold'
INK = colors.black
LINK = colors.HexColor('#2157be')
VALUE_BG = colors.HexColor('#f4f4f4')

BRANDS = {
    'wlth': {
        'header': os.path.join(HERE, 'assets', 'wlth', 'commencement-header.png'),
        'logo_rect': (518.8, 25.0, 575.0, 67.8),  # (x0, y0, x1, y1) top-down
        'label_bg': colors.HexColor('#2157be'),
        'team': 'The WLTH Team',
    },
    'mma': {
        'header': os.path.join(HERE, 'assets', 'mma', 'commencement-header.png'),
        'logo_rect': (447.5, 25.0, 574.2, 82.0),
        'label_bg': colors.HexColor('#1f232d'),
        'team': 'The Mortgage Mart Team',
    },
}

FOOTER = ('WLTH-V1.2  |  Commencement Letter  |  Australian Credit Licence 525752  |  '
          '13WLTH  |  hello@wlth.com')

LIST_ITEMS = [
    'Firstly, prepare an invoice outlining the stage of work completed and request the '
    'respective payment amount as outlined in the Progress Payment Schedule.',
    'Ask your client to review and sign the invoice (this includes the client/s writing '
    'their name, date, and the words “I authorise payment of this invoice” on the '
    'invoice), which confirms they have provided authorisation that the construction stage '
    'has been successfully completed and the progress payment is ready to be made.',
    'Finally, email all signed invoices to '
    '<font color="#2157be"><u>construction@wlth.com</u></font> so we can initiate the '
    'payment process.',
]


def _page(canvas, doc, brand):
    canvas.saveState()
    # brand mark, top-right
    hdr = brand['header']
    if os.path.exists(hdr):
        x0, y0, x1, y1 = brand['logo_rect']
        canvas.drawImage(hdr, x0, PAGE_H - y1, width=x1 - x0, height=y1 - y0, mask='auto')
    # footer: rule + ACL disclaimer + page marker
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(1)
    canvas.line(LM, 116, PAGE_W - RM, 116)
    canvas.setFillColor(colors.black)
    canvas.setFont(FONT, 8.5)
    canvas.drawString(LM, 100, FOOTER)
    canvas.drawRightString(PAGE_W - RM, 100, 'P1 / 1')
    canvas.restoreState()


def build_commencement_pdf(brand_id, v):
    brand = BRANDS.get(brand_id, BRANDS['wlth'])
    esc = PL.esc

    def g(key, default=''):
        val = v.get(key)
        val = val.strip() if isinstance(val, str) else val
        return val if val else default

    body = ParagraphStyle('b', fontName=FONT, fontSize=11, leading=13.2, textColor=INK)
    boldp = ParagraphStyle('bd', parent=body, fontName=BOLD)
    head = ParagraphStyle('h', parent=body, fontName=BOLD, fontSize=11)
    para = ParagraphStyle('p', parent=body, spaceAfter=10)
    item = ParagraphStyle('it', parent=body, leftIndent=29, bulletIndent=11,
                          spaceAfter=9, bulletFontName=FONT, bulletFontSize=8)
    lbl = ParagraphStyle('l', parent=body, fontName=BOLD, textColor=colors.white)
    val = ParagraphStyle('v', parent=body)

    frame = Frame(LM, 128, CONTENT_W, PAGE_H - 30 - 128,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=(PAGE_W, PAGE_H))
    doc.addPageTemplates([PageTemplate(id='cm', frames=[frame],
                                       onPage=lambda c, d: _page(c, d, brand))])

    flow = []
    # Builder block
    if g('builderName'):
        flow.append(Paragraph(esc(g('builderName')), body))
    for ln in _address_lines(g('builderAddress')):
        flow.append(Paragraph(esc(ln), body))
    if g('builderAbn'):
        flow.append(Paragraph(esc(g('builderAbn')), body))

    # Date
    flow.append(Spacer(1, 30))
    flow.append(Paragraph(esc(g('date')), body))

    # Salutation
    flow.append(Spacer(1, 32))
    flow.append(Paragraph(f'Dear {esc(g("builderName"))},' if g('builderName') else 'Dear,', body))

    # Fixed intro
    flow.append(Spacer(1, 26))
    flow.append(Paragraph('We are ready to start making progress payments.', head))
    flow.append(Spacer(1, 12))
    flow.append(Paragraph(
        'We want to let you know that we can start releasing progress payments for our '
        'mutual customers. This means you can now commence the construction or renovations.',
        para))

    # What you need to know? + table
    flow.append(Paragraph('What you need to know?', head))
    flow.append(Spacer(1, 10))
    rows = [
        [Paragraph('Customer Name(s):', lbl), Paragraph(esc(g('customerNames')) or '&nbsp;', val)],
        [Paragraph('Application Number:', lbl), Paragraph(esc(g('applicationNumber')) or '&nbsp;', val)],
        [Paragraph('Disbursement Total:', lbl), Paragraph(esc(g('disbursementTotal')) or '&nbsp;', val)],
        [Paragraph('Construction Address:', lbl), Paragraph(esc(g('constructionAddress')) or '&nbsp;', val)],
    ]
    table = Table(rows, colWidths=[150, CONTENT_W - 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), brand['label_bg']),
        ('BACKGROUND', (1, 0), (1, -1), VALUE_BG),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        # thin white gaps between the coloured cells
        ('LINEBELOW', (0, 0), (-1, -2), 2, colors.white),
    ]))
    flow.append(table)
    flow.append(Spacer(1, 20))

    # What you need to do? + list
    flow.append(Paragraph('What you need to do?', head))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph('When you have completed a stage of construction:', body))
    flow.append(Spacer(1, 8))
    for i, it in enumerate(LIST_ITEMS, 1):
        flow.append(Paragraph(it, item, bulletText=f'{i}.'))

    flow.append(Spacer(1, 6))
    flow.append(Paragraph(
        'Please be advised that every invoice received will require a progress inspection '
        'report to be completed prior to your invoice being processed. This may extend the '
        'time required prior to the invoice being paid.', para))
    flow.append(Paragraph(
        'This can take up to 10 - 15 business days and the progress payment will be processed '
        'once the inspection has been completed. Please consider this when determining your '
        'payment terms from our customers.', para))

    flow.append(Spacer(1, 14))
    flow.append(Paragraph('Yours Sincerely,', body))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(esc(brand['team']), body))

    doc.build(flow)
    return buf.getvalue()


if __name__ == '__main__':
    import sys, json
    sys.stdout.buffer.write(build_commencement_pdf(sys.argv[1], json.loads(sys.argv[2])))
