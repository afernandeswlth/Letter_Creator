"""
Render a Custom (letterhead) letter as a branded PDF, matching the WLTH / Mortgage
Mart "Letterhead Template": A4 page, a brand header band with the corner mark
(light-grey + blue W for WLTH, dark-navy + iMM for MMA), a left-aligned body
(recipient block, bold date, "Dear …", free-text body, sign-off, signature line
+ name/title), and the WLTH corporate footer block. Measurements taken directly
from the template PDFs.

Form-driven: the caller passes a dict of field values whose keys are the custom
field ids in app/utils/letterTypes.ts.

Font note: the template is set in Arial; we use Helvetica (metric-compatible).
"""
import io
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
)

import pdf_letter as PL

HERE = os.path.dirname(__file__)
PAGE_W, PAGE_H = 596, 842  # A4 (matches the template)
LM = RM = 72
CONTENT_W = PAGE_W - LM - RM  # 452

FONT, BOLD = 'Helvetica', 'Helvetica-Bold'
INK = colors.black
FOOT_GREY = colors.HexColor('#8a949e')
HEAD_H = 50  # header band height

BRANDS = {
    'wlth': {
        'header': os.path.join(HERE, 'assets', 'wlth', 'approval-header.png'),
        'band': colors.HexColor('#f4f4f4'),
    },
    'mma': {
        'header': os.path.join(HERE, 'assets', 'mma', 'approval-header.png'),
        'band': colors.HexColor('#1f232d'),
    },
}

# Corporate footer — the WLTH block, shown on both templates. Columns keyed by x.
FOOTER_COLS = [
    (72, ['WLTH']),
    (216, ['Level 2, 15 James St', 'Fortitude Valley', 'QLD 4006 Australia']),
    (324, ['hello@wlth.com', '13 WLTH', 'ACN: 639 591 245']),
    (468, ['wlth.com']),
]


def _address_lines(addr):
    """The recipient enters the address on one line; format it onto two —
    street on line 1, suburb/state/postcode on line 2 — by splitting at the
    first comma (matching the letterhead template). Honours explicit newlines
    if any are present, and stays on one line when there's no comma."""
    addr = (addr or '').strip()
    if not addr:
        return []
    if '\n' in addr:
        return [l.strip() for l in addr.split('\n') if l.strip()]
    i = addr.find(',')
    if i == -1:
        return [addr]
    line1 = addr[:i + 1].strip()   # keep the trailing comma on the street line
    line2 = addr[i + 1:].strip()
    return [line1, line2] if line2 else [line1]


def _page(canvas, doc, brand):
    canvas.saveState()
    # header band (full width) + brand mark bleeding into the top-right corner
    canvas.setFillColor(brand['band'])
    canvas.rect(0, PAGE_H - HEAD_H, PAGE_W, HEAD_H, stroke=0, fill=1)
    hdr = brand['header']
    if os.path.exists(hdr):
        iw, ih = ImageReader(hdr).getSize()
        hh = 46.5
        hw = hh * iw / ih
        canvas.drawImage(hdr, PAGE_W - hw, PAGE_H - hh + 1.5, width=hw, height=hh, mask='auto')
    # footer — grey corporate block
    canvas.setFillColor(FOOT_GREY)
    canvas.setFont(FONT, 8.5)
    tops = [PAGE_H - 784.9, PAGE_H - 794.7, PAGE_H - 804.4]  # baselines from bottom
    for x, lines in FOOTER_COLS:
        for i, ln in enumerate(lines):
            canvas.drawString(x, tops[i], ln)
    canvas.restoreState()


def build_custom_pdf(brand_id, v):
    brand = BRANDS.get(brand_id, BRANDS['wlth'])
    esc = PL.esc

    def g(key, default=''):
        val = v.get(key)
        val = val.strip() if isinstance(val, str) else val
        return val if val else default

    body = ParagraphStyle('b', fontName=FONT, fontSize=10.5, leading=13.9, textColor=INK)
    small = ParagraphStyle('s', parent=body, fontSize=10, leading=13.2)
    boldp = ParagraphStyle('bd', parent=small, fontName=BOLD)
    para = ParagraphStyle('p', parent=body, spaceAfter=9.5)
    sig = ParagraphStyle('sig', parent=small)

    frame = Frame(LM, 72, CONTENT_W, PAGE_H - HEAD_H - 22 - 72,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=(PAGE_W, PAGE_H))
    doc.addPageTemplates([PageTemplate(id='cl', frames=[frame],
                                       onPage=lambda c, d: _page(c, d, brand))])

    flow = []
    # Recipient block
    if g('recipientName'):
        flow.append(Paragraph(esc(g('recipientName')), small))
    for ln in _address_lines(g('recipientAddress')):
        flow.append(Paragraph(esc(ln), small))

    # Date
    flow.append(Spacer(1, 13))
    flow.append(Paragraph(esc(g('date')), boldp))

    # Salutation
    greeting = g('salutation') or g('recipientName')
    flow.append(Spacer(1, 30))
    flow.append(Paragraph(f'Dear {esc(greeting)},' if greeting else 'Dear,', small))
    flow.append(Spacer(1, 13))

    # Body — blank lines separate paragraphs; single newlines break within one.
    raw = g('body')
    blocks = [b for b in raw.replace('\r\n', '\n').split('\n\n')]
    for blk in blocks:
        text = '<br/>'.join(esc(l) for l in blk.split('\n') if l.strip() != '')
        if text:
            flow.append(Paragraph(text, para))

    # Sign-off + signature block
    flow.append(Spacer(1, 4))
    flow.append(Paragraph(esc(g('signOff', 'Sincerely,')), small))
    flow.append(Spacer(1, 48))
    line = Table([['']], colWidths=[300], rowHeights=[1], hAlign='LEFT')
    line.setStyle(TableStyle([('LINEABOVE', (0, 0), (-1, 0), 0.8, colors.black)]))
    flow.append(line)
    flow.append(Spacer(1, 4))
    name = esc(g('senderName', 'Firstname Lastname'))
    title = g('senderTitle')
    sig_html = f'<b>{name}</b>' + (f' – {esc(title)}' if title else '')
    flow.append(Paragraph(sig_html, sig))

    doc.build(flow)
    return buf.getvalue()


if __name__ == '__main__':
    import sys, json
    sys.stdout.buffer.write(build_custom_pdf(sys.argv[1], json.loads(sys.argv[2])))
