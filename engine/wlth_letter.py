import sys, zipfile, re, json
from xml.etree import ElementTree as ET
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def _pt(p):
    out=[]
    for n in p.iter():
        if n.tag==W+'t': out.append(n.text or '')
        elif n.tag==W+'tab': out.append('\t')
        elif n.tag==W+'br': out.append('\n')
    return ''.join(out)
def _cell(tc): return ' '.join(x for x in (_pt(p).strip() for p in tc.findall('.//'+W+'p')) if x)

def para_html(p):
    """Paragraph text with the funder's bold runs preserved as <b> (reportlab markup).
    The funder wraps bold text in nested runs (<w:r><w:rPr><w:b/></w:rPr><w:r>…</w:r></w:r>),
    so we process only outermost runs to avoid emitting the text twice."""
    runs=list(p.iter(W+'r'))
    inner={id(sub) for r in runs for sub in r.iter(W+'r') if sub is not r}
    parts=[]
    for r in runs:
        if id(r) in inner: continue
        rpr=r.find(W+'rPr')
        bel=rpr.find(W+'b') if rpr is not None else None
        bold=bel is not None and bel.get(W+'val') not in ('0','false')
        txt=''.join((x.text or '') if x.tag==W+'t' else (' ' if x.tag==W+'tab' else '') for x in r.iter())
        if not txt: continue
        esc=txt.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        parts.append(f'<b>{esc}</b>' if bold else esc)
    return ''.join(parts)

def repayment_items(path):
    """The repayment paragraphs (between Loan Account Details and Offset), each
    as {html, bullet} so the PDF keeps the funder's bold runs and bullet list."""
    z=zipfile.ZipFile(path); root=ET.fromstring(z.read('word/document.xml'))
    seq=[]
    def walk(el):
        for c in el:
            if c.tag in (W+'p', W+'tbl'): seq.append(c)
            elif c.tag in (W+'sdt', W+'sdtContent'): walk(c)
    walk(root.find(W+'body'))
    def ptext(p): return ''.join(t.text or '' for t in p.iter(W+'t'))
    la=next((i for i,e in enumerate(seq) if e.tag==W+'p' and 'Your Loan Account Details' in ptext(e)), None)
    items=[]
    if la is not None:
        for e in seq[la+1:]:
            if e.tag!=W+'p': continue
            t=ptext(e)
            if 'Linked Offset' in t or t.strip().startswith('Yours sincerely'): break
            if not t.strip(): continue
            ppr=e.find(W+'pPr')
            bullet=ppr is not None and ppr.find(W+'numPr') is not None
            items.append({'html':para_html(e), 'bullet':bullet})
    return items

def blocks(path):
    z=zipfile.ZipFile(path); root=ET.fromstring(z.read('word/document.xml')); out=[]
    def walk(el):
        for c in el:
            if c.tag==W+'p':
                t=_pt(c).strip()
                if t: out.append(('p',t))
            elif c.tag==W+'tbl':
                for tr in c.findall(W+'tr'):
                    out.append(('row',[_cell(tc) for tc in tr.findall(W+'tc')]))
            elif c.tag in (W+'sdt',W+'sdtContent'): walk(c)
    walk(root.find(W+'body')); return out

def parse_funder(path):
    b=blocks(path); ps=[t for k,t in b if k=='p']
    rows={r[0].rstrip(':').strip():(r[1].strip() if len(r)>1 else '') for k,r in b if k=='row' and r and r[0].strip()}
    d={}
    di=next((i for i,t in enumerate(ps) if re.match(r'^\s*\d{1,2}\s+\w+\s+\d{4}$',t)),None)
    d['recipient_name']=ps[0].strip()
    d['address']=[x.strip() for x in ps[1:di]]
    d['date']=ps[di].strip()
    d['greeting']=ps[di+1].strip()
    d['is_entity']=not d['greeting'].lower().startswith('dear')
    for t in ps:
        m=re.search(r'Home Loan with\s+(.+?)\s+on\s+([\d/]+)',t)
        if m: d['lender']=m.group(1).strip(); d['settlement_date']=m.group(2)
        s=t.replace('\t',' ')
        for lbl,key in [('Your Customer Number','customer_number'),('Your Customer SMSF Number','smsf_number'),('Your Loan Facility Number','loan_facility_number')]:
            mm=re.match(rf'{lbl}:\s*(\d+)',s.strip())
            if mm: d[key]=mm.group(1)
        for rx,key in [(r'minimum monthly contractual repayment is\s*(\$[\d,]+\.\d{2})','min_monthly'),
                       (r'is due on\s*([\d/]+)','first_repayment_date'),
                       (r'minimum weekly repayment is\s*(\$[\d,]+\.\d{2})','min_weekly'),
                       (r'minimum fortnightly repayment is\s*(\$[\d,]+\.\d{2})','min_fortnightly')]:
            mm=re.search(rx,t)
            if mm and key not in d: d[key]=mm.group(1)
    d['loan_purpose']=rows.get('Loan Purpose','')
    d['loan_amount']=rows.get('Loan Facility Amount','')
    d['borrowers_names']=rows.get('Borrower’s/s’ Names',rows.get("Borrower's/s' Names",''))
    d['guarantors_names']=rows.get('Guarantors Names','')
    d['loan_bsb']=rows.get('BSB Number','')
    d['current_balance']=rows.get('Current Account Balance','')
    d['loan_term']=rows.get('Loan Account Term','')
    d['interest_type']=rows.get('Interest Type','')
    d['interest_rate']=rows.get('Current interest Rate','')
    d['repayment_type']=rows.get('Repayment Type','')
    d['io_period']=rows.get('Interest Only Period (Months)','')
    d['offset_account']=rows.get('Offset Account Number','')
    d['offset_balance']=rows.get('Current Balance','')
    # repayment paragraph(s), with the funder's bold runs + bullet list preserved
    d['repayment_lines']=repayment_items(path)
    d['has_offset']=bool(d['offset_account'])
    return d

