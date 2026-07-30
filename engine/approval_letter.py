"""
Render a Formal Approval letter as a branded PDF, mirroring the WLTH / Mortgage
Mart "Formal Approval Letter" Word templates. Form-driven (no funder upload):
the caller passes a dict of field values. Reuses the shared reportlab
primitives + footer from pdf_letter.
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
LM = RM = 72
CONTENT_W = PAGE_W - LM - RM  # 451pt

BRANDS = {
    'wlth': {
        'header': os.path.join(HERE, 'assets', 'wlth', 'approval-header.png'),
        'header_align': 'right', 'header_w': 150,
        'lender': 'WLTH', 'product': 'Ocean', 'team': 'The WLTH Team',
    },
    'mma': {
        'header': os.path.join(HERE, 'assets', 'mma', 'approval-header.png'),
        'header_align': 'left', 'header_w': 140,
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

NOTE = ('Note that the interest rate is generally 2% higher if you are in default. '
        'The actual increased interest rate will be described in your loan agreement '
        'terms and conditions.')


def _page(canvas, doc, brand):
    canvas.saveState()
    # header graphic (brand letterhead mark)
    h = brand['header']
    if os.path.exists(h):
        iw, ih = ImageReader(h).getSize()
        w = brand['header_w']
        hh = w * ih / iw
        x = PAGE_W - w if brand['header_align'] == 'right' else LM
        canvas.drawImage(h, x, PAGE_H - hh, width=w, height=hh, mask='auto')
    # shared WLTH footer (same as the welcome letters)
    canvas.setFont(PL.FONT, 8)
    canvas.setFillColor(colors.HexColor('#8a90a0'))
    cols = [LM, LM + 210, LM + 330, LM + 470]
    for r, row in enumerate(PL.BRANDS['wlth']['footer']):
        y = 52 - r * 10
        for c, txt in enumerate(row):
            if txt:
                canvas.drawString(cols[c], y, txt)
    canvas.restoreState()


def _grid(data, col_widths, styles):
    """A bordered table; each cell is a Paragraph (col 0/2 = bold labels)."""
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, PL.BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return t


def build_approval_pdf(brand_id, v):
    brand = BRANDS.get(brand_id, BRANDS['wlth'])
    s = PL._styles()
    esc = PL.esc

    def g(key, default=''):
        val = (v.get(key) or '').strip() if isinstance(v.get(key), str) else v.get(key)
        return val if val else default

    title = ParagraphStyle('fatitle', parent=s['body'], fontName=PL.BOLD, fontSize=20,
                           leading=24, spaceAfter=2, textColor=PL.INK)
    small = ParagraphStyle('fasmall', parent=s['body'], fontSize=8.5, leading=12, spaceAfter=7,
                           textColor=colors.HexColor('#5b6270'))

    def cell(txt, bold=False):
        return Paragraph(esc(txt) or '&nbsp;', s['cellb'] if bold else s['cell'])

    buf = io.BytesIO()
    frame = Frame(LM, 62, CONTENT_W, PAGE_H - 118 - 62,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(buf, pagesize=A4)
    doc.addPageTemplates([PageTemplate(id='fa', frames=[frame],
                                       onPage=lambda c, d: _page(c, d, brand))])

    def P(text, st='body'):
        return Paragraph(text, s[st])

    flow = []
    flow.append(Paragraph('Formal Approval', title))
    flow.append(Spacer(1, 10))
    flow.append(P(esc(g('date', '')), 'tight'))
    flow.append(Spacer(1, 10))
    flow.append(P('We have the pleasure in forwarding you Formal Approval for finance.', 'tight'))
    flow.append(P('The details of the loan are as follows:'))

    # Applicant Overview
    flow.append(P('Applicant Overview', 'headb'))
    flow.append(_grid([
        [cell('Borrower(s):', True), cell(g('borrowers'))],
        [cell('Mortgagor(s):', True), cell(g('mortgagors'))],
        [cell('Guarantor(s):', True), cell(g('guarantors'))],
    ], [150, CONTENT_W - 150], s))
    flow.append(Spacer(1, 12))

    # Product Details (4-column grid)
    flow.append(P('Product Details', 'headb'))
    cw = [108, 117, 108, 118]  # = 451
    rows = [
        ('Lender', g('lender', brand['lender']), 'Product Name', g('productName', brand['product'])),
        ('Loan Account Number(s)', g('loanAccountNumber'), 'Loan Amount', g('loanAmount')),
        ('Loan Term', g('loanTerm'), 'Interest Rate', g('interestRate')),
        ('Revert Rate', g('revertRate'), 'Monthly Repayment', g('monthlyRepayment')),
        ('Rate Type', g('rateType', 'Variable'), 'Repayment Type', g('repaymentType', 'P&I')),
        ('Annual Facility Fee', g('annualFacilityFee', '$395.00'), 'Monthly Fees', g('monthlyFees', '$0.00')),
        ('Offset Account', g('offsetAccount', 'Yes'), 'Redraw Facility', g('redrawFacility')),
    ]
    flow.append(_grid(
        [[cell(a, True), cell(b), cell(c, True), cell(d)] for a, b, c, d in rows], cw, s))
    flow.append(Spacer(1, 10))

    flow.append(P(NOTE, 'tight'))
    flow.append(Spacer(1, 12))

    # Security / Solicitor / Special conditions
    flow.append(_grid([
        [cell('Security Property:', True), cell(g('securityProperty'))],
        [cell('Our Panel Solicitor:', True), cell(g('panelSolicitor', 'Green Mortgage Lawyers'))],
        [cell('Special Conditions:', True), cell(g('specialConditions'))],
    ], [150, CONTENT_W - 150], s))
    flow.append(Spacer(1, 16))

    flow.append(P('Yours Sincerely,', 'tight'))
    flow.append(P(esc(brand['team']), 'tight'))
    flow.append(Spacer(1, 12))
    for para in DISCLAIMER:
        flow.append(Paragraph(esc(para), small))

    doc.build(flow)
    return buf.getvalue()


if __name__ == '__main__':
    import sys, json
    sys.stdout.buffer.write(build_approval_pdf(sys.argv[1], json.loads(sys.argv[2])))
