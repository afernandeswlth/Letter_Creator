"""
Render a Formal Approval letter as a branded PDF, matching the WLTH / Mortgage
Mart "Formal Approval Letter" example pixel-for-pixel: US-Letter page, light-grey
header band ("Formal Approval" 15pt + brand mark, both bleeding), 14pt intro with
a blue lead-in, 9pt body/tables in #46494f, a blue "Product Details" bar over a
4-column grid, and a dark-navy footer band ("Yours Sincerely, The … Team" + brand
mark). Measurements taken directly from the example PDF.

Form-driven (no funder upload): the caller passes a dict of field values whose
keys are the approval field ids in app/utils/letterTypes.ts.

Font note: the example is set in Calibri, which isn't available on the server;
we use Helvetica (metric-compatible with Arial) — everything else matches.
"""
import io
import os

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
)

import pdf_letter as PL

HERE = os.path.dirname(__file__)
PAGE_W, PAGE_H = letter  # 612 x 792
LM = RM = 22
CONTENT_W = PAGE_W - LM - RM  # 568

FONT, BOLD = 'Helvetica', 'Helvetica-Bold'
INK = colors.HexColor('#46494f')
TITLE_BLUE = colors.HexColor('#2157be')
INTRO_BLUE = colors.HexColor('#2157be')
INTRO_GREY = colors.HexColor('#7a8890')
BAR_BLUE = colors.HexColor('#2157be')
GREY_BAND = colors.HexColor('#f4f4f4')
NAVY = colors.HexColor('#16224b')
GRIDC = colors.HexColor('#e6e8eb')
ZEBRA = colors.HexColor('#e9ecee')  # alternating row shade

BRANDS = {
    'wlth': {
        'header': os.path.join(HERE, 'assets', 'wlth', 'approval-header.png'),
        'footer_logo': os.path.join(HERE, 'assets', 'wlth', 'footer-w.png'),
        'lender': 'WLTH', 'product': 'Ocean', 'team': 'The WLTH Team',
        # light theme
        'band': colors.HexColor('#f4f4f4'), 'title': colors.HexColor('#2157be'),
        'bar': colors.HexColor('#2157be'), 'accent': '#2157be',
        'footer_band': colors.HexColor('#16224b'),
    },
    'mma': {
        'header': os.path.join(HERE, 'assets', 'mma', 'approval-header.png'),
        'footer_logo': os.path.join(HERE, 'assets', 'mma', 'footer-imm.png'),
        'lender': 'Mortgage Mart of Australia', 'product': 'Ultra', 'team': 'The Mortgage Mart Team',
        # dark theme
        'band': colors.HexColor('#1f232d'), 'title': colors.white,
        'bar': colors.black, 'accent': '#1f232d',
        'footer_band': colors.HexColor('#1f232d'),
    },
}

DISCLAIMER = [
    'This approval may be withdrawn at any time if anything occurs which in the opinion of its '
    'Funders and/or Insurers that adversely affects the loan proposal as they understand it. '
    'This document is not an offer of finance.',
    'Your loan offer documents will be issued in the near future, these contain the terms and '
    'conditions that make up the offer. You will need to review, sign, and return the loan '
    'documents, and satisfy any pre-settlement conditions, prior to any funds being made available.',
    'If you request or make any changes to the application details and its Funders and/or Insurers '
    'agree, additional costs and processing time should be allowed for your loan to be re-approved.',
]

NOTE = ('Note that the interest rate is generally 2% higher if you are in default.<br/>'
        'The actual increased interest rate will be described in your loan agreement '
        'terms and conditions.')


def _draw_logo(canvas, path, x, y, w, h):
    if os.path.exists(path):
        canvas.drawImage(path, x, y, width=w, height=h, mask='auto')


