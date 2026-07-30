"""
Extract Formal Approval field values from an uploaded "Schedule 4" document.
Handles BOTH known Origin MMS layouts:
  A) "Schedule 4 - Application for approval"  (Company/Person Applicants, Ownership, ...)
  B) "WLTH – SMSF LOAN SUBMISSION / Loan Submission Summary"
     (Primary Borrower Name, Member N Guarantor Name, Loan Product, Account No., ...)

Maps onto the approval field ids in app/utils/letterTypes.ts so the generated
letter matches the WLTH / Mortgage Mart Formal Approval examples. Label matching
is colon- and case-tolerant; each field tries several label variants.
"""
import re
import zipfile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

BRAND_LABEL = {'wlth': 'WLTH', 'mma': 'Mortgage Mart'}
MONTHS = {'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
          'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'}


def docx_text(path):
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read('word/document.xml'))
    return '\n'.join(''.join(t.text or '' for t in p.iter(W + 't')) for p in root.iter(W + 'p'))


def _lines(path):
    if path.lower().endswith('.pdf'):
        import fitz
        d = fitz.open(path)
        txt = '\n'.join(pg.get_text('text') for pg in d)
    else:
        txt = docx_text(path)
    out = []
    for ln in txt.split('\n'):
        ln = re.sub('[-•▪●■]', ' ', ln)  # drop bullet/PUA glyphs
        s = ' '.join(ln.split())  # collapse internal whitespace
        if not s:
            continue
        if re.match(r'^Page \d+ of \d+$', s):
            continue
        if re.match(r'^APP-\s+\d', s):  # spaced watermark, not the real APP-###### value
            continue
        out.append(s)
    return out


def _norm(label):
    return label.rstrip(':').strip().lower()


def _after(lines, *labels):
    """Value on the line after the first line matching any of `labels`
    (colon- and case-insensitive). Returns '' if none match."""
    wanted = {_norm(l) for l in labels}
    for i in range(len(lines) - 1):
        if _norm(lines[i]) in wanted:
            return lines[i + 1].strip()
    return ''


def _all_after_re(lines, pattern):
    rx = re.compile(pattern, re.I)
    out = []
    for i in range(len(lines) - 1):
        if rx.match(_norm(lines[i])):
            out.append(lines[i + 1].strip())
    return out


def _fmt_date(s):
    s = s.strip()
    m = re.match(r'(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{4})', s)  # 20 Jul 2026
    if m:
        return f"{m.group(1).zfill(2)}/{MONTHS.get(m.group(2)[:3].lower(), '01')}/{m.group(3)}"
    m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{2,4})\b', s)  # dd/mm/yy or dd/mm/yyyy
    if m:
        y = m.group(3)
        y = '20' + y if len(y) == 2 else y
        return f"{m.group(1).zfill(2)}/{m.group(2).zfill(2)}/{y}"
    return s


def _applicant_entries(lines):
    """Format A: Company/Person Applicants blocks."""
    heads = [i for i, l in enumerate(lines) if l in ('Company Applicants', 'Person Applicants')]
    entries = []
    for k, i in enumerate(heads):
        end = heads[k + 1] if k + 1 < len(heads) else len(lines)
        block = lines[i:end]
        entries.append({
            'kind': block[0],
            'role': block[1] if len(block) > 1 else '',
            'name': block[2] if len(block) > 2 else '',
            'trust': _after(block, 'Trust Name'),
        })
    return entries


def _term_years(term):
    m = re.search(r'(\d+)\s*month', term, re.I)
    if m:
        return f'{round(int(m.group(1)) / 12)} Years'
    return term


