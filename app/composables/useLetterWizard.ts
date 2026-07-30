import { BRANDS } from '~/utils/brands'
import { getLetterType } from '~/utils/letterTypes'
import type { BrandId, EngineResult, FieldValues, LetterTypeId, Party } from '~/types'

export interface WizardState {
  letterType: LetterTypeId | null // chosen on the landing page before the wizard
  step: number // 1..4
  brand: BrandId
  // 'upload' letter types (e.g. Welcome):
  files: File[] // the funder .docx uploads (one per party)
  parse: EngineResult | null // detected loan type + parties
  ddBsb: string // the single manual input…
  ddAccount: string // …applied to every party's letter
  noDirectDebit: boolean // no direct debit set up → omit the DD table
  offsetLinked: 'yes' | 'no' | null // mandatory — changes the email template
  // 'form' letter types (e.g. Approval, Discharge):
  fieldValues: FieldValues // keyed by LetterTypeField.id
  rendered: Party[] // parties with merged letter text
  deliveries: Record<string, { drive: boolean; email: boolean }>
}

function initialState(): WizardState {
  return {
    letterType: null,
    step: 1,
    brand: 'wlth',
    files: [],
    parse: null,
    ddBsb: '',
    ddAccount: '',
    noDirectDebit: false,
    offsetLinked: null,
    fieldValues: {},
    rendered: [],
    deliveries: {},
  }
}

// The wizard steps depend on the letter type's input model. 'upload' types
// collect the source docs then the BSB/account detail; 'form' types collect
// the field values in one step.
const UPLOAD_STEPS = [
  { id: 1, label: 'Upload Funder Docs' },
  { id: 2, label: 'BSB & Accounts' },
  { id: 3, label: 'Preview' },
  { id: 4, label: 'Save & Send' },
] as const

const FORM_STEPS = [
  { id: 1, label: 'Enter Details' },
  { id: 2, label: 'Preview' },
  { id: 3, label: 'Save & Send' },
] as const

// Kept for backwards-compatibility with existing imports.
export const WIZARD_STEPS = UPLOAD_STEPS

/** Shared, SSR-safe wizard state across all steps. */
export function useLetterWizard() {
  const state = useState<WizardState>('letter-wizard', initialState)
  const currentBrand = computed(() => BRANDS[state.value.brand])
  const currentType = computed(() => getLetterType(state.value.letterType))
  const steps = computed(() =>
    currentType.value?.inputModel === 'form' ? FORM_STEPS : UPLOAD_STEPS,
  )
  const lastStep = computed(() => steps.value.length)

  // Download/email filename for form letters, e.g. "WLTH Formal Approval Letter - John Smith".
  const formFilename = computed(() => {
    const t = currentType.value
    if (!t) return 'Letter'
    const label = state.value.brand === 'mortgage-mart' ? 'Mortgage Mart' : 'WLTH'
    const v = state.value.fieldValues
    const who = (v.borrowers || v.recipientName || '')
      .replace(/^(mr|mrs|ms|miss|dr)\.?\s+/i, '')
      .trim()
    return `${label} ${t.label}${who ? ' - ' + who : ''}`
  })

  function reset() {
    state.value = initialState()
  }
  /** Choose a letter type and start its wizard at step 1. */
  function chooseType(id: LetterTypeId) {
    reset()
    state.value.letterType = id
  }
  function goTo(step: number) {
    state.value.step = Math.min(lastStep.value, Math.max(1, step))
  }
  function next() {
    goTo(state.value.step + 1)
  }
  function back() {
    goTo(state.value.step - 1)
  }
  function setBrand(brand: BrandId) {
    state.value.brand = brand
  }

  return { state, currentBrand, currentType, steps, formFilename, reset, chooseType, goTo, next, back, setBrand }
}
