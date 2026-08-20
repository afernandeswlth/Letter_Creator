"""Credit Approval Memorandum — PDF renderer.

Built on the same letterhead as the Formal Approval / Pre-Approval letters
(engine/approval_letter.py): A4 page, grey header band + blue title + slanted WLTH
mark on page 1, blue (#2057be) section bars, grey (#eceff1) label columns, light
grid lines, and the shared navy "Yours Sincerely" footer band on the last page.

Sections size to their content and are kept together, so a section never splits
across a page break — the whole bar+body moves to the next page instead. Form
driven (field ids match app/utils/letterTypes.ts); meant to look like the filled
Word document (engine/docx_letter.py).
"""
import io
import json
import os
import re

import richtext
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, Image as RLImage,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

import pdf_letter as PL
from approval_letter import BRANDS, INK  # reuse the shared brand assets + ink colour

HERE = os.path.dirname(__file__)
PAGE_W, PAGE_H = 595.3, 842.0          # A4
LM = 48.2
RM = 43.8
CONTENT_W = PAGE_W - LM - RM           # ~503.3

TITLE_BLUE = colors.HexColor('#2557be')
BLUE = colors.HexColor('#2057be')      # section bars + headings
GREY_LABEL = colors.HexColor('#eceff1')
BAND = colors.HexColor('#f4f4f4')
GRIDC = colors.HexColor('#eceff1')
NAVY = colors.HexColor('#16224b')