def _page(canvas, doc, brand):
    canvas.saveState()
    # header band (full width) + title + brand mark (bleeds top-right)
    canvas.setFillColor(brand['band'])
    canvas.rect(0, PAGE_H - 47, PAGE_W, 47, stroke=0, fill=1)
    canvas.setFillColor(brand['title'])
    canvas.setFont(BOLD, 15)
    canvas.drawString(LM, PAGE_H - 31.5, 'Formal Approval')
    _draw_logo(canvas, brand['header'], PAGE_W - 82.2, PAGE_H - 47.2, 82.2, 46.5)
    # footer band (content width, not full-bleed) + sign-off + brand mark
    canvas.setFillColor(brand['footer_band'])
    canvas.rect(LM, 31, CONTENT_W, 25, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont(FONT, 9)
    canvas.drawString(LM + 8, 39.8, f"Yours Sincerely, {brand['team']}")
    fl = brand['footer_logo']
    if os.path.exists(fl):
        iw, ih = ImageReader(fl).getSize()
        fh = 14.0
        fw = fh * iw / ih
        canvas.drawImage(fl, PAGE_W - RM - 8 - fw, 31 + (25 - fh) / 2, width=fw, height=fh, mask='auto')
    canvas.restoreState()


def build_approval_pdf(brand_id, v):
    brand = BRANDS.get(brand_id, BRANDS['wlth'])
    esc = PL.esc

    def g(key, default=''):
        val = v.get(key)
        val = val.strip() if isinstance(val, str) else val
        return val if val else default

    body = ParagraphStyle('b', fontName=FONT, fontSize=9, leading=11.5, textColor=INK)
    tight = ParagraphStyle('t', parent=body, spaceAfter=0)
    date_s = ParagraphStyle('d', parent=body, fontSize=10, leading=13)
    intro = ParagraphStyle('i', parent=body, fontSize=14, leading=19.8, textColor=INTRO_GREY)
    head = ParagraphStyle('h', parent=body, fontSize=10, leading=13)
    lbl = ParagraphStyle('l', parent=body)
    val = ParagraphStyle('v', parent=body)
    bar = ParagraphStyle('bar', parent=body, textColor=colors.white)
    note = ParagraphStyle('n', parent=body, leading=11)
    disc = ParagraphStyle('dc', parent=body, leading=11, spaceAfter=11)
    cond = ParagraphStyle('c', parent=body, leftIndent=15, firstLineIndent=-15, spaceAfter=9)

    def L(t):
        return Paragraph(esc(t) or '&nbsp;', lbl)

    def V(t):
        return Paragraph((esc(t) or '&nbsp;').replace('\n', '<br/>'), val)

    tp = dict(topPadding=4.6, bottomPadding=4.6, leftPadding=5, rightPadding=5)

    buf = io.BytesIO()
    frame = Frame(LM, 60, CONTENT_W, PAGE_H - 51 - 60,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(buf, pagesize=(PAGE_W, PAGE_H))
    doc.addPageTemplates([PageTemplate(id='fa', frames=[frame],
                                       onPage=lambda c, d: _page(c, d, brand))])

    def grid_style(bar_row=False):
        s = [
            ('GRID', (0, 1 if bar_row else 0), (-1, -1), 0.5, GRIDC),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 4.6), ('BOTTOMPADDING', (0, 0), (-1, -1), 4.6),
        ]
        if bar_row:
            s += [('SPAN', (0, 0), (-1, 0)), ('BACKGROUND', (0, 0), (-1, 0), brand['bar']),
                  ('TOPPADDING', (0, 0), (-1, 0), 2.5), ('BOTTOMPADDING', (0, 0), (-1, 0), 2.5),
                  # column-based zebra: label columns gray, value columns white
                  ('BACKGROUND', (0, 1), (0, -1), ZEBRA),
                  ('BACKGROUND', (2, 1), (2, -1), ZEBRA),
                  # white row separators inside the gray label columns
                  ('LINEBELOW', (0, 1), (0, -2), 1, colors.white),
                  ('LINEBELOW', (2, 1), (2, -2), 1, colors.white)]
        return TableStyle(s)

    flow = []
    flow.append(Paragraph(esc(g('date')), date_s))
    flow.append(Spacer(1, 15))
    flow.append(Paragraph(
        f'<font color="{brand["accent"]}">We have the pleasure</font> in forwarding you Formal Approval '
        'for finance.<br/>The details of the loan are as follows:', intro))
    flow.append(Spacer(1, 14))

    flow.append(Paragraph('Applicant Overview', head))
    flow.append(Spacer(1, 4))
    ov = Table([
        [L('Borrower(s):'), V(g('borrowers'))],
        [L('Mortgagor(s):'), V(g('mortgagors'))],
        [L('Guarantor(s):'), V(g('guarantors'))],
    ], colWidths=[116, CONTENT_W - 116])
    ov.setStyle(grid_style())
    flow += [ov, Spacer(1, 18)]

    rows = [
        [Paragraph('Product Details', bar), '', '', ''],
        [L('Lender'), V(g('lender', brand['lender'])), L('Product Name'), V(g('productName', brand['product']))],
        [L('Loan Account Number'), V(g('loanAccountNumber')), L('Loan Amount'), V(g('loanAmount'))],
        [L('Loan Term'), V(g('loanTerm')), L('Interest Rate'), V(g('interestRate'))],
        [L('Revert Rate'), V(g('revertRate')), L('Monthly Repayment'), V(g('monthlyRepayment'))],
        [L('Rate Type'), V(g('rateType', 'Variable')), L('Repayment Type'), V(g('repaymentType', 'P&I'))],
        [L('Annual Facility Fee'), V(g('annualFacilityFee', '$395.00')), L('Monthly Fees'), V(g('monthlyFees', '$0.00'))],
        [L('Offset Account'), V(g('offsetAccount', 'Yes')), L('Redraw Facility'), V(g('redrawFacility', 'N/A'))],
    ]
    product = Table(rows, colWidths=[150, 135, 149, 134])
    product.setStyle(grid_style(bar_row=True))
    flow += [product, Spacer(1, 10)]

    flow.append(Paragraph(NOTE, note))
    flow.append(Spacer(1, 16))

    conds = g('specialConditions')
    cond_cell = [Paragraph(esc(l.strip()), cond) for l in conds.split('\n') if l.strip()] if conds else V('')
    sec = Table([
        [L('Security Property:'), V(g('securityProperty'))],
        [L('Our Panel Solicitor:'), V(g('panelSolicitor', 'Green Mortgage Lawyers'))],
        [L('Special Conditions:'), cond_cell],
    ], colWidths=[116, CONTENT_W - 116])
    sty = grid_style()
    sty.add('VALIGN', (1, 2), (1, 2), 'TOP')
    sec.setStyle(sty)
    flow += [sec, Spacer(1, 16)]

    for para in DISCLAIMER:
        flow.append(Paragraph(esc(para), disc))

    doc.build(flow)
    return buf.getvalue()


if __name__ == '__main__':
    import sys, json
    sys.stdout.buffer.write(build_approval_pdf(sys.argv[1], json.loads(sys.argv[2])))
