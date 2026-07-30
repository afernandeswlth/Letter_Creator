"""
Render a Formal Approval letter as a branded PDF, matching the WLTH / Mortgage
Mart "Formal Approval Letter" design: a light-grey header band ("Formal
Approval" + brand mark), a blue "Product Details" bar over a 4-column grid, and
a dark-navy footer band ("Yours Sincerely, The … Team" + brand mark).

Form-driven (no funder upload): the caller passes a dict of field values whose
keys are the approval field ids in app/utils/letterTypes.ts. Reuses reportlab
styling helpers from pdf_letter.
"""
import io
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
)

import pdf_letter as PL

HERE = os.path.dirname(__file__)
PAGE_W, PAGE_H = A4
LM = RM = 40
CONTENT_W = PAGE_W - LM - RM  # 515pt

BLUE = colors.HexColor('#2156bd')
HEADER_GREY = colors.HexColor('#f4f4f4')
NAVY = colors.HexColor('#16214a')
INK = colors.HexColor('#26303b')
LABEL = colors.HexColor('#3f4654')
GRID = colors.HexColor('#e5e7eb')
MUTED = colors.HexColor('#8a90a0')

HEADER_H = 42
FOOTER_H = 40

BRANDS = {
    'wlth': {
        'header': os.path.join(HERE, 'assets', 'wlth', 'approval-header.png'),
        'footer_logo': os.path.join(HERE, 'assets', 'wlth', 'footer-w.png'),
        'lender': 'WLTH', 'product': 'Ocean', 'team': 'The WLTH Team',
    },
    'mma': {
        'header': os.path.join(HERE, 'assets', 'mma', 'approval-header.png'),
        'footer_logo': os.path.join(HERE, 'assets', 'mma', 'footer-w.png'),
        'lender': 'Mortgage Mart of Australia', 'product': 'Ultra', 'team': 'The Mortgage Mart Team',
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


def _draw_logo(canvas, path, w, x, y_top):
    if os.path.exists(path):
        iw, ih = ImageReader(path).getSize()
        h = w * ih / iw
        canvas.drawImage(path, x, y_top - h, width=w, height=h, mask='auto')


def _page(canvas, doc, brand):
    canvas.saveState()
    # header grey band
    canvas.setFillColor(HEADER_GREY)
    canvas.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, stroke=0, fill=1)
    canvas.setFillColor(BLUE)
    canvas.setFont(PL.BOLD, 15)
    canvas.drawString(LM, PAGE_H - HEADER_H + 13, 'Formal Approval')
    _draw_logo(canvas, brand['header'], 92, PAGE_W - 92, PAGE_H)  # bleeds top-right
    # footer navy band
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, FOOTER_H, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont(PL.FONT, 9.5)
    canvas.drawString(LM, FOOTER_H / 2 - 3.5, f"Yours Sincerely, {brand['team']}")
    _draw_logo(canvas, brand['footer_logo'], 34, PAGE_W - RM - 34, FOOTER_H / 2 + 12)
    canvas.restoreState()


def build_approval_pdf(brand_id, v):
    brand = BRANDS.get(brand_id, BRANDS['wlth'])
    esc = PL.esc

    def g(key, default=''):
        val = v.get(key)
        val = val.strip() if isinstance(val, str) else val
        return val if val else default

    body = ParagraphStyle('fabody', fontName=PL.FONT, fontSize=9.5, leading=13.5, textColor=INK)
    tight = ParagraphStyle('fatight', parent=body, spaceAfter=0)
    intro = ParagraphStyle('faintro', parent=body, fontSize=13, leading=18, textColor=MUTED)
    head = ParagraphStyle('fahead', parent=body, fontSize=10, spaceAfter=4, spaceBefore=2, textColor=INK)
    lbl = ParagraphStyle('falbl', parent=body, textColor=LABEL)
    val = ParagraphStyle('faval', parent=body, textColor=INK)
    barst = ParagraphStyle('fabar', parent=body, fontName=PL.BOLD, textColor=colors.white)
    note = ParagraphStyle('fanote', parent=body, fontSize=8.5, leading=12, textColor=colors.HexColor('#5b6270'))
    disc = ParagraphStyle('fadisc', parent=body, fontSize=7.5, leading=11, textColor=colors.HexColor('#6b7280'), spaceAfter=6)
    cond = ParagraphStyle('facond', parent=body, leftIndent=16, firstLineIndent=-16, spaceAfter=8)

    def L(t):
        return Paragraph(esc(t) or '&nbsp;', lbl)

    def V(t):
        return Paragraph((esc(t) or '&nbsp;').replace('\n', '<br/>'), val)

    buf = io.BytesIO()
    frame = Frame(LM, FOOTER_H + 14, CONTENT_W, PAGE_H - HEADER_H - 16 - (FOOTER_H + 14),
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(buf, pagesize=A4)
    doc.addPageTemplates([PageTemplate(id='fa', frames=[frame],
                                       onPage=lambda c, d: _page(c, d, brand))])

    flow = []
    flow.append(Paragraph(esc(g('date')), tight))
    flow.append(Spacer(1, 14))
    flow.append(Paragraph(
        '<font color="#2156bd">We have the pleasure</font> in forwarding you Formal Approval '
        'for finance.<br/>The details of the loan are as follows:', intro))
    flow.append(Spacer(1, 16))

    # Applicant Overview
    flow.append(Paragraph('Applicant Overview', head))
    applicant = Table([
        [L('Borrower(s):'), V(g('borrowers'))],
        [L('Mortgagor(s):'), V(g('mortgagors'))],
        [L('Guarantor(s):'), V(g('guarantors'))],
    ], colWidths=[150, CONTENT_W - 150])
    applicant.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, GRID),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    flow += [applicant, Spacer(1, 16)]

    # Product Details — blue bar + 4-col grid
    cw = [116, 141, 116, 142]  # = 515
    rows = [
        [Paragraph('Product Details', barst), '', '', ''],
        [L('Lender'), V(g('lender', brand['lender'])), L('Product Name'), V(g('productName', brand['product']))],
        [L('Loan Account Number'), V(g('loanAccountNumber')), L('Loan Amount'), V(g('loanAmount'))],
        [L('Loan Term'), V(g('loanTerm')), L('Interest Rate'), V(g('interestRate'))],
        [L('Revert Rate'), V(g('revertRate')), L('Monthly Repayment'), V(g('monthlyRepayment'))],
        [L('Rate Type'), V(g('rateType', 'Variable')), L('Repayment Type'), V(g('repaymentType', 'P&I'))],
        [L('Annual Facility Fee'), V(g('annualFacilityFee', '$395.00')), L('Monthly Fees'), V(g('monthlyFees', '$0.00'))],
        [L('Offset Account'), V(g('offsetAccount', 'Yes')), L('Redraw Facility'), V(g('redrawFacility', 'N/A'))],
    ]
    product = Table(rows, colWidths=cw)
    product.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), BLUE),
        ('LEFTPADDING', (0, 0), (0, 0), 8), ('TOPPADDING', (0, 0), (-1, 0), 4), ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('GRID', (0, 1), (-1, -1), 0.5, GRID),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 1), (-1, -1), 8), ('RIGHTPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6), ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    flow += [product, Spacer(1, 10)]
    flow.append(Paragraph(NOTE, note))
    flow.append(Spacer(1, 14))

    # Security / Solicitor / Special conditions
    conds = g('specialConditions')
    if conds:
        items = [Paragraph(esc(line.strip()), cond) for line in conds.split('\n') if line.strip()]
        cond_cell = items if items else V('')
    else:
        cond_cell = V('')
    security = Table([
        [L('Security Property:'), V(g('securityProperty'))],
        [L('Our Panel Solicitor:'), V(g('panelSolicitor', 'Green Mortgage Lawyers'))],
        [L('Special Conditions:'), cond_cell],
    ], colWidths=[150, CONTENT_W - 150])
    security.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, GRID),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('VALIGN', (1, 2), (1, 2), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    flow += [security, Spacer(1, 16)]

    for para in DISCLAIMER:
        flow.append(Paragraph(esc(para), disc))

    doc.build(flow)
    return buf.getvalue()


if __name__ == '__main__':
    import sys, json
    sys.stdout.buffer.write(build_approval_pdf(sys.argv[1], json.loads(sys.argv[2])))
