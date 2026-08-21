"""Shared rich-text (editor HTML) rendering for the letter engine.

The editor (app/components/RichTextEditor.vue) emits HTML using <b>/<i>/<u>,
<font size/color> and <ul>/<ol>/<li>. This module parses that into a neutral
block/run structure (`parse_blocks`) that both renderers use:

  • the PDF renderer here (`rich_flow` → reportlab flowables, with bullets), and
  • the Word renderer in docx_letter.py (formatted runs + list prefixes).

Keeping one parser means bold/italic/underline/colour/size and bullet/numbered
lists come out the same in the PDF and the .docx.
"""
import re
from html import escape as _hesc
from html.parser import HTMLParser

# HTML <font size="1..7"> is a relative scale; map it to absolute points.
_FONT_PT = {1: 8, 2: 9, 3: 10, 4: 11, 5: 12, 6: 14, 7: 18}
_BLOCK_TAGS = {'p', 'div'}
# Some editors offer heading styles (formatBlock h2/h3/…) instead of a font-size
# control; render those as bold, sized text.
_HEADING_PT = {'h1': 18, 'h2': 15, 'h3': 12.5, 'h4': 11, 'h5': 10, 'h6': 10}


def looks_like_html(s):
    return bool(re.search(r'<(b|i|u|br|div|p|font|span|strong|em|ul|ol|li|h[1-6])\b', s or '', re.I))


def _parse_style(s):
    out = {}
    for part in (s or '').split(';'):
        if ':' in part:
            k, _, val = part.partition(':')
            out[k.strip().lower()] = val.strip().lower()
    return out


