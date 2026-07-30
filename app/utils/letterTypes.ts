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
 * That's the whole drop-in — the UI, wizard, preview, download and email all
 * pick the new type up from this registry.
 */
export const LETTER_TYPES: Record<LetterTypeId, LetterType> = {
  welcome: {
    id: 'welcome',
    label: 'Welcome Letter',
    description:
      'Rebrand a funder’s welcome letter into a WLTH or Mortgage Mart letter. Auto-detects borrowers, trusts and SMSFs from the uploaded documents.',
    icon: 'M3 8l7.9 5.3a2 2 0 002.2 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
    status: 'available',
    inputModel: 'upload',
    engine: 'welcome',
  },

  approval: {
    id: 'approval',
    label: 'Formal Approval Letter',
    description:
      'Confirm formal (unconditional) approval of a loan application, including the approved amount and any conditions.',
    icon: 'M9 12l2 2 4-4m1 8H8a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v10a2 2 0 01-2 2z',
    status: 'coming-soon',
    inputModel: 'form',
    engine: 'approval',
    // Placeholder schema — refine once the official template arrives.
    fields: [
      { id: 'borrowerName', label: 'Borrower Name(s)', type: 'text', required: true, placeholder: 'Mr John Smith', section: 'Borrower' },
      { id: 'borrowerEmail', label: 'Borrower Email', type: 'email', required: false, placeholder: 'john@example.com', section: 'Borrower' },
      { id: 'loanAccountNumber', label: 'Loan / Application Number', type: 'text', required: true, placeholder: '200009019', section: 'Loan' },
      { id: 'approvedAmount', label: 'Approved Amount', type: 'currency', required: true, placeholder: '$500,000.00', section: 'Loan' },
      { id: 'approvalDate', label: 'Approval Date', type: 'date', required: true, section: 'Loan' },
      { id: 'conditions', label: 'Conditions of Approval', type: 'textarea', required: false, placeholder: 'One condition per line…', help: 'Leave blank for an unconditional approval.', section: 'Loan' },
    ],
  },

  discharge: {
    id: 'discharge',
    label: 'Discharge Letter',
    description:
      'Confirm the discharge of a mortgage once a loan is repaid or refinanced, including the security property and settlement details.',
    icon: 'M5 13l4 4L19 7M12 3a9 9 0 100 18 9 9 0 000-18z',
    status: 'coming-soon',
    inputModel: 'form',
    engine: 'discharge',
    // Placeholder schema — refine once the official template arrives.
    fields: [
      { id: 'borrowerName', label: 'Borrower Name(s)', type: 'text', required: true, placeholder: 'Mr John Smith', section: 'Borrower' },
      { id: 'borrowerEmail', label: 'Borrower Email', type: 'email', required: false, placeholder: 'john@example.com', section: 'Borrower' },
      { id: 'loanAccountNumber', label: 'Loan Account Number', type: 'text', required: true, placeholder: '200009019', section: 'Loan' },
      { id: 'securityAddress', label: 'Security Property Address', type: 'textarea', required: true, placeholder: '28 Leichhardt Drive, Moranbah QLD 4744', section: 'Loan' },
      { id: 'dischargeDate', label: 'Discharge / Settlement Date', type: 'date', required: true, section: 'Loan' },
    ],
  },
}

export const LETTER_TYPE_LIST: LetterType[] = Object.values(LETTER_TYPES)

export function getLetterType(id: LetterTypeId | null | undefined): LetterType | null {
  return id ? LETTER_TYPES[id] ?? null : null
}
