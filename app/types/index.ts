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
  | 'commencement'
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
  type: 'text' | 'textarea' | 'richtext' | 'date' | 'number' | 'email' | 'currency' | 'select'
  required: boolean
  placeholder?: string
  help?: string
  default?: string // pre-filled value (a 'date' field defaults to today when empty)
  options?: { value: string; label: string }[] // for type: 'select'
  section?: string // optional grouping heading in the form UI
  showIf?: { field: string; equals: string } // only show when another field matches
  rows?: number // textarea height (rows); defaults to a small box when omitted
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
  /** How a 'form' type is filled: from a Schedule 4 upload, or by hand.
   *  Defaults to 'schedule4' when omitted. */
  source?: 'schedule4' | 'manual'
  /** Field schema for 'form' types. */
  fields?: LetterTypeField[]
  /** When set, the Download step also offers to create an email draft (with the
   *  letter attached). The draft is created from `from` (server-enforced). */
  email?: {
    from?: string // mailbox the draft is created from, e.g. 'construction@wlth.com'
    toLabel: string // label for the primary recipient input
    ccLabels?: string[] // labels for the CC recipient inputs (broker, borrowers…)
  }
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
  letterType: string // e.g. 'welcome', 'approval'
  typeLabel: string // e.g. 'Welcome Letter'
  brand: string // 'wlth' | 'mma'
  customer: string | null
  reference: string | null
  status: LetterStatus
  filename: string
  createdAt: string // ISO timestamp
}

export interface DeliveryResult {
  ok: boolean
  message: string
  reference?: string
  link?: string // e.g. a Google Drive file link
}
