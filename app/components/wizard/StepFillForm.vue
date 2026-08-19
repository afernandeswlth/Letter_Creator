<script setup lang="ts">
import type { LetterTypeField } from '~/types'

const { state, currentType, next, themeClasses } = useLetterWizard()
const { parseFormSource, importHubspotDeal } = useLetterApi()

const showErrors = ref(false)
// After a prefill (HubSpot import), every still-empty field is flagged red so the
// assessor can see at a glance what HubSpot didn't fill.
const prefilled = ref(false)

const today = new Date().toLocaleDateString('en-GB') // dd/mm/yyyy

const fields = computed<LetterTypeField[]>(() => currentType.value?.fields ?? [])

// Some form types are filled from a Schedule 4 upload (Approval); others are
// filled by hand (Custom). Manual-only types skip the upload UI entirely.
const supportsSchedule4 = computed(() => currentType.value?.source !== 'manual')

// CAM-style entry: no brand picker (always WLTH) and a choice between importing
// from the loan app and entering details by hand — the fields only appear once
// "Enter manually" is chosen.
const usesLoanAppEntry = computed(() => !!currentType.value?.loanAppImport)
const entryMode = ref<'hubspot' | 'manual' | null>(null)
// The fields are shown for ordinary manual types immediately, and for
// loan-app-entry types only after "Enter manually" (or a HubSpot import) reveals them.
const showFields = computed(() => !usesLoanAppEntry.value || entryMode.value === 'manual')

// --- HubSpot Deal import -----------------------------------------------------
const dealId = ref('')
const importing = ref(false)
const importMsg = ref('')
const importErr = ref('')

async function runHubspotImport() {
  importErr.value = ''
  importMsg.value = ''
  const id = dealId.value.trim()
  if (!id) {
    importErr.value = 'Enter a HubSpot Record ID.'
    return
  }
  importing.value = true
  try {
    const values = await importHubspotDeal(id)
    const keys = Object.keys(values)
    for (const k of keys) state.value.fieldValues[k] = values[k]!
    if (keys.length) {
      importMsg.value = `Imported ${keys.length} field${keys.length === 1 ? '' : 's'} from HubSpot — complete the fields outlined in red and review the amber (template default) ones below.`
      entryMode.value = 'manual' // reveal the (now prefilled) form
      prefilled.value = true // flag remaining empty fields red
    } else {
      importErr.value = 'That deal had no matching fields to import.'
    }
  } catch (e) {
    const msg = (e as { data?: { statusMessage?: string; message?: string }; statusMessage?: string })
    importErr.value = `Could not import the deal. ${msg?.data?.statusMessage || msg?.data?.message || msg?.statusMessage || (e as Error).message}`
  } finally {
    importing.value = false
  }
}

// Ordered, unique section names.
const sections = computed(() => {
  const seen: string[] = []
  for (const f of fields.value) {
    const s = f.section ?? 'Details'
    if (!seen.includes(s)) seen.push(s)
  }
  return seen
})
function isVisible(f: LetterTypeField) {
  const c = f.showIf
  return !c || (state.value.fieldValues[c.field] ?? '') === c.equals
}
const fieldsIn = (section: string) =>
  fields.value.filter((f) => (f.section ?? 'Details') === section && isVisible(f))

// Seed defaults (and blanks so the keys are reactive) once.
function seedDefaults() {
  for (const f of fields.value) {
    const cur = state.value.fieldValues[f.id]
    if (cur == null || cur === '') {
      state.value.fieldValues[f.id] = f.default ?? (f.type === 'date' ? today : '')
    }
  }
}
onMounted(() => {
  seedDefaults()
  // Manual-only types (Custom) have no Schedule 4 — go straight to the fields.
  if (!supportsSchedule4.value) state.value.formMode = 'manual'
  // Loan-app-entry types (CAM) are always WLTH and wait for a mode choice.
  if (usesLoanAppEntry.value) state.value.brand = 'wlth'
})

function fieldText(f: LetterTypeField) {
  const v = state.value.fieldValues[f.id] ?? ''
  // richtext holds HTML — measure the visible text, not the markup.
  return f.type === 'richtext' ? v.replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').trim() : v.trim()
}
const missing = (f: LetterTypeField) => f.required && !fieldText(f)
const isValid = computed(() => fields.value.every((f) => !missing(f)))
// Red border when a required field fails validation on Next, or when the form was
// prefilled and this field is still empty.
const highlight = (f: LetterTypeField) =>
  (showErrors.value && missing(f)) || (prefilled.value && !fieldText(f))
