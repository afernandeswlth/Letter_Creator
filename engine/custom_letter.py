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
import re
from html import escape as _hesc
from html.parser import HTMLParser

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


# --- Rich-text body -------------------------------------------------------
# The Letter Body field is a small WYSIWYG editor (app/components/RichTextEditor.vue)
# that emits HTML using <b>/<i>/<u> and <font size color> tags. reportlab's
# Paragraph understands the same tag vocabulary, so we translate the editor HTML
# into paragraph markup rather than dropping the formatting.

# HTML <font size="1..7"> is a relative scale; map it to absolute points. 3 is
# the editor's "Normal" and matches the body font size.
_FONT_PT = {1: 7.5, 2: 9, 3: 10.5, 4: 12, 5: 15, 6: 20, 7: 27}
_BLOCK_TAGS = {'p', 'div', 'li', 'ul', 'ol', 'blockquote'}
_DEFAULT_PT = 10.5


def _parse_style(s):
    out = {}
    for part in (s or '').split(';'):
        if ':' in part:
            k, _, val = part.partition(':')
            out[k.strip().lower()] = val.strip().lower()
    return out


def _clean_color(c):
    """Return a reportlab-safe colour: #rrggbb, rgb(...) → hex, or a plain name."""
    c = (c or '').strip()
    m = re.match(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', c)
    if m:
        return '#%02x%02x%02x' % (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    if re.match(r'^#[0-9a-fA-F]{3,8}$', c):
        return c[:7]
    if re.match(r'^[a-zA-Z]+$', c):
        return c
    return '#111827'


def _pt_from_style(style):
    sz = style.get('font-size', '')
    try:
        if sz.endswith('px'):
            return round(float(sz[:-2]) * 0.75, 1)
        if sz.endswith('pt'):
            return float(sz[:-2])
    except ValueError:
        pass
    return None


class _RichTextParser(HTMLParser):
    """Convert editor HTML into a list of (line_markup, max_font_pt) tuples.
    A <br> or block element ends the current line; an empty line marks a
    paragraph break."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lines = []
        self._cur = []
        self._stack = []      # per open element: list of closing tags to emit
        self._line_pt = _DEFAULT_PT

    def _flush(self):
        self.lines.append((''.join(self._cur), self._line_pt))
        self._cur = []
        self._line_pt = _DEFAULT_PT

    def handle_starttag(self, tag, attrs):
        if tag == 'br':
            self._flush()
            return
        a = {k.lower(): (val or '') for k, val in attrs}
        style = _parse_style(a.get('style', ''))
        opens, closes = [], []

        weight = style.get('font-weight', '')
        if tag in ('b', 'strong') or weight in ('bold', 'bolder') or weight[:3] in ('600', '700', '800', '900'):
            opens.append('<b>'); closes.append('</b>')
        if tag in ('i', 'em') or style.get('font-style') == 'italic':
            opens.append('<i>'); closes.append('</i>')
        if tag == 'u' or 'underline' in style.get('text-decoration', ''):
            opens.append('<u>'); closes.append('</u>')

        color = a.get('color') if tag == 'font' else None
        color = style.get('color') or color
        pt = None
        if tag == 'font' and a.get('size', '').isdigit():
            pt = _FONT_PT.get(int(a['size']))
        pt = _pt_from_style(style) or pt

        font_attr = ''
        if color:
            font_attr += ' color="%s"' % _clean_color(color)
        if pt:
            font_attr += ' size="%s"' % pt
            self._line_pt = max(self._line_pt, pt)
        if font_attr:
            opens.append('<font%s>' % font_attr); closes.append('</font>')

        if tag in _BLOCK_TAGS and self._cur:
            self._flush()
        self._cur.extend(opens)
        self._stack.append(closes)

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self._flush()
        else:
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == 'br':
            return
        closes = self._stack.pop() if self._stack else []
        for c in reversed(closes):
            self._cur.append(c)
        if tag in _BLOCK_TAGS:
            self._flush()

    def handle_data(self, data):
        self._cur.append(_hesc(data, quote=False))

    def result(self):
        if self._cur:
            self._flush()
        return self.lines


def _looks_like_html(s):
    return bool(re.search(r'<(b|i|u|br|div|p|font|span|strong|em|ul|ol|li)\b', s or '', re.I))


def _rich_body_flow(raw, para_style):
    """Turn editor HTML into a list of Paragraph flowables, grouping lines into
    paragraphs (blank line = new paragraph) and widening the leading when a
    paragraph uses a larger font so big text doesn't clip."""
    parser = _RichTextParser()
    parser.feed(raw.replace('\r\n', '\n'))
    lines = parser.result()

    blocks, cur, cur_pt = [], [], _DEFAULT_PT
    for markup, pt in lines:
        plain = re.sub(r'<[^>]+>', '', markup).replace('\xa0', ' ').strip()
        if plain == '':
            if cur:
                blocks.append((cur, cur_pt)); cur, cur_pt = [], _DEFAULT_PT
        else:
            cur.append(markup); cur_pt = max(cur_pt, pt)
    if cur:
        blocks.append((cur, cur_pt))

    flow = []
    base_lead = para_style.leading
    for markup_lines, pt in blocks:
        style = para_style
        if pt > _DEFAULT_PT:
            style = ParagraphStyle('rt%.0f' % pt, parent=para_style,
                                   leading=max(base_lead, pt * 1.32))
        flow.append(Paragraph('<br/>'.join(markup_lines), style))
    return flow


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

    # Body — the WYSIWYG editor sends HTML (bold/italic/underline/size/colour),
    # which we translate to reportlab markup. Plain-text bodies (or other
    # callers) fall back to the newline-based paragraph split.
    raw = g('body')
    if _looks_like_html(raw):
        flow.extend(_rich_body_flow(raw, para))
    else:
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
