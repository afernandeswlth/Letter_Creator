"""
Extract Formal Approval field values from an uploaded "Schedule 4" document
(Origin MMS "Schedule 4 - Application for approval"). Maps the S4 to the
approval field ids in app/utils/letterTypes.ts so the generated letter matches
the WLTH / Mortgage Mart Formal Approval example.

Mapping (S4 label -> approval field):
  Date of Approval          -> date            (reformatted dd/mm/yyyy)
  Borrower company + trust   -> borrowers       ("Company ATF TrustName")
  Security "Ownership"       -> mortgagors
  Person guarantors          -> guarantors      (joined with " and ")
  Loan Account Number        -> loanAccountNumber
  Loan Amount                -> loanAmount
  Loan Term (Years)          -> loanTerm
  Interest Rate              -> interestRate / revertRate
  Initial Repayment Amount   -> monthlyRepayment
  Interest Type              -> rateType
  Repayment Type             -> repaymentType   ("Principal and Interest" -> "P&I")
  Offset account             -> offsetAccount
  Ongoing annual fee         -> annualFacilityFee
  Security Property          -> securityProperty (trailing ", Australia" stripped)
  Solicitor                  -> panelSolicitor
  Special conditions (p.3)   -> specialConditions (numbered; "Origin" -> brand)
  first person Email         -> borrowerEmail
Product Name is intentionally left blank — the WLTH marketing product name
(e.g. "Ocean SMSF Residential 80") isn't in the S4, so the user completes it.
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
        ln = re.sub('[\ue000-\uf8ff\u2022\u25aa\u25cf\u25a0]', ' ', ln)  # drop bullet/PUA glyphs
        s = ' '.join(ln.split())  # collapse internal whitespace
        if not s:
            continue
        if re.match(r'^Page \d+ of \d+$', s):
            continue
        if re.match(r'^APP-\s+\d', s):  # spaced watermark, not the real APP-###### value
            continue
        out.append(s)
    return out


def _after(lines, label, start=0):
    for i in range(start, len(lines) - 1):
        if lines[i] == label:
            return lines[i + 1].strip()
    return ''


def _fmt_date(s):
    m = re.match(r'(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{4})', s)
    if not m:
        return s
    return f"{m.group(1).zfill(2)}/{MONTHS.get(m.group(2)[:3].lower(), '01')}/{m.group(3)}"


def _applicant_entries(lines):
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


def _special_conditions(lines, brand):
    try:
        si = lines.index('Special conditions')
    except ValueError:
        return ''
    ei = len(lines)
    for marker in ('Special instructions to solicitor',):
        if marker in lines:
            ei = min(ei, lines.index(marker))
    conds, cur = [], []
    for l in lines[si + 1:ei]:
        if l in ('Condition unmet', 'Condition met'):
            if cur:
                conds.append(' '.join(cur))
                cur = []
        else:
            cur.append(l)
    if cur:
        conds.append(' '.join(cur))
    label = BRAND_LABEL.get(brand, 'WLTH')
    # strip bullet glyphs (incl. the Symbol-font  used in the S4 PDF)
    bullets = '•▪●·'
    cleaned = []
    for c in conds:
        c = re.sub(rf'[{bullets}]', '', c)
        c = re.sub(r'\s{2,}', ' ', c).strip()
        c = re.sub(r'\bOrigin\b', label, c)
        if c:
            cleaned.append(c)
    return '\n'.join(f'{i + 1}. {c}' for i, c in enumerate(cleaned))


def parse_schedule4(path, brand='wlth'):
    lines = _lines(path)
    out = {}

    def put(key, val):
        if val:
            out[key] = val.strip()

    put('date', _fmt_date(_after(lines, 'Date of Approval')))
    put('panelSolicitor', _after(lines, 'Solicitor'))
    put('loanAccountNumber', _after(lines, 'Loan Account Number'))
    put('loanAmount', _after(lines, 'Loan Amount'))
    put('loanTerm', _after(lines, 'Loan Term (Years)'))
    rate = _after(lines, 'Interest Rate')
    put('interestRate', rate)
    put('revertRate', rate)
    put('monthlyRepayment', _after(lines, 'Initial Repayment Amount'))

    itype = _after(lines, 'Interest Type')
    put('rateType', 'Fixed' if 'fixed' in itype.lower() else 'Variable')
    rtype = _after(lines, 'Repayment Type')
    put('repaymentType', 'Interest Only' if 'interest only' in rtype.lower() else 'P&I')
    offset = _after(lines, 'Offset account')
    put('offsetAccount', 'No' if offset.lower().startswith('n') else 'Yes')
    put('redrawFacility', 'N/A')
    put('annualFacilityFee', _after(lines, 'Ongoing annual fee') or '$395.00')
    put('monthlyFees', '$0.00')

    sec = _after(lines, 'Security Property')
    put('securityProperty', re.sub(r',\s*Australia\s*$', '', sec))
    put('mortgagors', _after(lines, 'Ownership'))

    # Applicants
    entries = _applicant_entries(lines)
    borrowers = []
    for e in entries:
        if e['role'] == 'Borrower':
            borrowers.append(f"{e['name']} ATF {e['trust']}" if e['trust'] else e['name'])
    put('borrowers', ' and '.join(b for b in borrowers if b))
    guarantors = [e['name'] for e in entries
                  if e['role'] == 'Guarantor' and e['kind'] == 'Person Applicants' and e['name']]
    put('guarantors', ' and '.join(guarantors))

    put('borrowerEmail', _after(lines, 'Email'))
    put('specialConditions', _special_conditions(lines, brand))
    return out