def _special_conditions(lines, brand):
    start = None
    for i, l in enumerate(lines):
        if _norm(l) in ('special conditions', 'settlement conditions'):
            start = i + 1
            break
    if start is None:
        return ''
    end = len(lines)
    for i in range(start, len(lines)):
        n = _norm(lines[i])
        if n in ('special instructions to solicitor', 'special solicitor instructions') or n.startswith('approval ('):
            end = i
            break
    section = lines[start:end]

    conds = []
    if any(l in ('Condition unmet', 'Condition met') for l in section):
        # Format A: each condition ends at a Condition unmet/met marker
        cur = []
        for l in section:
            if l in ('Condition unmet', 'Condition met'):
                if cur:
                    conds.append(' '.join(cur))
                    cur = []
            else:
                cur.append(l)
        if cur:
            conds.append(' '.join(cur))
    else:
        # Format B: numbered "1." "2." conditions, possibly multi-line
        cur = []
        for l in section:
            if re.match(r'^\d+[.)]\s*', l):
                if cur:
                    conds.append(' '.join(cur))
                cur = [re.sub(r'^\d+[.)]\s*', '', l)]
            elif cur:
                cur.append(l)
            elif l.strip():
                cur = [l]
        if cur:
            conds.append(' '.join(cur))

    # Internal document-collection notes (bank statements / payslips) are not
    # customer-facing special conditions — the letters omit them.
    INTERNAL = ('bank statement', 'payslip', 'pay slip')
    label = BRAND_LABEL.get(brand, 'WLTH')
    cleaned = []
    for c in conds:
        c = re.sub(r'\s{2,}', ' ', c).strip()
        c = re.sub(r'\bOrigin\b', label, c)
        if c and not any(k in c.lower() for k in INTERNAL):
            cleaned.append(c)
    return '\n'.join(f'{i + 1}. {c}' for i, c in enumerate(cleaned))


def parse_schedule4(path, brand='wlth'):
    lines = _lines(path)
    out = {}

    def put(key, val):
        if isinstance(val, str):
            val = val.strip()
        if val:
            out[key] = val

    put('date', _fmt_date(_after(lines, 'Date of Approval', 'Disclosure Date')))
    # Panel solicitor is always WLTH's panel ("Green Mortgage Lawyers", the
    # renderer default) — not reliably in the S4, so don't scrape it.
    put('loanAccountNumber', _after(lines, 'Loan Account Number', 'Account No.', 'Application Ref No.'))
    put('loanAmount', _after(lines, 'Loan Amount', 'Total Loan Amount'))
    put('loanTerm', _term_years(_after(lines, 'Loan Term (Years)', 'Total Loan Term', 'Loan Term')))
    rate = _after(lines, 'Interest Rate')
    put('interestRate', rate)
    put('revertRate', rate)
    put('monthlyRepayment', _after(lines, 'Initial Repayment Amount', 'Repayment Amount'))
    put('productName', _after(lines, 'Loan Product'))  # marketing name (Format B only)

    itype = _after(lines, 'Interest Type', 'Interest Rate Type')
    put('rateType', 'Fixed' if 'fixed' in itype.lower() else 'Variable')
    rtype = _after(lines, 'Repayment Type')
    put('repaymentType', 'Interest Only' if 'interest only' in rtype.lower() else 'P&I')
    offset = _after(lines, 'Offset account', 'Offset Account Y/N')
    put('offsetAccount', 'No' if offset.lower().startswith('n') else 'Yes')
    put('redrawFacility', 'N/A')
    put('annualFacilityFee', '$395.00')
    put('monthlyFees', '$0.00')

    sec = _after(lines, 'Security Property', 'Security Address')
    put('securityProperty', re.sub(r',\s*Australia\s*$', '', sec))
    put('mortgagors', _after(lines, 'Security Ownership', 'Ownership'))

    # Borrower(s): Format B has the full "Company ATF Trust" in one field;
    # Format A builds it from the company applicant + its trust name.
    borrower = _after(lines, 'Primary Borrower Name')
    if not borrower:
        bs = []
        for e in _applicant_entries(lines):
            if e['role'] == 'Borrower' and e['name']:
                bs.append(f"{e['name']} ATF {e['trust']}" if e['trust'] else e['name'])
        borrower = ' & '.join(bs)
    put('borrowers', borrower)

    # Guarantor(s): Format B "Member N Guarantor Name", else Format A person applicants.
    gs = _all_after_re(lines, r'member\s+\d+\s+guarantor name')
    if not gs:
        gs = [e['name'] for e in _applicant_entries(lines)
              if e['role'] == 'Guarantor' and e['kind'] == 'Person Applicants' and e['name']]
    put('guarantors', ' & '.join(gs))

    put('borrowerEmail', _after(lines, 'Contact Email', 'Email'))
    put('specialConditions', _special_conditions(lines, brand))
    return out
