import { BRANDS } from '~/utils/brands'
import type { BrandId, EngineResult, Party } from '~/types'

export interface WizardState {
  step: number // 1..4
  brand: BrandId
  files: File[] // the funder .docx uploads (one per party)
  parse: EngineResult | null // detected loan type + parties
  ddBsb: string // the single manual input…
  ddAccount: string // …applied to every party's letter
  offsetLinked: 'yes' | 'no' | null // mandatory — changes the email template
  rendered: Party[] // parties with merged letter text
  deliveries: Record<string, { drive: boolean; email: boolean }>
}

function initialState(): WizardState {
  return {
    step: 1,
    brand: 'wlth',
    files: [],
    parse: null,
    ddBsb: '',
    ddAccount: '',
    offsetLinked: null,
    rendered: [],
    deliveries: {},
  }
}

export const WIZARD_STEPS = [
  { id: 1, label: 'Upload Funder Docs' },
  { id: 2, label: 'BSB & Accounts' },
  { id: 3, label: 'Preview' },
  { id: 4, label: 'Save & Send' },
] as const

/** Shared, SSR-safe wizard state across all four steps. */
export function useLetterWizard() {
  const state = useState<WizardState>('letter-wizard', initialState)
  const currentBrand = computed(() => BRANDS[state.value.brand])

  function reset() {
    state.value = initialState()
  }
  function goTo(step: number) {
    state.value.step = Math.min(4, Math.max(1, step))
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

  return { state, currentBrand, reset, goTo, next, back, setBrand }
}
