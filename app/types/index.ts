// Shared domain types for the Welcome Letter Generator.

export type BrandId = 'mortgage-mart' | 'wlth'

export interface Brand {
  id: BrandId
  name: string
  logo: string
  fromEmail: string
  driveFolder: string
  accent: string
}

export type LetterStatus = 'Draft' | 'Completed' | 'Sent'

export interface UploadedTemplate {
  id: string
  filename: string
  brand: BrandId
  uploadedAt: string
}

/**
 * A single fillable field derived from a `{{token}}` in the uploaded template.
 * The backend will produce this schema by scanning the .docx; for now it is mocked.
 */
export interface TemplateField {
  token: string // e.g. "borrower_name"
  label: string // e.g. "Borrower Name"
  type: 'text' | 'email' | 'date' | 'number' | 'textarea'
  placeholder?: string
  required: boolean
}

export type FieldValues = Record<string, string>

/** A borrower/entity on the loan, derived from one funder .docx. */
export interface Party {
  name: string
  role: 'Entity' | 'Member'
  customerNumber: string | null
  isEntity: boolean
  loanFacilityNumber?: string
  text?: string // the fully merged letter, once rendered
}

export interface EngineResult {
  loanType: string
  smsfNumber?: string | null
  parties: Party[]
}

export interface LetterRecord {
  id: string
  borrowerName: string
  template: string
  status: LetterStatus
  createdAt: string
}

export interface DeliveryResult {
  ok: boolean
  message: string
  reference?: string
  link?: string // e.g. a Google Drive file link
}