# Carlito is metric-compatible with Calibri (the template's font).
FONT, BOLD = 'Carlito', 'Carlito-Bold'
_FDIR = os.path.join(HERE, 'assets', 'fonts')
try:
    pdfmetrics.registerFont(TTFont('Carlito', os.path.join(_FDIR, 'Carlito-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Carlito-Bold', os.path.join(_FDIR, 'Carlito-Bold.ttf')))
except Exception:  # noqa: BLE001
    FONT, BOLD = 'Helvetica', 'Helvetica-Bold'

CAM_TITLE = 'Credit Approval Memorandum (CAM)'


def _refinance_notes(raw):
    """Parse the refinance field (a JSON array of note strings) into a list.

    The form stores 1-5 refinances as a JSON array; older/plain values fall back
    to a single-item list. Always returns at least one (possibly empty) entry so
    the table shows a "Refinance 1" row.
    """
    items = []
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                items = [str(x).strip() for x in parsed]
            else:
                items = [str(parsed).strip()]
        except (ValueError, TypeError):
            items = [raw.strip()]
    return items or ['']


def _table_rows(raw, ncols, min_rows=1):
    """Parse a table field into a list of ncols-wide string rows.

    Accepts a JSON 2D array (list of rows), a JSON array of strings (each becomes
    the first column), or a plain string (legacy single value). Each row is padded
    or trimmed to ncols; always returns at least min_rows rows so the grid renders.
    """
    rows = []
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                for r in parsed:
                    cells = r if isinstance(r, list) else [r]
                    rows.append([('' if i >= len(cells) or cells[i] is None else str(cells[i]).strip())
                                 for i in range(ncols)])
            else:
                rows.append([str(parsed).strip()] + [''] * (ncols - 1))
        except (ValueError, TypeError):
            rows.append([str(raw).strip()] + [''] * (ncols - 1))
    while len(rows) < min_rows:
        rows.append([''] * ncols)
    return rows


def _header(cvs, brand):
    """Grey header band, blue title, slanted WLTH mark bleeding top-right (page 1)."""
    cvs.saveState()
    cvs.setFillColor(BAND)
    cvs.rect(0, PAGE_H - 47, PAGE_W, 47, stroke=0, fill=1)
    cvs.setFillColor(TITLE_BLUE)
    cvs.setFont(BOLD, 15)
    cvs.drawString(23, PAGE_H - 31.5, CAM_TITLE)
    hdr = brand.get('header')
    if hdr and os.path.exists(hdr):
        cvs.drawImage(hdr, PAGE_W - 82.2, PAGE_H - 47.2, width=82.2, height=46.5, mask='auto')
    cvs.restoreState()


def _footer(cvs, brand):
    """The shared Approval/Pre-Approval footer: navy band + sign-off + W mark."""
    cvs.saveState()
    cvs.setFillColor(brand.get('footer_band', NAVY))
    cvs.rect(LM, 31, CONTENT_W, 25, stroke=0, fill=1)
    cvs.setFillColor(colors.white)
    cvs.setFont(FONT, 9)
    cvs.drawString(LM + 8, 39.8, f"Yours Sincerely, {brand.get('team', 'The WLTH Team')}")
    fl = brand.get('footer_logo')
    if fl and os.path.exists(fl):
        iw, ih = ImageReader(fl).getSize()
        fh = 14.0
        fw = fh * iw / ih
        cvs.drawImage(fl, PAGE_W - RM - 8 - fw, 31 + (25 - fh) / 2, width=fw, height=fh, mask='auto')
    cvs.restoreState()


def _signature_image(data_url, max_w, max_h):
    if not data_url or 'base64,' not in data_url:
        return None
    try:
        import base64
        raw = base64.b64decode(data_url.split('base64,', 1)[1])
        iw, ih = ImageReader(io.BytesIO(raw)).getSize()
        s = min(max_w / iw, max_h / ih)
        return RLImage(io.BytesIO(raw), width=iw * s, height=ih * s)
    except Exception:  # noqa: BLE001
        return None


def build_cam_pdf(brand_id, v):
    brand = BRANDS.get(brand_id, BRANDS['wlth'])
    esc = PL.esc

    def g(key, default=''):
        val = v.get(key)
        val = val.strip() if isinstance(val, str) else val
        return val if val else default

    body = ParagraphStyle('b', fontName=FONT, fontSize=10, leading=12.5, textColor=INK)
    date_s = ParagraphStyle('d', parent=body)
    head = ParagraphStyle('h', parent=body, textColor=BLUE)          # blue section headings
    lbl = ParagraphStyle('l', parent=body, fontSize=9, leading=11)
    val = ParagraphStyle('v', parent=body, fontSize=9, leading=11)
    barp = ParagraphStyle('bar', parent=body, fontSize=9, leading=11, textColor=colors.white)

    def L(t):
        return Paragraph(esc(t) or '&nbsp;', lbl)

    def V(t):
        return Paragraph((esc(t) or '&nbsp;').replace('\n', '<br/>'), val)

    # Rich-text fields (edited in RichTextEditor) render with their formatting and
    # bullet/numbered lists; a plain value falls back to the ordinary cell.
    def RV(key):
        raw = g(key)
        if raw and richtext.looks_like_html(raw):
            return richtext.rich_flow(raw, val)
        return V(raw)

    def mtext(key):
        """Plain text of a (possibly rich) field, for measuring row heights."""
        raw = g(key)
        return re.sub(r'<[^>]+>', ' ', raw) if raw and richtext.looks_like_html(raw) else raw

    def B(t):
        return Paragraph(esc(t), barp)

    # Padding that reproduces the template's ~14pt single-line rows while letting
    # multi-line cells grow to fit their text.
    def style(bar_first=False, label_cols=(), extra=None):
        s = [
            ('GRID', (0, 0), (-1, -1), 0.5, GRIDC),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 1.7), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.7),
        ]
        if bar_first:
            s += [('SPAN', (0, 0), (-1, 0)), ('BACKGROUND', (0, 0), (-1, 0), BLUE),
                  ('TOPPADDING', (0, 0), (-1, 0), 1.4), ('BOTTOMPADDING', (0, 0), (-1, 0), 1.4)]
        r0 = 1 if bar_first else 0
        for c in label_cols:
            s.append(('BACKGROUND', (c, r0), (c, -1), GREY_LABEL))
        return TableStyle(s + (extra or []))

    def section(flowables):
        return KeepTogether(flowables)

    ov_cols = [100.0, CONTENT_W - 100.0]
    pd_cols = [84.5, 163.6, 77.3, CONTENT_W - 84.5 - 163.6 - 77.3]
    bg_cols = [98.4, CONTENT_W - 98.4]
    rf_cols = [98.4, CONTENT_W - 98.4]  # narrow "Refinance N" col, same as the Background label col
    li_cols = [156.0, 184.4, CONTENT_W - 156.0 - 184.4]
    half = CONTENT_W / 2.0
    GAP = 20

    flow = [Paragraph(esc(g('date') or '01/01/2025'), date_s), Spacer(1, 22)]

    # Applicant Overview
    ov = Table([[L('Borrower(s):'), V(g('borrowers'))],
                [L('Account number:'), V(g('exposureAccount'))],
                [L('Mortgage Manager:'), V(g('mortgageManager'))]], colWidths=ov_cols)
    ov.setStyle(style())
    flow += [section([Paragraph('Applicant Overview', head), Spacer(1, 9), ov]), Spacer(1, GAP)]

    # Product Details
    pd = Table([[B('Product Details'), '', '', ''],
                [L('Proposed Exposure'), V(g('exposureBalance')), L('Proposed Balence'), V(g('exposureBalance'))],
                [L('Interest Type'), V(g('exposureInterestType')), L('Loan Purpose'), V(g('exposureLoanPurpose'))],
                [L('Proposed Security'), V(g('proposedSecurity')), L('Proposed LVR'), V(g('proposedLvr'))]],
               colWidths=pd_cols)
    pd.setStyle(style(bar_first=True, label_cols=(0, 2)))
    flow += [section([pd]), Spacer(1, GAP)]

    # Background information
    bg_rows = [[B('Background information'), '']]
    _RICH_BG = {'personalInfo', 'employment', 'rentalIncome', 'security'}
    for name, fld in [('Personal Info', 'personalInfo'), ('Employment', 'employment'),
                      ('Rental Income', 'rentalIncome'), ('Security', 'security'),
                      ('LMI', 'lmi'), ('NDI', 'ndi')]:
        bg_rows.append([L(name), RV(fld) if fld in _RICH_BG else V(g(fld))])
    bg = Table(bg_rows, colWidths=bg_cols)
    bg.setStyle(style(bar_first=True, label_cols=(0,)))
    flow += [section([bg]), Spacer(1, GAP)]

    # Refinance History — one row per refinance (left "Refinance N", right notes).
    refis = _refinance_notes(g('refinanceNotes'))
    rf = Table([[L('Refinance %d' % (i + 1)), V(note)] for i, note in enumerate(refis)],
               colWidths=rf_cols)
    rf.setStyle(style(label_cols=(0,)))
    flow += [section([Paragraph('Refinance History', head), Spacer(1, 9), rf]), Spacer(1, GAP)]

    # Liabilities — header row + one row per liability (Type / Balance / Conduct).
    li_rows = [[L('Type of Loan'), L('Outstanding Balance / Limit'), L('Conduct')]]
    for r in _table_rows(g('liabilities'), 3, min_rows=1):
        li_rows.append([V(r[0]), V(r[1]), V(r[2])])
    li = Table(li_rows, colWidths=li_cols)
    li.setStyle(style(extra=[('BACKGROUND', (0, 0), (-1, 0), GREY_LABEL)]))
    flow += [section([Paragraph('Liabilities', head), Spacer(1, 9), li]), Spacer(1, GAP)]

    # Credit History (roomy min height for notes)
    ch = Table([[B('Credit History')], [RV('creditHistory')]],
               colWidths=[CONTENT_W], rowHeights=[None, _min_h(mtext('creditHistory'), val, CONTENT_W, 120)])
    ch.setStyle(style(bar_first=True))
    flow += [section([ch]), Spacer(1, GAP)]

    # Living Costs / Policy exceptions
    lc_h = _min_h(mtext('livingCost'), val, half, 90, mtext('policyExceptions'))
    lcp = Table([[B('Living Costs:'), B('Policy exceptions (including mitigants)')],
                 [RV('livingCost'), RV('policyExceptions')]],
                colWidths=[half, half], rowHeights=[None, lc_h])
    lcp.setStyle(style(bar_first=True))
    flow += [section([lcp]), Spacer(1, GAP)]

    # Final Assessment (auto height)
    fa = Table([[B('Final Assesment')], [RV('finalAssessment')]],
               colWidths=[CONTENT_W], rowHeights=[None, _min_h(mtext('finalAssessment'), val, CONTENT_W, 60)])
    fa.setStyle(style(bar_first=True))
    flow += [section([fa]), Spacer(1, GAP)]

    # Recommendation + sign-off (kept together; signature box sized to the drawing)
    sig = _signature_image(g('recommendedSignature'), max_w=half - 16, max_h=46)
    sig_h = (sig.drawHeight + 8) if sig is not None else 16
    rec = Table([
        [B('Recommendation / Approval (including conditions)'), ''],
        [V(g('recommendation')), ''],
        [L('Name:'), V(g('recommendedName'))],
        [L('Date:'), V(g('recommendedDate'))],
        [L('Signature:'), sig if sig is not None else V('')],
    ], colWidths=[half, half], rowHeights=[None, _min_h(g('recommendation'), val, CONTENT_W, 40), None, None, sig_h])
    rec.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, GRIDC), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 1.7), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.7),
        ('SPAN', (0, 0), (-1, 0)), ('SPAN', (0, 1), (-1, 1)),
        ('BACKGROUND', (0, 0), (-1, 0), BLUE),
        ('TOPPADDING', (0, 0), (-1, 0), 1.4), ('BOTTOMPADDING', (0, 0), (-1, 0), 1.4),
        ('BACKGROUND', (0, 2), (0, 4), GREY_LABEL),
    ]))
    flow += [section([rec])]

    # The header goes on page 1 only; the footer on the last page only.
    class _CamCanvas(canvas.Canvas):
        def __init__(self, *a, **k):
            canvas.Canvas.__init__(self, *a, **k)
            self._states = []

        def showPage(self):
            self._states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            n = len(self._states)
            for i, st in enumerate(self._states):
                self.__dict__.update(st)
                if i == 0:
                    _header(self, brand)
                if i == n - 1:
                    _footer(self, brand)
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)

    buf = io.BytesIO()
    # Content stops above the footer band on every page; page 1 leaves room for the
    # header band, later pages start higher.
    frame1 = Frame(LM, 62, CONTENT_W, PAGE_H - 62 - 62, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    frame2 = Frame(LM, 62, CONTENT_W, PAGE_H - 52.6 - 62, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(buf, pagesize=(PAGE_W, PAGE_H))
    from reportlab.platypus import NextPageTemplate
    doc.addPageTemplates([
        PageTemplate(id='first', frames=[frame1]),
        PageTemplate(id='later', frames=[frame2]),
    ])
    flow.insert(0, NextPageTemplate('later'))
    doc.build(flow, canvasmaker=_CamCanvas)
    return buf.getvalue()


def _min_h(text, style_, width, minimum, text2=''):
    """Row height = max(minimum, wrapped height of the (longer) text) + padding."""
    from reportlab.platypus import Paragraph as _P
    h = 0
    for t in (text, text2):
        if t:
            p = _P((t or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>'), style_)
            h = max(h, p.wrap(width - 10, 100000)[1])
    return max(minimum, h + 6)
