"""
Render a Pre-Approval ("Approval in Principle") letter as a branded PDF, matching
the WLTH / Mortgage Mart "Pre-Approval Letter" template. It reuses the Formal
Approval letterhead (header band + title, footer band + sign-off/logo) but with a
congratulations intro, a shorter 4-row Product Details table, a single Security
Property row, and the pre-approval disclaimer (60-day validity).

Form-driven: field ids match app/utils/letterTypes.ts.
"""
import io
import re

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, KeepInFrame,
)

import pdf_letter as PL
from approval_letter import (
    BRANDS, PAGE_W, PAGE_H, LM, RM, CONTENT_W, INK, INTRO_GREY, GRIDC, ZEBRA,
    FONT, BOLD, _page,
)

DISCLAIMER = [
    'This approval is based on the information you have provided in your loan application and is '
    'subject to any additional information we may require from you. Your pre-approval is valid for a '
    'period of 60 days from the date when your application form was signed.',
    'This approval may be withdrawn at any time if anything occurs which in the opinion of its '
    'Funders and/or Insurers that adversely affects the loan proposal as they understand it. This '
    'document is not an offer of finance.',
    'This information is current at the date of this letter and is based on the details you have '
    'provided on your current financial position. These details may change for a number of reasons, '
    'including financial positions, interest rate or package concession changes.',
    'If you request or make any changes to the application details and its Funders and/or Insurers '
    'agree, additional costs and processing time should be allowed for your loan to be re-approved.',
]


def build_preapproval_pdf(brand_id, v):
    """One page: try full spacing, then tighten gaps, then shrink as a last resort."""
    import fitz
    for gap_scale in (1.0, 0.85, 0.7, 0.55, 0.4, 0.3):
        pdf = _build_pdf(brand_id, v, gap_scale=gap_scale)
        if fitz.open(stream=pdf, filetype='pdf').page_count == 1:
            return pdf
    return _build_pdf(brand_id, v, gap_scale=0.3, shrink=True)


def _build_pdf(brand_id, v, gap_scale=1.0, shrink=False):
    brand = BRANDS.get(brand_id, BRANDS['wlth'])
    esc = PL.esc

    def g(key, default=''):
        val = v.get(key)
        val = val.strip() if isinstance(val, str) else val
        return val if val else default

    body = ParagraphStyle('b', fontName=FONT, fontSize=9, leading=11.5, textColor=INK)
    date_s = ParagraphStyle('d', parent=body, fontSize=10, leading=13)
    intro = ParagraphStyle('i', parent=body, fontSize=14, leading=19.8, textColor=INTRO_GREY)
    head = ParagraphStyle('h', parent=body, fontSize=10, leading=13)
    tsize = brand.get('tsize', 9)
    lead = tsize + 0.6
    lbl = ParagraphStyle('l', parent=body, fontSize=tsize, leading=lead)
    val = ParagraphStyle('v', parent=body, fontSize=tsize, leading=lead)
    bar = ParagraphStyle('bar', parent=body, fontSize=tsize, textColor=colors.white)
    disc = ParagraphStyle('dc', parent=body, leading=11, spaceAfter=11)

    def L(t):
        return Paragraph(esc(t) or '&nbsp;', lbl)

    def V(t):
        return Paragraph((esc(t) or '&nbsp;').replace('\n', '<br/>'), val)

    def grid_style(bar_row=False):
        s = [
            ('GRID', (0, 1 if bar_row else 0), (-1, -1), 0.25, GRIDC),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 4.6), ('BOTTOMPADDING', (0, 0), (-1, -1), 4.6),
        ]
        if bar_row:
            s += [('SPAN', (0, 0), (-1, 0)), ('BACKGROUND', (0, 0), (-1, 0), brand['bar']),
                  ('TOPPADDING', (0, 0), (-1, 0), 2.5), ('BOTTOMPADDING', (0, 0), (-1, 0), 2.5),
                  ('BACKGROUND', (0, 1), (0, -1), ZEBRA), ('BACKGROUND', (2, 1), (2, -1), ZEBRA),
                  ('LINEBELOW', (0, 1), (0, -2), 1, colors.white),
                  ('LINEBELOW', (2, 1), (2, -2), 1, colors.white)]
        return TableStyle(s)

    def G(x):
        return Spacer(1, x * gap_scale)

    buf = io.BytesIO()
    frame_h = PAGE_H - 61 - 60
    frame = Frame(LM, 60, CONTENT_W, frame_h,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(buf, pagesize=(PAGE_W, PAGE_H))
    doc.addPageTemplates([PageTemplate(id='pa', frames=[frame],
                                       onPage=lambda c, d: _page(c, d, brand, 'Approval in Principle'))])

    flow = []
    flow.append(Paragraph(esc(g('date')), date_s))
    flow.append(G(20))
    flow.append(Paragraph(
        f'<font color="{brand["accent"]}">Congratulations</font> your loan application is '
        'pre-approved!<br/>The details of the loan are as follows:', intro))
    flow.append(G(16))

    flow.append(Paragraph('Applicant Overview', head))
    flow.append(G(11))
    ov_rows = [[L('Borrower(s):'), V(g('borrowers'))]]
    if g('mortgagors'):
        ov_rows.append([L('Mortgagor(s):'), V(g('mortgagors'))])
    if g('guarantors'):
        ov_rows.append([L('Guarantor(s):'), V(g('guarantors'))])
    ov = Table(ov_rows, colWidths=brand['acols'])
    ov.setStyle(grid_style())
    flow += [ov, G(24)]

    # Interest-only: append the IO period, e.g. "Interest Only – 5 Years".
    rtype = g('repaymentType', 'P&I')
    if 'interest only' in rtype.lower():
        m = re.search(r'\d+', g('ioYears'))
        if m:
            n = m.group()
            rtype = f"Interest Only – {n} {'Year' if n == '1' else 'Years'}"
        else:
            rtype = 'Interest Only'

    prow = brand.get('prow', 20.7)
    rows = [
        [Paragraph('Product Details', bar), '', '', ''],
        [L('Lender'), V(g('lender', brand['lender'])), L('Product Name'), V(g('productName', brand['product']))],
        [L('Application Reference No.'), V(g('applicationNumber')), L('Loan Amount'), V(g('loanAmount'))],
        [L('Loan Term'), V(g('loanTerm')), L('Interest Rate'), V(g('interestRate'))],
        [L('Rate Type'), V(g('rateType', 'Variable')), L('Repayment Type'), V(rtype)],
    ]
    psty = grid_style(bar_row=True)
    psty.add('TOPPADDING', (0, 1), (-1, -1), 0.5)
    psty.add('BOTTOMPADDING', (0, 1), (-1, -1), 0.5)
    product = Table(rows, colWidths=brand['pcols'], rowHeights=[None] + [prow] * (len(rows) - 1))
    product.setStyle(psty)
    flow += [product, G(24)]

    sec = Table([[L('Security Property:'), V(g('securityProperty', 'To be advised'))]],
                colWidths=brand['acols'])
    sec.setStyle(grid_style())
    flow += [sec, G(brand.get('disc_gap', 21))]

    for para in DISCLAIMER:
        flow.append(Paragraph(esc(para), disc))

    if shrink:
        flow = [KeepInFrame(CONTENT_W, frame_h, flow, mode='shrink', hAlign='LEFT', vAlign='TOP')]
    doc.build(flow)
    return buf.getvalue()


if __name__ == '__main__':
    import sys, json
    sys.stdout.buffer.write(build_preapproval_pdf(sys.argv[1], json.loads(sys.argv[2])))
