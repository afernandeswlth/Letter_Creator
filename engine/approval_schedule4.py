"""
Extract Formal Approval field values from an uploaded "Schedule 4" document.

STATUS: awaiting a sample Schedule 4 to map its layout to the approval field
ids in app/utils/letterTypes.ts (borrowers, mortgagors, guarantors,
loanAccountNumber, loanAmount, loanTerm, interestRate, revertRate,
monthlyRepayment, rateType, repaymentType, annualFacilityFee, monthlyFees,
offsetAccount, redrawFacility, securityProperty, panelSolicitor,
specialConditions, productName).

Until the mapping is implemented, parse_schedule4() returns {} so the UI falls
back to manual entry. To finish it: read the sample, then map its labels/values
to the field ids below.
"""
import zipfile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def docx_text(path):
    """Full plain text of a .docx (paragraphs joined by newlines)."""
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read('word/document.xml'))
    return '\n'.join(
        ''.join(t.text or '' for t in p.iter(W + 't'))
        for p in root.iter(W + 'p')
    )


def parse_schedule4(path):
    """Return a dict of {field_id: value} extracted from the Schedule 4.

    Not yet implemented — needs a sample Schedule 4 to map fields. Returns {}
    so callers degrade gracefully to manual entry.
    """
    return {}
