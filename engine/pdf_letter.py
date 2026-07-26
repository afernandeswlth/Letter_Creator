"""
Render a welcome letter as a branded PDF that mirrors the WLTH letterhead:
full-width grey band + blue "W" banner top-right, bordered 2-column account
tables, and the WLTH address footer. Uses reportlab (pure Python).
"""
import io
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, PageBreak,
)

PAGE_W, PAGE_H = A4
LM = RM = 72
BAND_H = 38
FONT = 'Helvetica'
BOLD = 'Helvetica-Bold'
INK = colors.HexColor('#1e2430')
BAND = colors.HexColor('#f1f2f4')
BORDER = colors.HexColor('#cbccd0')
LINK = '#0000ff'  # hyperlink blue, matching the real letters

HERE = os.path.dirname(__file__)

BRANDS = {
    'wlth': {
        'name': 'WLTH',
        'banner': os.path.join(HERE, 'assets', 'wlth', 'banner.png'),
        'portal_url': 'www.wlth.com', 'portal_tail': ' and click on the Portal button.',
        'phone': '13 WLTH', 'email': 'Hello@wlth.com', 'signoff': 'The WLTH team.',
        'footer': [
            ['WLTH', 'Level 2, 15 James St', 'hello@wlth.com', 'wlth.com'],
            ['Fortitude Valley', '13 WLTH', '', ''],
            ['QLD 4006 Australia', 'ACN: 639 591 245', '', ''],
        ],
    },
    'mma': {
        'name': 'Mortgage Mart',
        'banner': os.path.join(HERE, 'assets', 'mma', 'banner.png'),
        'portal_url': 'https://online.originmms.com.au/ib/mortgagemart', 'portal_tail': '',
        'phone': '1300 650 200', 'email': 'hello@wlth.com', 'signoff': 'The Mortgage Mart Team.',
        'footer': [
            ['WLTH', 'Level 2, 15 James St', 'hello@wlth.com', 'wlth.com'],
            ['Fortitude Valley', '13 WLTH', '', ''],
            ['QLD 4006 Australia', 'ACN: 639 591 245', '', ''],
        ],
    },
}

# --- paragraph styles -------------------------------------------------------
def _styles():
    body = ParagraphStyle('body', fontName=FONT, fontSize=10.5, leading=15,
                          textColor=INK, spaceAfter=10, alignment=TA_LEFT)
    return {
        'body': body,
        'tight': ParagraphStyle('tight', parent=body, spaceAfter=0, leading=14),
        'bold': ParagraphStyle('bold', parent=body, fontName=BOLD),
        # section headings kept with the table that follows them
        'head': ParagraphStyle('head', parent=body, keepWithNext=True, spaceAfter=6),
        'headb': ParagraphStyle('headb', parent=body, fontName=BOLD, keepWithNext=True, spaceAfter=6),
        'cell': ParagraphStyle('cell', parent=body, spaceAfter=0, leading=14),
        'cellb': ParagraphStyle('cellb', parent=body, fontName=BOLD, spaceAfter=0, leading=14),
        'bullet': ParagraphStyle('bullet', parent=body, leftIndent=24, bulletIndent=8,
                                 spaceAfter=3, leading=15),
    }


def esc(v):
    """Escape text for reportlab's mini-markup (so & < > are literal)."""
    return (v or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _page(canvas, doc, brand):
    canvas.saveState()
    # full-width brand banner across the top (matches the real letterhead)
    b = brand['banner']
    if os.path.exists(b):
        h = 49.6
        canvas.drawImage(b, -3, PAGE_H - h, width=PAGE_W + 6, height=h, mask='auto')
    # footer
    canvas.setFont(FONT, 8)
    canvas.setFillColor(colors.HexColor('#8a90a0'))
    cols = [LM, LM + 210, LM + 330, LM + 470]
    for r, row in enumerate(brand['footer']):
        y = 52 - r * 10
        for c, txt in enumerate(row):
            if txt:
                canvas.drawString(cols[c], y, txt)
    canvas.restoreState()


def _kv_table(rows, styles, bold_label=False, bold_value=False, pad=5):
    data = [[Paragraph(k, styles['cellb'] if bold_label else styles['cell']),
             Paragraph(v or '&nbsp;', styles['cellb'] if bold_value else styles['cell'])]
            for k, v in rows]
    t = Table(data, colWidths=[170, 231])
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), pad),
        ('BOTTOMPADDING', (0, 0), (-1, -1), pad),
    ]))
    return t


