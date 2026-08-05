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

  'pre-approval': {
    id: 'pre-approval',
    label: 'Pre-Approval Letter',
    description: 'Create pre-approval letters for eligible customers.',
    icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM6 21a6 6 0 0112 0',
    status: 'disabled',
    inputModel: 'form',
    engine: 'pre-approval',
    fields: [
      { id: 'borrowerName', label: 'Borrower Name(s)', type: 'text', required: true, placeholder: 'Mr John Smith', section: 'Borrower' },
      { id: 'borrowerEmail', label: 'Borrower Email', type: 'email', required: false, placeholder: 'john@example.com', section: 'Borrower' },
      { id: 'preApprovedAmount', label: 'Pre-Approved Amount', type: 'currency', required: true, placeholder: '$500,000.00', section: 'Loan' },
      { id: 'expiryDate', label: 'Pre-Approval Expiry Date', type: 'date', required: true, section: 'Loan' },
    ],
  },

  'conditional-approval': {
    id: 'conditional-approval',
    label: 'Conditional Approval Letter',
    description: 'Generate letters for approvals subject to specific conditions.',
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
    status: 'disabled',
    inputModel: 'form',
    engine: 'conditional-approval',
    fields: [
      { id: 'borrowerName', label: 'Borrower Name(s)', type: 'text', required: true, placeholder: 'Mr John Smith', section: 'Borrower' },
      { id: 'borrowerEmail', label: 'Borrower Email', type: 'email', required: false, placeholder: 'john@example.com', section: 'Borrower' },
      { id: 'loanAccountNumber', label: 'Loan / Application Number', type: 'text', required: true, placeholder: '200009019', section: 'Loan' },
      { id: 'approvedAmount', label: 'Approved Amount', type: 'currency', required: true, placeholder: '$500,000.00', section: 'Loan' },
      { id: 'conditions', label: 'Conditions', type: 'textarea', required: true, placeholder: 'One condition per line…', section: 'Loan' },
    ],
  },

  discharge: {
    id: 'discharge',
    label: 'Discharge Confirmation Letter',
    description: 'Confirm loan discharge and account closure with this letter.',
    icon: 'M9 12l2 2 4-4m-3-8.3l7 3.1v4.7c0 4.4-3 8.5-7 9.7-4-1.2-7-5.3-7-9.7V6.5l7-3.1z',
    status: 'disabled',
    inputModel: 'form',
    engine: 'discharge',
    fields: [
      { id: 'borrowerName', label: 'Borrower Name(s)', type: 'text', required: true, placeholder: 'Mr John Smith', section: 'Borrower' },
      { id: 'borrowerEmail', label: 'Borrower Email', type: 'email', required: false, placeholder: 'john@example.com', section: 'Borrower' },
      { id: 'loanAccountNumber', label: 'Loan Account Number', type: 'text', required: true, placeholder: '200009019', section: 'Loan' },
      { id: 'securityAddress', label: 'Security Property Address', type: 'textarea', required: true, placeholder: '28 Leichhardt Drive, Moranbah QLD 4744', section: 'Loan' },
      { id: 'dischargeDate', label: 'Discharge / Settlement Date', type: 'date', required: true, section: 'Loan' },
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
      { id: 'body', label: 'Letter Body', type: 'textarea', required: true, placeholder: 'Write the letter content…\n\nLeave a blank line between paragraphs.', section: 'Letter' },
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
