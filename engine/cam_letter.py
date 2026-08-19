"""
Credit Approval Memorandum (CAM) — rendered to match the WLTH Word template:
"WLTH" wordmark + W mark header, a single 4-column table with a centred grey
title, grey (#F2F2F2) section-header rows in black bold, white bold labels, grey
empty spacer rows between every section, 10pt Calibri-substitute (Helvetica),
and the template's column widths.
"""
import io
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Table, TableStyle, Paragraph, Spacer,
    Image as RLImage,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE = os.path.dirname(__file__)
PAGE_W, PAGE_H = A4
LM = 48        # measured content left edge in the reference
RM = 43.4      # measured content right edge (551.8 from left)
TOP = 84       # table top (y=84 from the top edge, below the WLTH header)
BOT = 36
CONTENT_W = PAGE_W - LM - RM

LABEL_SZ = 10   # labels / section headers / title (Calibri-Bold)
VALUE_SZ = 11   # field values (Calibri)

# The template is set in Calibri. Carlito is a free, metric-compatible twin, so
# embedding it makes the PDF match the Word doc's typeface exactly.
_FONT_DIR = os.path.join(HERE, 'assets', 'fonts')
try:
    pdfmetrics.registerFont(TTFont('Carlito', os.path.join(_FONT_DIR, 'Carlito-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Carlito-Bold', os.path.join(_FONT_DIR, 'Carlito-Bold.ttf')))
    FONT, BOLD = 'Carlito', 'Carlito-Bold'
except Exception:  # noqa: BLE001
    FONT, BOLD = 'Helvetica', 'Helvetica-Bold'
F2 = colors.HexColor('#F2F2F2')      # section headers + most spacers
D9 = colors.HexColor('#D9D9D9')      # the one darker spacer (row 4)
GRIDC = colors.black                 # table borders are black in the reference
INK = colors.black
LOGO = os.path.join(HERE, 'assets', 'cam-logo.png')

_RAW_COLS = [1979, 1977, 2543, 3566]
SPACER_H = 13.5
MIN_ROW = 14.0        # Word's minimum row height for a single-line value cell
BULLET_SZ = 10        # bulleted "List Paragraph" cells render at 10pt, not 11pt
BULLET_TRAIL = 12.7   # trailing empty List Paragraph Word renders after bullet cells
GRID3_TOP = 12.0      # blank line Word renders above the Liabilities nested table
_BULLET_TRAIL_FIELDS = {'employment', 'creditHistory'}  # bullet cells that keep a trailing blank  # measured height of the empty separator rows
BULLET = '▪'  # small square bullet (matches the template's Wingdings bullet)

# (label, field, kind) — kind: 'bullet' first line, 'grid2'/'grid3' empty sub-table.
_BACKGROUND = [
    ('Personal Info', 'personalInfo', None),
    ('Employment', 'employment', 'bullet'),
    ('Rental Income', 'rentalIncome', None),
    ('Security', 'security', 'bullet'),
    ('LMI', 'lmi', None),
    ('Refinance History', 'refinanceHistory', 'grid2'),
    ('Liabilities', 'liabilities', 'grid3'),
    ('Credit history', 'creditHistory', 'bullet'),
    ('NDI', 'ndi', None),
]


def _esc(text):
    return (str(text) if text is not None else '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _p(text, bold=False, size=LABEL_SZ, align='left'):
    # Word gives each value cell a little space after the paragraph, which makes
    # single-line value rows ~16.5pt tall; mirror that so rows line up.
    st = ParagraphStyle('c', fontName=BOLD if bold else FONT, fontSize=size,
                        leading=size + 2.4, textColor=INK,
                        spaceAfter=3 if size >= VALUE_SZ else 0,
                        alignment=TA_CENTER if align == 'center' else 0)
    return Paragraph(_esc(text).replace('\n', '<br/>'), st)


def _bullet_p(text):
    # The bulleted cells (Employment, Security, Credit history) use Word's "List
    # Paragraph" style: 10pt text with a hanging indent — a square bullet at the
    # cell's left edge and every text line aligned ~18pt in.
    st = ParagraphStyle('cb', fontName=FONT, fontSize=BULLET_SZ, leading=BULLET_SZ + 2.2,
                        textColor=INK, leftIndent=18, firstLineIndent=0,
                        bulletIndent=0, bulletFontName=FONT, bulletFontSize=BULLET_SZ)
    return Paragraph(_esc(text).replace('\n', '<br/>'), st, bulletText=BULLET)


def _signature_image(data_url, max_w, max_h):
    """Decode a base64 PNG data URL into a reportlab Image scaled to fit."""
    if not data_url or 'base64,' not in data_url:
        return None
    try:
        import base64
        raw = base64.b64decode(data_url.split('base64,', 1)[1])
        iw, ih = ImageReader(io.BytesIO(raw)).getSize()
        scale = min(max_w / iw, max_h / ih)
        return RLImage(io.BytesIO(raw), width=iw * scale, height=ih * scale)
    except Exception:
        return None


def _numbered_p(text):
    # Final Assessment is numbered list item "1." in the template: the number
    # hangs at the margin and every text line (intro + sub-points) aligns in.
    st = ParagraphStyle('cnum', fontName=FONT, fontSize=VALUE_SZ, leading=VALUE_SZ + 2.4,
                        textColor=INK, leftIndent=22, firstLineIndent=0,
                        bulletIndent=4, bulletFontName=FONT, bulletFontSize=VALUE_SZ)
    return Paragraph(_esc(text).replace('\n', '<br/>'), st, bulletText='1.')


def _page(canvas, doc):
    # The WLTH logo + wordmark header only appears on the first page.
    if canvas.getPageNumber() != 1:
        return
    if os.path.exists(LOGO):
        iw, ih = ImageReader(LOGO).getSize()
        hh = 58.4
        hw = hh * iw / ih
        canvas.drawImage(LOGO, 547.1 - hw, PAGE_H - 78.2, width=hw, height=hh, mask='auto')
    canvas.setFont(FONT, 20)
    canvas.setFillColor(INK)
    canvas.drawCentredString((LM + (PAGE_W - RM)) / 2.0, PAGE_H - 72, 'WLTH')


def build_cam_pdf(brand_id, v):
    def g(key, default=''):
        x = v.get(key)
        x = x.strip() if isinstance(x, str) else x
        return x if x else default

    total = sum(_RAW_COLS)
    col = [x / total * CONTENT_W for x in _RAW_COLS]
    value_w = col[1] + col[2] + col[3]

    def _grid(cols_w, data_rows):
        inner = Table(data_rows, colWidths=cols_w, rowHeights=[None] + [12.7] * (len(data_rows) - 1))
        inner.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, GRIDC), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 1), ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        return inner

    def value_cell(field, kind):
        val = g(field)
        if kind == 'bullet':
            return _bullet_p(val)
        # Nested tables must fit inside the value cell's padding (5.5 + 5), or they
        # overflow past the table's right border.
        avail = value_w - 10.5
        if kind == 'grid2' and not val:
            # Template nested table: 2 cols x 2 rows, widths 1733550:3257550 EMU.
            w0 = avail * 1733550 / (1733550 + 3257550)
            return _grid([w0, avail - w0], [['', ''], ['', '']])
        if kind == 'grid3' and not val:
            # Template nested table: 3 cols x 3 rows (header + 2 blank), EMU widths below.
            # Word renders a blank line above this table, so lead with a Spacer.
            ws = [1527175, 1710055, 1570990]
            cw = [avail * x / sum(ws) for x in ws]
            head = [_p('Type of Loan', bold=True, size=9), _p('Outstanding Balance/Limit', bold=True, size=9), _p('Conduct', bold=True, size=9)]
            return [Spacer(1, GRID3_TOP), _grid(cw, [head, ['', '', ''], ['', '', '']])]
        return _p(val, size=VALUE_SZ)

    rows, styles, heights = [], [], []
    label_vrows = []   # rows whose label|value divider is drawn (top section only)
    exposure_vrows = []  # rows whose 4-column internal dividers are drawn
    r = 0

    def push(cells, h=None):
        nonlocal r
        rows.append(cells)
        heights.append(h)
        r += 1

    def span_full():
        styles.append(('SPAN', (0, r), (3, r)))

    def span_value():
        styles.append(('SPAN', (1, r), (3, r)))

    def shade(color, c0=0, c1=3):
        styles.append(('BACKGROUND', (c0, r), (c1, r), color))

    def spacer(color):
        shade(color); span_full(); push(['', '', '', ''], SPACER_H)

    # Word gives every value cell a minimum row height of ~16.5pt (single-line
    # rows) and grows with content; reportlab only auto-sizes to the text, so we
    # measure each value flowable and enforce that same minimum.
    def _mh(flowable, width):
        try:
            items = flowable if isinstance(flowable, list) else [flowable]
            h = sum(f.wrap(width, 100000)[1] for f in items)
            return max(h + 1.0, MIN_ROW)
        except Exception:
            return MIN_ROW

    def value_row(label, field, default='', kind=None, vline=False):
        """label | value spanning cols 1-3, with a Word-matching min height.

        vline=True keeps the vertical divider between label and value (only the
        top section has it; the whole background section leaves it white).
        """
        val = value_cell(field, kind) if kind else _p(g(field, default), size=VALUE_SZ)
        if vline:
            label_vrows.append(r)
        h = _mh(val, value_w)
        # Employment and Credit history carry a trailing empty "List Paragraph" that
        # Word renders as one extra line; Security's content fills its cell, so it
        # gets none (matches the Word doc).
        if kind == 'bullet' and field in _BULLET_TRAIL_FIELDS:
            h += BULLET_TRAIL
        span_value(); push([_p(label, bold=True), val, '', ''], h)

    def full_value(field='', text=None, default=''):
        """Value spanning all 4 cols, with a Word-matching min height."""
        val = _p(text if text is not None else g(field, default), size=VALUE_SZ)
        span_full(); push([val, '', '', ''], _mh(val, CONTENT_W))

    # Title + Date (grey, full width)
    shade(F2); span_full(); push([_p('Credit Approval Memorandum (CAM)', bold=True, align='center'), '', '', ''])
    shade(F2); span_full(); push([_p(f"Date : {g('date')}", bold=True), '', '', ''])
    # Borrowers / Mortgage Manager (top section keeps the label|value divider)
    value_row('Borrowers', 'borrowers', vline=True)
    value_row('Mortgage Manager', 'mortgageManager', vline=True)
    spacer(D9)
    # Proposed Exposure (4-column sub-grid keeps its internal dividers)
    span_full(); push([_p('Proposed Exposure', bold=True), '', '', ''])
    exposure_vrows.append(r)
    push([_p('Account number', bold=True), _p('Proposed balance', bold=True), _p('Interest Type', bold=True), _p('Loan Purpose', bold=True)])
    ev = [_p(g('exposureAccount'), size=VALUE_SZ), _p(g('exposureBalance'), size=VALUE_SZ), _p(g('exposureInterestType'), size=VALUE_SZ), _p(g('exposureLoanPurpose'), size=VALUE_SZ)]
    exposure_vrows.append(r)
    push(ev, max(_mh(ev[i], col[i]) for i in range(4)))
    # Proposed security
    shade(F2); span_full(); push([_p('Proposed security', bold=True), '', '', ''])
    full_value('proposedSecurity', default='TBA')
    spacer(F2)
    value_row('Proposed  LVR', 'proposedLvr', vline=True)
    # Background information. Every row from here through the last background
    # spacer has no horizontal borders in the template (only grey shading marks
    # the spacers), so we suppress the horizontal lines across this whole band.
    shade(F2); span_full(); push([_p('Background information', bold=True), '', '', ''])
    bg_white_start = r
    full_value('backgroundInformation')
    for label, field, kind in _BACKGROUND:
        value_row(label, field, kind=kind)
        spacer(F2)
    bg_white_end = r - 1
    # NDI is the last background item above; then Living cost — a bold "Living
    # cost" label followed by the value at the template's 93.5pt tab stop.
    lc = g('livingCost')
    if lc:
        lc_inner = Table(
            [[_p('Living cost', bold=True, size=VALUE_SZ), _p(lc, bold=True, size=VALUE_SZ)]],
            colWidths=[93.5, CONTENT_W - 10.5 - 93.5])
        lc_inner.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        span_full(); push([lc_inner, '', '', ''], _mh(lc_inner, CONTENT_W))
    else:
        span_full(); push([_p('Living cost', bold=True, size=VALUE_SZ), '', '', ''])
    # Policy exceptions
    shade(F2); span_full(); push([_p('Policy exceptions (including mitigants)', bold=True), '', '', ''])
    full_value('policyExceptions')
    # Final Assessment — a numbered "1." list item (intro line + sub-points).
    shade(F2); span_full(); push([_p('Final Assessment', bold=True), '', '', ''])
    fa = g('finalAssessment')
    if fa:
        fap = _numbered_p(fa)
        span_full(); push([fap, '', '', ''], _mh(fap, CONTENT_W))
    else:
        full_value('finalAssessment')
    # Recommendation
    shade(F2); span_full(); push([_p('Recommendation / Approval (including conditions)', bold=True), '', '', ''])
    full_value('recommendation', default='Recommended for Conditional Approval:')
    # Sign-off block: two columns so Name/Signature line up under each other.
    # If the assessor drew a signature, place it inline after "Signature:".
    half = CONTENT_W / 2.0
    sig_img = _signature_image(g('recommendedSignature'), max_w=half - 62, max_h=26)
    if sig_img is not None:
        sig_cell = Table([[_p('Signature:', size=VALUE_SZ), sig_img]], colWidths=[58, half - 58])
        sig_cell.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
    else:
        sig_cell = _p('Signature: ______________________', size=VALUE_SZ)
    signoff = Table(
        [[_p('Recommended for Conditional Approval:', size=VALUE_SZ), _p('Name:', size=VALUE_SZ)],
         [_p(f"Date: {g('recommendedDate')}", size=VALUE_SZ), sig_cell]],
        colWidths=[half, half])
    signoff.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (0, 0), 1), ('TOPPADDING', (0, 1), (-1, 1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    span_full(); push([signoff, '', '', ''], _mh(signoff, CONTENT_W))

    # The outer box is drawn all round. Horizontal lines run under every row
    # EXCEPT the background band (Background info value → last background spacer),
    # which the template leaves border-free — only the grey shading marks it.
    # Vertical dividers are added only where the template shows them: the top
    # label|value rows and the 4-column exposure sub-grid. The whole background
    # section also keeps a white label|value gap.
    line_styles = [
        ('BOX', (0, 0), (-1, -1), 0.5, GRIDC),
        ('LINEBELOW', (0, 0), (-1, bg_white_start - 1), 0.5, GRIDC),
        ('LINEBELOW', (0, bg_white_end + 1), (-1, -1), 0.5, GRIDC),
    ]
    for rr in label_vrows:
        line_styles.append(('LINEAFTER', (0, rr), (0, rr), 0.5, GRIDC))
    for rr in exposure_vrows:
        line_styles.append(('LINEAFTER', (0, rr), (2, rr), 0.5, GRIDC))

    table = Table(rows, colWidths=col, rowHeights=heights)
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5.5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 0.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5),
    ] + line_styles + styles))

    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=A4)
    frame = Frame(LM, BOT, CONTENT_W, PAGE_H - TOP - BOT, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id='cam', frames=[frame], onPage=_page)])
    doc.build([table])
    return buf.getvalue()


if __name__ == '__main__':
    import sys, json
    sys.stdout.buffer.write(build_cam_pdf(sys.argv[1], json.loads(sys.argv[2])))