def build_pdf(d, brand_id, dd_bsb, dd_account, smsf_number=None):
    brand = BRANDS.get(brand_id, BRANDS['wlth'])
    s = _styles()
    buf = io.BytesIO()

    frame = Frame(LM, 64, PAGE_W - LM - RM, PAGE_H - BAND_H - 30 - 64,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(buf, pagesize=A4)
    doc.addPageTemplates([PageTemplate(id='wlth', frames=[frame],
                                       onPage=lambda c, dd: _page(c, dd, brand))])

    def P(text, st='body'):
        return Paragraph(text, s[st])

    flow = []
    flow.append(P(esc(d['recipient_name'])))
    for a in d['address']:
        flow.append(P(esc(a), 'tight'))
    flow.append(Spacer(1, 12))
    flow.append(P(esc(d['date'])))
    flow.append(Spacer(1, 12))
    flow.append(P(esc(d['greeting'])))
    flow.append(P(f"Congratulations on the settlement of your new Home Loan with "
                  f"<b>{esc(d['lender'])}</b> on {esc(d['settlement_date'])}!"))
    flow.append(P("This letter contains important information regarding your new home loan facility."))

    # customer numbers — bold label + value, borderless aligned
    cust = [('Your Customer Number:', d.get('customer_number', ''))]
    if not d['is_entity'] and smsf_number:
        cust.append(('Your Customer SMSF Number:', smsf_number))
    elif d['is_entity']:
        cust = [('Your Customer SMSF Number:', d.get('customer_number', ''))]
    cust.append(('Your Loan Facility Number:', d.get('loan_facility_number', '')))
    ct = Table([[Paragraph(k, s['bold']), Paragraph(esc(v), s['bold'])] for k, v in cust],
               colWidths=[220, 220])
    ct.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0),
                            ('TOPPADDING', (0, 0), (-1, -1), 3),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
    flow += [Spacer(1, 4), ct, Spacer(1, 10)]

    flow.append(P("In order to best assist you, your Customer and/or Loan Facility Number is "
                  "required whenever you contact us to discuss your home loan."))
    flow.append(P("You can find the key details of your individual loan account(s) below. "
                  "Detailed financial statements will be issued every 6 months (in January and "
                  "July each year), however you can choose to access your account(s) information "
                  "online at any time."))
    flow.append(P("Internet Account Access"))
    flow.append(P("Internet Account Access is an easy and reliable way for you to check your "
                  "balance and recent payment history, as well as make repayments or transfer "
                  "funds over the internet, at any time most convenient for you."))

    # numbered list (portal URL shown as a blue link)
    portal = f'<font color="{LINK}">{esc(brand["portal_url"])}</font>{esc(brand["portal_tail"])}'
    items = [
        f"You should have already received instructions on how to access your online accounts "
        f"as per below.<br/>{portal}",
        "Your User ID has been provided via email.",
        "Your temporary password has been provided via SMS.",
    ]
    nl = Table([['', Paragraph(f"{i + 1}.", s['cell']), Paragraph(t, s['cell'])]
                for i, t in enumerate(items)], colWidths=[18, 20, 409])
    nl.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                            ('TOPPADDING', (0, 0), (-1, -1), 2),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    flow += [nl, Spacer(1, 8)]
    flow.append(P("Please contact us on 1300 767 023 between 8am - 7pm Monday to Friday (AEST) "
                  "or 8am - 5pm Saturday (AEST) if you have not received your User ID or temporary "
                  "password. Once you have changed your initial password, you can access your "
                  "account online 24 hours a day, 7 days a week."))

    # Customer Support begins on page 2 (matches the real letter)
    flow.append(PageBreak())
    email = f'<font color="{LINK}">{esc(brand["email"])}</font>'
    flow.append(P("Customer Support"))
    flow.append(P(f"If you have any questions please feel free to call us on {esc(brand['phone'])} "
                  f"between Monday to Friday 9am to 5pm or email us at {email}."))
    flow.append(Spacer(1, 8))

    # Direct debit
    flow.append(P("Your Nominated Direct Debit Account Details:", 'head'))
    flow.append(_kv_table([('BSB Number:', esc(dd_bsb)), ('Account Number:', esc(dd_account))], s, pad=4))
    flow.append(Spacer(1, 12))

    # Loan facility details
    flow.append(P("Your Loan Facility Details:", 'headb'))
    guarantors = esc(d.get('guarantors_names', '')).replace('\n\n', '<br/><br/>').replace('\n', '<br/>')
    flow.append(_kv_table([
        ('Loan Purpose:', esc(d.get('loan_purpose', ''))),
        ('Loan Facility Number:', esc(d.get('loan_facility_number', ''))),
        ('Loan Facility Amount:', esc(d.get('loan_amount', ''))),
        ("Borrower’s/s’ Names", esc(d.get('borrowers_names', ''))),
        ('Guarantors Names', guarantors),
    ], s, pad=6))
    flow.append(Spacer(1, 12))
    flow.append(_kv_table([('Loan Account Number:', esc(d.get('loan_facility_number', '')))],
                          s, bold_label=True, bold_value=True, pad=6))
    flow.append(Spacer(1, 12))

    # Loan account details
    flow.append(P("Your Loan Account Details:", 'headb'))
    flow.append(_kv_table([
        ('BSB Number:', esc(d.get('loan_bsb', ''))),
        ('Loan Account Number:', esc(d.get('loan_facility_number', ''))),
        ('Current Account Balance:', esc(d.get('current_balance', ''))),
        ('Loan Account Term:', esc(d.get('loan_term', ''))),
        ('Interest Type:', esc(d.get('interest_type', ''))),
        ('Current interest Rate:', esc(d.get('interest_rate', ''))),
        ('Repayment Type:', esc(d.get('repayment_type', ''))),
        ('Interest Only Period (Months):', esc(d.get('io_period', ''))),
    ], s, pad=6))
    flow.append(Spacer(1, 10))

    # repayments start on the last page (matches the real letter).
    # repayment_lines carry the funder's bold runs (as <b>) and bullet flags.
    flow.append(PageBreak())
    for item in d.get('repayment_lines', []):
        if item.get('bullet'):
            flow.append(Paragraph(item['html'], s['bullet'], bulletText='•'))
        else:
            flow.append(P(item['html'], 'body'))
    flow.append(Spacer(1, 4))

    # offset (only when the loan has an offset account)
    if d.get('has_offset'):
        flow.append(P("Your Linked Offset Account Details:", 'headb'))
        flow.append(_kv_table([
            ('BSB Number:', esc(d.get('loan_bsb', ''))),
            ('Offset Account Number:', esc(d.get('offset_account', ''))),
            ('Current Balance:', esc(d.get('offset_balance', ''))),
        ], s, pad=6))
    flow.append(Spacer(1, 16))
    flow.append(P("Yours sincerely,", 'tight'))
    flow.append(P(brand['signoff'], 'tight'))

    doc.build(flow)
    return buf.getvalue()