// Amber border when a field still holds its template default (boilerplate) — a hint
// to the assessor to review it or add more detail.
const isTemplateDefault = (f: LetterTypeField) =>
  !!f.default && (state.value.fieldValues[f.id] ?? '') === f.default
// Border colour: red (needs attention) wins over amber (review default) over normal.
const borderClass = (f: LetterTypeField) =>
  highlight(f) ? 'border-red-400' : isTemplateDefault(f) ? 'border-amber-400' : 'border-slate-300'

// --- Schedule 4 upload (auto-fill) -----------------------------------------
const fileInput = ref<HTMLInputElement | null>(null)
const dragging = ref(false)
const reading = ref(false)
const readMsg = ref('')
const readErr = ref('')

function pickFile() {
  fileInput.value?.click()
}
function onFile(list: FileList | null | undefined) {
  readErr.value = ''
  readMsg.value = ''
  const f = list?.[0]
  if (!f) return
  if (!/\.(docx|pdf)$/i.test(f.name)) {
    readErr.value = 'Please upload the Schedule 4 as a .docx or .pdf file.'
    return
  }
  state.value.files = [f]
  readSchedule4() // auto-read on upload
}
function removeFile() {
  state.value.files = []
  readMsg.value = ''
  state.value.formParsed = false
}

async function readSchedule4() {
  if (!currentType.value || !state.value.files.length) return
  reading.value = true
  readErr.value = ''
  readMsg.value = ''
  state.value.formParsed = false
  try {
    const values = await parseFormSource(currentType.value.engine, state.value.brand, state.value.files[0]!)
    const keys = Object.keys(values).filter((k) => values[k])
    for (const k of keys) state.value.fieldValues[k] = values[k]!
    state.value.formParsed = keys.length > 0
    readMsg.value = keys.length
      ? `Read ${keys.length} field${keys.length === 1 ? '' : 's'} from the Schedule 4. Continue to the preview to review.`
      : 'Uploaded, but no fields could be read automatically. Try Create Manually.'
  } catch (e) {
    readErr.value = `Could not read the Schedule 4. ${(e as Error).message}`
  } finally {
    reading.value = false
  }
}

function setMode(mode: 'manual' | 'schedule4') {
  showErrors.value = false
  state.value.formMode = mode
}

