// Shared domain types for the Letter Generator.

export type BrandId = 'mortgage-mart' | 'wlth'

// ---------------------------------------------------------------------------
// Letter types
// ---------------------------------------------------------------------------
// The app generates several kinds of letters. Each "letter type" is registered
// in app/utils/letterTypes.ts and declares how it collects input and how it is
// rendered. Two input models exist:
//   • 'upload' — the user uploads a source .docx that the engine parses and
//     rebrands (this is how Welcome Letters work).
//   • 'form'   — the user fills in fields defined by the type's schema, which
//     are merged into a branded template (Approval, Discharge, etc.).

export type LetterTypeId =
  | 'welcome'
  | 'approval'
  | 'pre-approval'
  | 'conditional-approval'
  | 'discharge'
  | 'custom'
export type InputModel = 'upload' | 'form'
// 'available'  — fully working (clickable, runs its flow)
// 'coming-soon' — clickable, in active development (shows the setup panel)
// 'disabled'    — greyed out and unclickable (planned, not started)
export type LetterTypeStatus = 'available' | 'coming-soon' | 'disabled'

/** One fillable field for a 'form' letter type. */
export interface LetterTypeField {
  id: string
  label: string
  type: 'text' | 'textarea' | 'date' | 'number' | 'email' | 'currency' | 'select'
  required: boolean
  placeholder?: string
  help?: string
  default?: string // pre-filled value (a 'date' field defaults to today when empty)
  options?: { value: string; label: string }[] // for type: 'select'
  section?: string // optional grouping heading in the form UI
}

export interface LetterType {
  id: LetterTypeId
  label: string
  description: string
  icon: string // inline SVG path (24x24 outline)
  status: LetterTypeStatus
  inputModel: InputModel
  /** Engine identifier passed to the Python CLI (e.g. 'welcome', 'approval'). */
  engine: string
  /** Field schema for 'form' types. */
  fields?: LetterTypeField[]
}

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
