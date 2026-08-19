import type { LetterType, LetterTypeId } from '~/types'

/**
 * The registry of letter types the app can generate.
 *
 * ADDING A NEW LETTER TYPE
 * ------------------------
 * 1. Add an entry here (id, label, description, icon, inputModel).
 * 2. For a 'form' type, list its `fields` — these render automatically in the
 *    Fill-in step and are passed to the engine as name/value pairs.
 * 3. Add the matching renderer in the Python engine (see
 *    docs/ADDING_A_LETTER_TYPE.md) and set `engine` to its id.
 * 4. Flip `status` from 'coming-soon' to 'available'.
 * That's the whole drop-in — the dashboard, wizard, preview, download and email
 * all pick the new type up from this registry.
 */
export const LETTER_TYPES: Record<LetterTypeId, LetterType> = {
  welcome: {
    id: 'welcome',
    label: 'Welcome Letter',
    description:
      'Send a warm welcome to new customers and provide important information.',
    icon: 'M3 8l7.9 5.3a2 2 0 002.2 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
    status: 'available',
    inputModel: 'upload',
    engine: 'welcome',
  },

  approval: {
    id: 'approval',
    label: 'Formal Approval Letter',
    description: 'Generate a formal approval letter for approved applications.',
    icon: 'M9 12l2 2 4-4m1 8H8a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v10a2 2 0 01-2 2z',
    status: 'available',
    inputModel: 'form',
    engine: 'approval',
    source: 'schedule4',
    fields: [
      // Applicant Overview
      { id: 'date', label: 'Letter Date', type: 'date', required: true, section: 'Applicant Overview' },
      { id: 'borrowers', label: 'Borrower(s)', type: 'text', required: true, placeholder: 'Mr John Smith & Mrs Jane Smith', section: 'Applicant Overview' },
      { id: 'mortgagors', label: 'Mortgagor(s)', type: 'text', required: false, placeholder: 'Same as borrower(s), or an entity name', section: 'Applicant Overview' },
      { id: 'guarantors', label: 'Guarantor(s)', type: 'text', required: false, placeholder: 'Leave blank if none', section: 'Applicant Overview' },
      { id: 'borrowerEmail', label: 'Borrower Email (for the draft)', type: 'email', required: false, placeholder: 'john@example.com', section: 'Applicant Overview' },
      // Product Details
      { id: 'productName', label: 'Product Name', type: 'text', required: false, placeholder: 'Ocean (WLTH) / Ultra (MMA)', help: 'Leave blank to use the brand default.', section: 'Product Details' },
      { id: 'loanAccountNumber', label: 'Loan Account Number(s)', type: 'text', required: true, placeholder: '200009019', section: 'Product Details' },
      { id: 'loanAmount', label: 'Loan Amount', type: 'currency', required: true, placeholder: '$750,000.00', section: 'Product Details' },
      { id: 'loanTerm', label: 'Loan Term', type: 'text', required: true, placeholder: '30 Years', section: 'Product Details' },
      { id: 'interestRate', label: 'Interest Rate', type: 'text', required: true, placeholder: '6.24%', section: 'Product Details' },
      { id: 'revertRate', label: 'Revert Rate', type: 'text', required: false, placeholder: '6.49%', section: 'Product Details' },
      { id: 'monthlyRepayment', label: 'Monthly Repayment', type: 'currency', required: true, placeholder: '$4,612.30', section: 'Product Details' },
      { id: 'rateType', label: 'Rate Type', type: 'select', required: true, default: 'Variable', options: [{ value: 'Variable', label: 'Variable' }, { value: 'Fixed', label: 'Fixed' }], section: 'Product Details' },
      { id: 'repaymentType', label: 'Repayment Type', type: 'select', required: true, default: 'P&I', options: [{ value: 'P&I', label: 'Principal & Interest' }, { value: 'Interest Only', label: 'Interest Only' }], section: 'Product Details' },
      { id: 'annualFacilityFee', label: 'Annual Facility Fee', type: 'text', required: false, default: '$395.00', section: 'Product Details' },
      { id: 'monthlyFees', label: 'Monthly Fees', type: 'text', required: false, default: '$0.00', section: 'Product Details' },
      { id: 'offsetAccount', label: 'Offset Account', type: 'select', required: true, default: 'Yes', options: [{ value: 'Yes', label: 'Yes' }, { value: 'No', label: 'No' }], section: 'Product Details' },
      { id: 'redrawFacility', label: 'Redraw Facility', type: 'text', required: false, placeholder: 'Yes', section: 'Product Details' },
      // Security & Conditions
      { id: 'securityProperty', label: 'Security Property', type: 'textarea', required: true, placeholder: '28 Leichhardt Drive, Moranbah QLD 4744', section: 'Security & Conditions' },
      { id: 'panelSolicitor', label: 'Our Panel Solicitor', type: 'text', required: false, default: 'Green Mortgage Lawyers', section: 'Security & Conditions' },
      { id: 'specialConditions', label: 'Special Conditions', type: 'textarea', required: false, placeholder: 'One condition per line…', section: 'Security & Conditions' },
    ],
  },

  commencement: {
    id: 'commencement',
    label: 'Commencement Letter',
    description: 'Notify a builder that progress payments can commence for a construction loan.',
    icon: 'M3 21h18M5 21V7l7-4 7 4v14M9 9h.01M9 13h.01M9 17h.01M15 9h.01M15 13h.01M15 17h.01',
    status: 'available',
    inputModel: 'form',
    engine: 'commencement',
    source: 'manual',
    email: {
      from: 'construction@wlth.com',
      toLabel: 'Builder email',
      ccLabels: ['Broker email', 'Borrower email(s)'],
    },
    fields: [
      // Builder (name/address block + salutation)
      { id: 'builderName', label: 'Builder Name', type: 'text', required: true, placeholder: 'United Homes Qld Pty Ltd', section: 'Builder' },
      { id: 'builderAddress', label: 'Builder Address', type: 'text', required: false, placeholder: '8 Honeysuckle Crescent, Bridgeman Downs', help: 'We’ll split this onto two lines automatically.', section: 'Builder' },
      { id: 'builderAbn', label: 'Builder ABN', type: 'text', required: false, placeholder: 'ABN: 75634805208', section: 'Builder' },
      { id: 'date', label: 'Date', type: 'date', required: false, section: 'Builder' },
      // What you need to know (the table)
      { id: 'customerNames', label: 'Customer Name(s)', type: 'text', required: false, placeholder: 'Tristan & Penelope Waller', section: 'Progress Payment Details' },
      { id: 'applicationNumber', label: 'Application Number', type: 'text', required: false, placeholder: '400178868', section: 'Progress Payment Details' },
      { id: 'disbursementTotal', label: 'Disbursement Total', type: 'currency', required: false, placeholder: '$540,000.00', section: 'Progress Payment Details' },
      { id: 'constructionAddress', label: 'Construction Address', type: 'text', required: false, placeholder: '60 Ryder Street, Wynnum, Queensland, 4178', section: 'Progress Payment Details' },
    ],
  },

  'pre-approval': {
    id: 'pre-approval',
    label: 'Pre-Approval Letter',
    description: 'Create pre-approval letters for eligible customers.',
    icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM6 21a6 6 0 0112 0',
    status: 'available',
    inputModel: 'form',
    engine: 'pre-approval',
    source: 'manual',
    fields: [
      // Applicant Overview
      { id: 'date', label: 'Letter Date', type: 'date', required: false, section: 'Applicant Overview' },
      { id: 'borrowers', label: 'Borrower(s)', type: 'text', required: true, placeholder: 'Mr John Smith & Mrs Jane Smith', section: 'Applicant Overview' },
      { id: 'mortgagors', label: 'Mortgagor(s)', type: 'text', required: false, placeholder: 'Same as borrower(s), or an entity name', section: 'Applicant Overview' },
      { id: 'guarantors', label: 'Guarantor(s)', type: 'text', required: false, placeholder: 'Leave blank if none', section: 'Applicant Overview' },
      // Product Details
      { id: 'productName', label: 'Product Name', type: 'text', required: false, placeholder: 'Ocean (WLTH) / Ultra (MMA)', help: 'Leave blank to use the brand default.', section: 'Product Details' },
      { id: 'applicationNumber', label: 'Application Reference No.', type: 'text', required: false, placeholder: 'APP-791033', section: 'Product Details' },
      { id: 'loanAmount', label: 'Loan Amount', type: 'currency', required: false, placeholder: '$750,000.00', section: 'Product Details' },
      { id: 'loanTerm', label: 'Loan Term (Years)', type: 'text', required: false, placeholder: '30', help: '“Years” is added automatically.', section: 'Product Details' },
      { id: 'interestRate', label: 'Interest Rate', type: 'text', required: false, placeholder: '6.24%', section: 'Product Details' },
      { id: 'rateType', label: 'Rate Type', type: 'select', required: false, default: 'Variable', options: [{ value: 'Variable', label: 'Variable' }, { value: 'Fixed', label: 'Fixed' }], section: 'Product Details' },
      { id: 'repaymentType', label: 'Repayment Type', type: 'select', required: false, default: 'P&I', options: [{ value: 'P&I', label: 'Principal & Interest' }, { value: 'Interest Only', label: 'Interest Only' }], section: 'Product Details' },
      { id: 'ioYears', label: 'Interest Only Period (Years)', type: 'text', required: false, placeholder: '5', help: 'Shows as “Interest Only – 5 Years”.', section: 'Product Details', showIf: { field: 'repaymentType', equals: 'Interest Only' } },
      // Security
      { id: 'securityProperty', label: 'Security Property', type: 'text', required: false, default: 'To be advised', section: 'Security' },
    ],
  },

  'conditional-approval': {
    id: 'conditional-approval',
    label: 'Conditional Approval Letter',
    description: 'Generate letters for approvals subject to specific conditions.',
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
    status: 'available',
    inputModel: 'form',
    engine: 'conditional-approval',
    source: 'manual',
    fields: [
      // Applicant Overview
      { id: 'date', label: 'Letter Date', type: 'date', required: false, section: 'Applicant Overview' },
      { id: 'borrowers', label: 'Borrower(s)', type: 'text', required: true, placeholder: 'Mr John Smith & Mrs Jane Smith', section: 'Applicant Overview' },
      { id: 'mortgagors', label: 'Mortgagor(s)', type: 'text', required: false, placeholder: 'Same as borrower(s), or an entity name', section: 'Applicant Overview' },
      { id: 'guarantors', label: 'Guarantor(s)', type: 'text', required: false, placeholder: 'Leave blank if none', section: 'Applicant Overview' },
      // Product Details
      { id: 'productName', label: 'Product Name', type: 'text', required: false, placeholder: 'Ocean (WLTH) / Ultra (MMA)', help: 'Leave blank to use the brand default.', section: 'Product Details' },
      { id: 'applicationNumber', label: 'Application Reference No.', type: 'text', required: false, placeholder: 'APP-791033', section: 'Product Details' },
      { id: 'loanAmount', label: 'Loan Amount', type: 'currency', required: false, placeholder: '$750,000.00', section: 'Product Details' },
      { id: 'loanTerm', label: 'Loan Term (Years)', type: 'text', required: false, placeholder: '30', help: '“Years” is added automatically.', section: 'Product Details' },
      { id: 'interestRate', label: 'Interest Rate', type: 'text', required: false, placeholder: '6.24%', section: 'Product Details' },
      { id: 'rateType', label: 'Rate Type', type: 'select', required: false, default: 'Variable', options: [{ value: 'Variable', label: 'Variable' }, { value: 'Fixed', label: 'Fixed' }], section: 'Product Details' },
      { id: 'repaymentType', label: 'Repayment Type', type: 'select', required: false, default: 'P&I', options: [{ value: 'P&I', label: 'Principal & Interest' }, { value: 'Interest Only', label: 'Interest Only' }], section: 'Product Details' },
      { id: 'ioYears', label: 'Interest Only Period (Years)', type: 'text', required: false, placeholder: '5', help: 'Shows as “Interest Only – 5 Years”.', section: 'Product Details', showIf: { field: 'repaymentType', equals: 'Interest Only' } },
      { id: 'offsetAccount', label: 'Offset Account', type: 'select', required: false, default: 'Yes', options: [{ value: 'Yes', label: 'Yes' }, { value: 'No', label: 'No' }], section: 'Product Details' },
      { id: 'redrawFacility', label: 'Redraw Facility', type: 'text', required: false, placeholder: 'Yes', section: 'Product Details' },
      // Security & Conditions
      { id: 'securityProperty', label: 'Security Property', type: 'textarea', required: false, placeholder: '28 Leichhardt Drive, Moranbah QLD 4744', section: 'Security & Conditions' },
      { id: 'conditionalItems', label: 'Conditional Approval Items', type: 'textarea', required: false, placeholder: 'One condition per line…', help: 'Numbered lines (1., 2.) render as a numbered list.', section: 'Security & Conditions' },
    ],
  },

  'credit-approval-memorandum': {
    id: 'credit-approval-memorandum',
    label: 'Credit Approval Memorandum',
    description: 'Internal CAM — assess the application and record the credit recommendation.',
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01',
    status: 'available',
    inputModel: 'form',
    engine: 'credit-approval-memorandum',
    source: 'manual',
    loanAppImport: true,
    fields: [
      // Overview
      { id: 'date', label: 'Date', type: 'date', required: false, section: 'Overview' },
      { id: 'borrowers', label: 'Borrower(s)', type: 'text', required: true, placeholder: 'Mr John Smith & Mrs Jane Smith', section: 'Overview' },
      { id: 'mortgageManager', label: 'Mortgage Manager', type: 'text', required: false, default: 'WLTH', section: 'Overview' },
      // Proposed Exposure
      { id: 'exposureAccount', label: 'Account Number', type: 'text', required: false, placeholder: '400192207', section: 'Proposed Exposure' },
      { id: 'exposureBalance', label: 'Proposed Balance', type: 'currency', required: false, placeholder: '$750,000.00', section: 'Proposed Exposure' },
      { id: 'exposureInterestType', label: 'Interest Type', type: 'text', required: false, default: 'Variable', section: 'Proposed Exposure' },
      { id: 'exposureLoanPurpose', label: 'Loan Purpose', type: 'text', required: false, placeholder: 'Purchase - Owner Occupied', section: 'Proposed Exposure' },
      { id: 'proposedSecurity', label: 'Proposed Security', type: 'textarea', required: false, default: 'TBA', section: 'Proposed Exposure' },
      { id: 'proposedLvr', label: 'Proposed LVR', type: 'text', required: false, placeholder: '72%', section: 'Proposed Exposure' },
      // Background Information
      { id: 'backgroundInformation', label: 'Background Information', type: 'textarea', required: false, rows: 3, section: 'Background Information' },
      { id: 'personalInfo', label: 'Personal Info', type: 'textarea', required: false, rows: 5, default: '(MA)\nID Checked – Category 1 (VOI conducted by a Third-Party Certifier)\nPassport (valid)\nDriver’s License (valid)', section: 'Background Information' },
      { id: 'employment', label: 'Employment', type: 'textarea', required: false, rows: 3, default: 'Payslips:\nGross Base Income:\nSalary Credits in:', section: 'Background Information' },
      { id: 'rentalIncome', label: 'Rental Income', type: 'textarea', required: false, rows: 2, section: 'Background Information' },
      { id: 'security', label: 'Security', type: 'textarea', required: false, rows: 6, default: 'Metro (Category 1)\nValuation Date:\nMain Dwelling:\nLiving Area:\nComparable Sales:\nMarket Value (Valuation Report):\nRental Income:', section: 'Background Information' },
      { id: 'lmi', label: 'LMI', type: 'text', required: false, default: 'N/A (Does not exceed 80% LVR)', section: 'Background Information' },
      { id: 'refinanceNotes', label: 'Refinance History', type: 'refinance', required: false, help: 'Add up to 5 refinances — each becomes a row (Refinance N | notes).', section: 'Background Information' },
      { id: 'liabilities', label: 'Liabilities', type: 'textarea', required: false, rows: 2, section: 'Background Information' },
      { id: 'creditHistory', label: 'Credit History', type: 'textarea', required: false, rows: 5, default: 'Report date:  – Comprehensive\nEquifax Score:\nClear from any adverse\nNo Recent Credit Enquiries\nNo Recent Commercial Enquiry\nNo Current Directorship', section: 'Background Information' },
      { id: 'ndi', label: 'NDI', type: 'textarea', required: false, rows: 2, section: 'Background Information' },
      { id: 'livingCost', label: 'Living Cost', type: 'textarea', required: false, rows: 2, placeholder: 'Living cost: $ pm / $ pa — HEM of ( %)', section: 'Background Information' },
      // Assessment
      { id: 'policyExceptions', label: 'Policy Exceptions (including mitigants)', type: 'textarea', required: false, rows: 3, section: 'Assessment' },
      { id: 'finalAssessment', label: 'Final Assessment', type: 'textarea', required: false, rows: 8, default: 'I have assessed the loan application in a prudent manner and reasonable enquiries have been made in my assessment and I have determined that the loan is not unsuitable for the applicant/s and that the:\nthe loan terms meet the applicant/s requirements and objectives;\nthe applicant/s will be able to comply with their financial obligations under the loan product;\nthe applicant/s have the requisite capacity to service all financial commitments and without substantial hardship; and\neach applicant/s has the requisite authority / capacity to grant the supporting securities.', section: 'Assessment' },
      { id: 'recommendation', label: 'Recommendation / Approval (including conditions)', type: 'textarea', required: false, rows: 4, default: 'Recommended for Conditional Approval:', section: 'Assessment' },
      { id: 'recommendedName', label: 'Assessor Name', type: 'text', required: true, section: 'Assessment' },
      { id: 'recommendedDate', label: 'Date Signed', type: 'date', required: false, section: 'Assessment' },
      { id: 'recommendedSignature', label: 'Signature', type: 'signature', required: true, help: 'Sign in the box — this is placed at the Signature line in the PDF and Word doc.', section: 'Assessment' },
    ],
  },

  discharge: {
    id: 'discharge',
    label: 'Discharge Confirmation Letter',
    description: 'Confirm loan discharge and account closure with this letter.',
    icon: 'M9 12l2 2 4-4m-3-8.3l7 3.1v4.7c0 4.4-3 8.5-7 9.7-4-1.2-7-5.3-7-9.7V6.5l7-3.1z',
    status: 'available',
    inputModel: 'form',
    engine: 'discharge',
    source: 'manual',
    fields: [
      // Recipient
      { id: 'recipientName', label: 'Recipient Name', type: 'text', required: true, placeholder: 'Mrs Louise Ntambwe', section: 'Recipient' },
      { id: 'recipientAddress', label: 'Recipient Address', type: 'textarea', required: false, rows: 3, placeholder: '19 Tulipwood Street,\nCollingwood Park, QLD,\n4301', help: 'One line per row.', section: 'Recipient' },
      // Discharge Details
      { id: 'date', label: 'Letter Date', type: 'date', required: false, section: 'Discharge Details' },
      { id: 'productName', label: 'Loan Product', type: 'text', required: false, placeholder: 'Ultra', section: 'Discharge Details' },
      { id: 'accountNumbers', label: 'Loan Account Number(s)', type: 'text', required: true, placeholder: '400136590 & 400136611', section: 'Discharge Details' },
      { id: 'dischargeDate', label: 'Discharge / Release Date', type: 'text', required: false, placeholder: '27 February 2026', section: 'Discharge Details' },
      // Security
      { id: 'securityAddress', label: 'Security Address', type: 'textarea', required: false, rows: 2, placeholder: '19 Tulipwood Street, Collingwood Park, Queensland, 4301, Australia', section: 'Security' },
    ],
  },

  custom: {
    id: 'custom',
    label: 'Custom Letter',
    description: 'Create a custom letter using templates or your own content.',
    icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.4-9.6a2 2 0 112.8 2.8L11.8 15.2 8 16l.8-3.8 8.8-8.8z',
    status: 'available',
    inputModel: 'form',
    engine: 'custom',
    source: 'manual',
    fields: [
      // Recipient block (top of the letter)
      { id: 'recipientName', label: 'Recipient Name', type: 'text', required: false, placeholder: 'Mr. Smith', section: 'Recipient' },
      { id: 'recipientAddress', label: 'Recipient Address', type: 'text', required: false, placeholder: '98 Shirley Street, Pimpama, QLD 4209', help: 'We’ll split this onto two lines automatically.', section: 'Recipient' },
      // Letter
      { id: 'date', label: 'Date', type: 'date', required: false, section: 'Letter' },
      { id: 'salutation', label: 'Greeting (after “Dear”)', type: 'text', required: false, placeholder: 'Mr. Smith', help: 'Leave blank to use the recipient name.', section: 'Letter' },
      { id: 'body', label: 'Letter Body', type: 'richtext', required: true, placeholder: 'Write the letter content… Use the toolbar for bold, underline, size and colour. Leave a blank line between paragraphs.', help: 'Formatting (bold, underline, size, colour) carries through to the PDF.', section: 'Letter' },
      { id: 'signOff', label: 'Sign-off', type: 'text', required: false, default: 'Sincerely,', section: 'Letter' },
      // Signature
      { id: 'senderName', label: 'Your Name', type: 'text', required: false, placeholder: 'Firstname Lastname', section: 'Signature' },
      { id: 'senderTitle', label: 'Your Job Title', type: 'text', required: false, placeholder: 'Job Title', section: 'Signature' },
    ],
  },
}

export const LETTER_TYPE_LIST: LetterType[] = Object.values(LETTER_TYPES)

export function getLetterType(id: LetterTypeId | null | undefined): LetterType | null {
  return id ? LETTER_TYPES[id] ?? null : null
}