function onNext() {
  showErrors.value = true
  // Schedule 4 flow: once an S4 is read, proceed to Preview (review there).
  // Manual flow: require all fields.
  if (supportsSchedule4.value && state.value.formMode === 'schedule4') {
    if (state.value.formParsed) next()
  } else if (isValid.value) {
    next()
  }
}
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white p-6">
    <h2 class="text-lg font-semibold text-slate-900">Enter Details</h2>
    <p class="mt-1 text-sm text-slate-500">
      {{ usesLoanAppEntry
        ? 'Prefill from a HubSpot deal, or enter the details manually.'
        : (supportsSchedule4 ? 'Choose the brand, then upload the Schedule 4 to auto-fill the letter.' : 'Choose the brand, then fill in the letter details.') }}
    </p>

    <!-- Brand (hidden for loan-app-entry types — always WLTH) -->
    <div v-if="!usesLoanAppEntry" class="mt-6">
      <BrandSelector />
    </div>

    <!-- Loan-app-entry chooser (CAM): loan app (soon) / HubSpot deal / manual -->
    <div v-if="usesLoanAppEntry" class="mt-6">
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <!-- Import from loan app — disabled (coming soon) -->
        <div class="flex cursor-not-allowed items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 opacity-70">
          <WIcon name="download" class="mt-0.5 h-5 w-5 flex-none text-slate-300" />
          <span>
            <span class="flex flex-wrap items-center gap-1.5">
              <span class="text-sm font-semibold text-slate-400">Import from loan app</span>
              <span class="rounded-full bg-slate-200 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-slate-500">Coming soon</span>
            </span>
            <span class="mt-0.5 block text-xs text-slate-400">Pull the application details in automatically.</span>
          </span>
        </div>
        <!-- Import from HubSpot Deal -->
        <button
          type="button"
          class="flex items-start gap-3 rounded-xl border p-4 text-left transition"
          :class="entryMode === 'hubspot' ? 'border-blue-500 bg-blue-50/60 ring-1 ring-blue-500' : 'border-slate-200 hover:border-slate-300'"
          @click="entryMode = 'hubspot'"
        >
          <WIcon name="database" class="mt-0.5 h-5 w-5 flex-none text-blue-600" />
          <span>
            <span class="block text-sm font-semibold text-slate-900">Import from HubSpot Deal</span>
            <span class="block text-xs text-slate-500">Prefill from a HubSpot Record ID.</span>
          </span>
        </button>
        <!-- Enter manually -->
        <button
          type="button"
          class="flex items-start gap-3 rounded-xl border p-4 text-left transition"
          :class="entryMode === 'manual' ? 'border-blue-500 bg-blue-50/60 ring-1 ring-blue-500' : 'border-slate-200 hover:border-slate-300'"
          @click="entryMode = 'manual'"
        >
          <WIcon name="square-pen" class="mt-0.5 h-5 w-5 flex-none text-blue-600" />
          <span>
            <span class="block text-sm font-semibold text-slate-900">Enter manually</span>
            <span class="block text-xs text-slate-500">Fill in the memorandum details yourself.</span>
          </span>
        </button>
      </div>

      <!-- HubSpot Record ID input -->
      <div v-if="entryMode === 'hubspot'" class="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
        <label for="hubspot-deal-id" class="block text-sm font-medium text-slate-700">HubSpot Record ID</label>
        <div class="mt-1.5 flex flex-col gap-2 sm:flex-row">
          <input
            id="hubspot-deal-id"
            v-model="dealId"
            type="text"
            inputmode="numeric"
            placeholder="e.g. 63484278077"
            class="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            @keyup.enter="runHubspotImport"
          />
          <button
            type="button"
            :disabled="importing"
            class="inline-flex flex-none items-center justify-center gap-2 rounded-lg px-5 py-2 text-sm font-semibold text-white transition disabled:opacity-50"
            :class="themeClasses.btn"
            @click="runHubspotImport"
          >
            <svg v-if="importing" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
            </svg>
            {{ importing ? 'Importing…' : 'Import' }}
          </button>
        </div>
        <p class="mt-1.5 text-xs text-slate-400">We’ll pull the borrower, loan amount, account, security and refinance details from the deal — you complete the rest.</p>
        <p v-if="importMsg" class="mt-2 text-xs font-medium text-green-700">{{ importMsg }}</p>
        <p v-if="importErr" class="mt-2 text-xs text-red-600">{{ importErr }}</p>
      </div>
    </div>

    <!-- Default: Schedule 4 upload (only for Schedule-4-backed types) -->
    <template v-if="supportsSchedule4 && state.formMode === 'schedule4'">
      <div class="mt-6">
        <p class="text-sm font-medium text-slate-700">Upload Schedule 4</p>
        <p class="mt-0.5 text-xs text-slate-400">We’ll read the loan details from the Schedule 4 and build the letter.</p>

        <div
          v-if="!state.files.length"
          class="mt-3 flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition"
          :class="dragging ? 'border-blue-500 bg-blue-50/50' : 'border-slate-300'"
          @dragover.prevent="dragging = true"
          @dragleave.prevent="dragging = false"
          @drop.prevent="dragging = false; onFile($event.dataTransfer?.files)"
        >
          <svg class="h-8 w-8 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 15V3m0 0L8 7m4-4l4 4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
          </svg>
          <p class="mt-3 text-sm text-slate-500">Drag and drop the Schedule 4 here</p>
          <p class="my-1 text-xs text-slate-400">or</p>
          <button type="button" class="mt-1 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" @click="pickFile">Browse Files</button>
          <input ref="fileInput" type="file" accept=".docx,.pdf" class="hidden" @change="onFile(($event.target as HTMLInputElement).files)" />
        </div>

        <div v-else class="mt-3 flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3">
          <span class="flex items-center gap-3 text-sm text-slate-800">
            <span class="flex h-7 w-7 items-center justify-center rounded bg-blue-600 text-[10px] font-bold text-white">S4</span>
            {{ state.files[0]?.name }}
          </span>
          <div class="flex items-center gap-3">
            <span v-if="reading" class="inline-flex items-center gap-1.5 text-sm text-slate-500">
              <svg class="h-4 w-4 animate-spin text-blue-600" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              Reading…
            </span>
            <span v-else-if="state.formParsed" class="inline-flex items-center gap-1 text-sm font-medium text-green-700">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
              Read
            </span>
            <button class="text-sm font-medium text-slate-400 hover:text-red-600" @click="removeFile">Remove</button>
          </div>
        </div>

        <p v-if="readMsg" class="mt-2 text-xs text-green-700">{{ readMsg }}</p>
        <p v-if="readErr" class="mt-2 text-xs text-red-600">{{ readErr }}</p>
      </div>

      <!-- Create Manually (disabled for now) -->
      <div class="mt-6 border-t border-slate-100 pt-5">
        <button
          type="button"
          disabled
          class="cursor-not-allowed rounded-lg border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-400"
          @click="setMode('manual')"
        >
          Create Manually
        </button>
        <p class="mt-1.5 text-xs text-slate-400">Manual entry is coming soon — we’re focusing on Schedule 4 upload for now.</p>
      </div>
    </template>

    <!-- Manual entry: the input questions (for CAM, only after "Enter manually") -->
    <template v-else-if="showFields">
      <!-- Colour legend for the review borders -->
      <div class="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-500">
        <span class="inline-flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded border-2 border-red-400" />Needs a value</span>
        <span class="inline-flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded border-2 border-amber-400" />Template default — review or add detail</span>
      </div>
      <div v-for="section in sections" :key="section" class="mt-8">
        <h3 class="border-b border-slate-100 pb-2 text-base font-semibold text-slate-900">{{ section }}</h3>
        <div class="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <div
            v-for="f in fieldsIn(section)"
            :key="f.id"
            :class="f.type === 'textarea' || f.type === 'richtext' || f.type === 'signature' || f.type === 'refinance' ? 'sm:col-span-2' : ''"
          >
            <label :for="f.id" class="block text-sm font-medium text-slate-700">
              {{ f.label }} <span v-if="f.required" class="text-red-500">*</span>
            </label>

            <RefinanceList
              v-if="f.type === 'refinance'"
              v-model="state.fieldValues[f.id]"
              :placeholder="f.placeholder"
            />
            <SignaturePad
              v-else-if="f.type === 'signature'"
              v-model="state.fieldValues[f.id]"
              :placeholder="f.placeholder"
              :invalid="highlight(f)"
              class="mt-1.5"
            />
            <RichTextEditor
              v-else-if="f.type === 'richtext'"
              v-model="state.fieldValues[f.id]"
              :placeholder="f.placeholder"
              class="mt-1.5"
            />
            <textarea
              v-else-if="f.type === 'textarea'"
              :id="f.id"
              v-model="state.fieldValues[f.id]"
              :rows="f.rows ?? 2"
              :placeholder="f.placeholder"
              class="mt-1.5 block w-full rounded-lg border px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              :class="borderClass(f)"
            />
            <select
              v-else-if="f.type === 'select'"
              :id="f.id"
              v-model="state.fieldValues[f.id]"
              class="mt-1.5 block w-full rounded-lg border bg-white px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              :class="borderClass(f)"
            >
              <option v-for="opt in f.options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
            <input
              v-else
              :id="f.id"
              v-model="state.fieldValues[f.id]"
              :type="f.type === 'email' ? 'email' : 'text'"
              :placeholder="f.placeholder"
              class="mt-1.5 block w-full rounded-lg border px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              :class="borderClass(f)"
            />

            <p v-if="f.help" class="mt-1 text-xs text-slate-400">{{ f.help }}</p>
            <p v-if="showErrors && missing(f)" class="mt-1 text-xs text-red-600">This field is required.</p>
          </div>
        </div>
      </div>
      <button v-if="supportsSchedule4" type="button" class="mt-6 text-sm font-medium text-blue-600 hover:text-blue-700" @click="setMode('schedule4')">
        ← Use Schedule 4 upload instead
      </button>
    </template>

    <!-- Validation hint for Schedule 4 mode (fields are hidden) -->
    <p v-if="showErrors && supportsSchedule4 && !state.formParsed && state.formMode === 'schedule4'" class="mt-4 text-sm text-red-600">
      Please upload a Schedule 4 before continuing.
    </p>

    <div v-if="showFields" class="mt-8 flex items-center justify-end">
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-white transition"
        :class="themeClasses.btn"
        @click="onNext"
      >
        Next: Preview
      </button>
    </div>
  </div>
</template>