def _clean_color(c):
    """Return a #rrggbb colour from #hex / rgb(...) / a plain name, else a default."""
    c = (c or '').strip()
    m = re.match(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', c)
    if m:
        return '#%02x%02x%02x' % (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    if re.match(r'^#[0-9a-fA-F]{6,8}$', c):
        return c[:7]
    if re.match(r'^#[0-9a-fA-F]{3}$', c):
        return '#' + ''.join(ch * 2 for ch in c[1:])
    _NAMES = {'black': '#111827', 'red': '#dc2626', 'green': '#059669',
              'blue': '#1e63e9', 'amber': '#d97706', 'purple': '#7c3aed', 'white': '#ffffff'}
    return _NAMES.get(c.lower(), '#111827')


def _roman(n):
    out, vals = '', [(1000, 'm'), (900, 'cm'), (500, 'd'), (400, 'cd'), (100, 'c'),
                     (90, 'xc'), (50, 'l'), (40, 'xl'), (10, 'x'), (9, 'ix'),
                     (5, 'v'), (4, 'iv'), (1, 'i')]
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out or 'i'


def _alpha(n):
    s = ''
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(97 + r) + s
    return s or 'a'


def list_marker(kind, number, depth):
    """The marker for a list item. Bullets nest disc → circle → square and
    ordered lists nest decimal → lower-alpha → lower-roman (1. / a. / i.),
    matching the editor's list CSS so the PDF mirrors what was typed."""
    if kind == 'ul':
        if depth <= 1:
            return '•'      # disc
        if depth == 2:
            return '◦'      # circle (white bullet)
        return '▪'          # square (black small square)
    if depth <= 1:
        return '%d.' % number
    if depth == 2:
        return '%s.' % _alpha(number)
    return '%s.' % _roman(number)


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


class _Parser(HTMLParser):
    """Parse editor HTML into a list of blocks. Each block is:
        {'bullet': None|'ul'|'ol', 'number': int, 'indent': int,
         'lines': [[run, ...], ...]}   # lines split on <br>; run has text + flags
    A run is {'text', 'b', 'i', 'u', 'color', 'pt'}.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self._lines = []
        self._line = []
        self._b = self._i = self._u = 0
        self._colors = []
        self._pts = []
        self._lists = []       # {'ordered': bool, 'count': int}
        self._bullet = None    # (kind, number, indent) while inside an <li>
        self._quote = 0        # <blockquote> nesting depth = Tab-indent level
        self._elstack = []

    def _run_fmt(self):
        return {'b': self._b > 0, 'i': self._i > 0, 'u': self._u > 0,
                'color': self._colors[-1] if self._colors else None,
                'pt': self._pts[-1] if self._pts else None}

    def _newline(self):
        self._lines.append(self._line)
        self._line = []

    def _flush(self):
        if self._line:
            self._newline()
        has_text = any(any(r['text'].strip() for r in ln) for ln in self._lines)
        # Keep a list item even when it's empty — the browser shows it and numbers
        # it, so dropping it here made the PDF numbering jump (2 → 7). Empty content
        # outside a list is a paragraph gap.
        if has_text or self._bullet is not None:
            self.blocks.append({
                'bullet': self._bullet[0] if self._bullet else None,
                'number': self._bullet[1] if self._bullet else 0,
                'indent': self._bullet[2] if self._bullet else self._quote,
                'lines': self._lines or [[]],
            })
        elif self._lines:
            self.blocks.append({'bullet': None, 'number': 0, 'indent': self._quote, 'lines': [[]]})
        self._lines = []
        self._line = []

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or '') for k, v in attrs}
        style = _parse_style(a.get('style', ''))
        undo = {'b': 0, 'i': 0, 'u': 0, 'color': 0, 'pt': 0}
        if tag == 'br':
            self._newline()
            # <br> is void — no matching end tag — so it must NOT push onto the
            # undo stack, or a later </b>/</i> pops this instead of its own entry
            # and the formatting leaks forward.
            return
        if tag in ('ul', 'ol'):
            self._flush()
            # A nested list closes its parent item's own line, so the parent <li>
            # doesn't also emit an empty numbered row when it ends.
            self._bullet = None
            start = 0
            if tag == 'ol':
                try:
                    start = max(0, int(a.get('start', '1')) - 1)  # honour <ol start="N">
                except ValueError:
                    start = 0
            self._lists.append({'ordered': tag == 'ol', 'count': start})
            self._elstack.append(undo)
            return
        if tag == 'blockquote':
            self._flush()
            self._quote += 1
            self._elstack.append(undo)
            return
        if tag == 'li':
            self._flush()
            if self._lists:
                self._lists[-1]['count'] += 1
                lst = self._lists[-1]
                self._bullet = ('ol' if lst['ordered'] else 'ul', lst['count'], len(self._lists))
            else:
                self._bullet = ('ul', 1, 1)
            self._elstack.append(undo)
            return
        weight = style.get('font-weight', '')
        if tag in _HEADING_PT:
            self._b += 1
            undo['b'] += 1
            self._pts.append(_HEADING_PT[tag])
            undo['pt'] += 1
        if tag in ('b', 'strong') or weight in ('bold', 'bolder') or weight[:3] in ('600', '700', '800', '900'):
            self._b += 1
            undo['b'] += 1
        if tag in ('i', 'em') or style.get('font-style') == 'italic':
            self._i += 1
            undo['i'] += 1
        if tag == 'u' or 'underline' in style.get('text-decoration', ''):
            self._u += 1
            undo['u'] += 1
        color = a.get('color') if tag == 'font' else None
        color = style.get('color') or color
        if color:
            self._colors.append(_clean_color(color))
            undo['color'] += 1
        pt = None
        if tag == 'font' and a.get('size', '').isdigit():
            pt = _FONT_PT.get(int(a['size']))
        pt = _pt_from_style(style) or pt
        if pt:
            self._pts.append(pt)
            undo['pt'] += 1
        if tag in _BLOCK_TAGS or tag in _HEADING_PT:
            self._flush()
        self._elstack.append(undo)

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self._newline()
        else:
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == 'br':
            return
        undo = self._elstack.pop() if self._elstack else {'b': 0, 'i': 0, 'u': 0, 'color': 0, 'pt': 0}
        self._b -= undo['b']
        self._i -= undo['i']
        self._u -= undo['u']
        for _ in range(undo['color']):
            if self._colors:
                self._colors.pop()
        for _ in range(undo['pt']):
            if self._pts:
                self._pts.pop()
        if tag in ('ul', 'ol'):
            if self._lists:
                self._lists.pop()
            return
        if tag == 'li':
            self._flush()
            self._bullet = None
            return
        if tag == 'blockquote':
            self._flush()
            if self._quote > 0:
                self._quote -= 1
            return
        if tag in _BLOCK_TAGS or tag in _HEADING_PT:
            self._flush()

    def handle_data(self, data):
        if data:
            fmt = self._run_fmt()
            fmt['text'] = data
            self._line.append(fmt)

    def result(self):
        self._flush()
        return self.blocks


def parse_blocks(raw):
    """Parse editor HTML into the neutral block/run structure (see _Parser)."""
    p = _Parser()
    p.feed((raw or '').replace('\r\n', '\n'))
    return p.result()


def _line_markup(runs):
    out = []
    for r in runs:
        t = _hesc(r['text'], quote=False).replace('\xa0', ' ')
        if not t:
            continue
        opens, closes = '', ''
        fa = ''
        if r.get('color'):
            fa += ' color="%s"' % r['color']
        if r.get('pt'):
            fa += ' size="%s"' % r['pt']
        if fa:
            opens += '<font%s>' % fa
            closes = '</font>' + closes
        if r['b']:
            opens += '<b>'
            closes = '</b>' + closes
        if r['i']:
            opens += '<i>'
            closes = '</i>' + closes
        if r['u']:
            opens += '<u>'
            closes = '</u>' + closes
        out.append(opens + t + closes)
    return ''.join(out)


def rich_flow(raw, para_style):
    """Render editor HTML to a list of reportlab flowables using para_style as the
    base. Bullet/numbered <li> items become indented Paragraphs with a bullet; the
    rest becomes ordinary Paragraphs (blank lines preserved). Leading grows with
    the largest font on a paragraph so big text doesn't clip the following line."""
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph

    base_pt = para_style.fontSize or 9
    base_lead = para_style.leading or (base_pt * 1.2)

    def line_pt(runs):
        pts = [r['pt'] for r in runs if r.get('pt')]
        return max(pts) if pts else base_pt

    def mk_style(max_pt, **kw):
        lead = max(base_lead, max_pt * 1.3) if max_pt > base_pt else base_lead
        return ParagraphStyle('rt', parent=para_style, leading=lead, **kw)

    blocks = parse_blocks(raw)
    flow = []
    pending = []  # (markup, max_pt)

    def flush_pending():
        if pending:
            mp = max(pt for _, pt in pending)
            flow.append(Paragraph('<br/>'.join(m for m, _ in pending), mk_style(mp)))
            del pending[:]

    for blk in blocks:
        if blk['bullet']:
            flush_pending()
            text = '<br/>'.join(_line_markup(ln) for ln in blk['lines']) or '&nbsp;'
            mp = max((line_pt(ln) for ln in blk['lines']), default=base_pt)
            depth = max(1, blk['indent'])
            indent = 14 * (depth - 1)
            li_style = mk_style(mp, leftIndent=indent + 14, bulletIndent=indent,
                                spaceBefore=1, spaceAfter=1,
                                # Draw the bullet in the body font, not reportlab's
                                # default Helvetica — Helvetica lacks the circle/square
                                # glyphs used for nested levels and boxes them.
                                bulletFontName=para_style.fontName)
            bt = list_marker(blk['bullet'], blk['number'], depth)
            flow.append(Paragraph(text, li_style, bulletText=bt))
        elif blk['indent']:
            flush_pending()
            text = '<br/>'.join(_line_markup(ln) for ln in blk['lines']) or '&nbsp;'
            mp = max((line_pt(ln) for ln in blk['lines']), default=base_pt)
            # The editor's Tab indent wraps each level in a <blockquote> with
            # margin-left:40px (~24pt); mirror that so the PDF steps in the same
            # way, with a little breathing room above/below like the editor.
            para = mk_style(mp, leftIndent=24 * blk['indent'], spaceBefore=2, spaceAfter=2)
            flow.append(Paragraph(text, para))
        else:
            for ln in blk['lines']:
                pending.append((_line_markup(ln), line_pt(ln)))
    flush_pending()
    if not flow:
        flow = [Paragraph('&nbsp;', para_style)]
    return flow