BRANDS={
 'wlth':{'portal':'www.wlth.com and click on the Portal button.','phone':'13 WLTH','email':'Hello@wlth.com','signoff':'The WLTH team.'},
 'mma':{'portal':'https://online.originmms.com.au/ib/mortgagemart','phone':'1300 650 200','email':'hello@wlth.com','signoff':'The Mortgage Mart Team.'},
}

def render_text(d, brand, dd_bsb, dd_account, smsf_number=None):
    B=BRANDS[brand]; L=[]
    A=L.append
    A(d['recipient_name'])
    for a in d['address']: A(a)
    A(d['date']); A(d['greeting'])
    A(f"Congratulations on the settlement of your new Home Loan with {d['lender']} on {d['settlement_date']}!")
    A("This letter contains important information regarding your new home loan facility.")
    if d['is_entity']:
        A(f"Your Customer SMSF Number: {d['customer_number']}")
    else:
        A(f"Your Customer Number: {d['customer_number']}")
        if smsf_number: A(f"Your Customer SMSF Number: {smsf_number}")
    A(f"Your Loan Facility Number: {d['loan_facility_number']}")
    A("In order to best assist you, your Customer and/or Loan Facility Number is required whenever you contact us to discuss your home loan.")
    A("You can find the key details of your individual loan account(s) below. Detailed financial statements will be issued every 6 months (in January and July each year), however you can choose to access your account(s) information online at any time.")
    A("Internet Account Access")
    A("Internet Account Access is an easy and reliable way for you to check your balance and recent payment history, as well as make repayments or transfer funds over the internet, at any time most convenient for you.")
    A("You should have already received instructions on how to access your online accounts as per below.")
    A(B['portal'])
    A("Your User ID has been provided via email.")
    A("Your temporary password has been provided via SMS.")
    A("Please contact us on 1300 767 023 between 8am - 7pm Monday to Friday (AEST) or 8am - 5pm Saturday (AEST) if you have not received your User ID or temporary password. Once you have changed your initial password, you can access your account online 24 hours a day, 7 days a week.")
    A("Customer Support")
    A(f"If you have any questions please feel free to call us on {B['phone']} between Monday to Friday 9am to 5pm or email us at {B['email']}.")
    if dd_bsb:
        A("Your Nominated Direct Debit Account Details:")
        A(f"BSB Number: {dd_bsb}"); A(f"Account Number: {dd_account}")
    A("Your Loan Facility Details:")
    A(f"Loan Purpose: {d['loan_purpose']}")
    A(f"Loan Facility Number: {d['loan_facility_number']}")
    A(f"Loan Facility Amount: {d['loan_amount']}")
    A(f"Borrower’s/s’ Names {d['borrowers_names']}")
    A(f"Guarantors Names {d['guarantors_names']}")
    A(f"Loan Account Number: {d['loan_facility_number']}")
    A("Your Loan Account Details:")
    A(f"BSB Number: {d['loan_bsb']}")
    A(f"Loan Account Number: {d['loan_facility_number']}")
    A(f"Current Account Balance: {d['current_balance']}")
    A(f"Loan Account Term: {d['loan_term']}")
    A(f"Interest Type: {d['interest_type']}")
    A(f"Current interest Rate: {d['interest_rate']}")
    A(f"Repayment Type: {d['repayment_type']}")
    A(f"Interest Only Period (Months): {d['io_period']}".rstrip())
    for item in d.get('repayment_lines', []):
        plain=re.sub(r'<[^>]+>','',item['html']).replace('&amp;','&').replace('&lt;','<').replace('&gt;','>')
        A(('• ' if item['bullet'] else '')+plain)
    if d.get('has_offset'):
        A("Your Linked Offset Account Details:")
        A(f"BSB Number: {d['loan_bsb']}")
        A(f"Offset Account Number: {d['offset_account']}")
        A(f"Current Balance: {d['offset_balance']}")
    A("Yours sincerely,"); A(B['signoff'])
    return '\n'.join(L)

if __name__=='__main__':
    print(json.dumps(parse_funder(sys.argv[1]),indent=2,ensure_ascii=False))
