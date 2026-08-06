<script setup lang="ts">
import type { LetterTypeField } from '~/types'

const { state, currentType, next, themeClasses } = useLetterWizard()
const { parseFormSource } = useLetterApi()

const showErrors = ref(false)

const today = new Date().toLocaleDateString('en-GB') // dd/mm/yyyy

const fields = computed<LetterTypeField[]>(() => currentType.value?.fields ?? [])

// Some form types are filled from a Schedule 4 upload (Approval); others are
// filled by hand (Custom). Manual-only types skip the upload UI entirely.
const supportsSchedule4 = computed(() => currentType.value?.source !== 'manual')

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
})

const missing = (f: LetterTypeField) => f.required && !(state.value.fieldValues[f.id] ?? '').trim()
const isValid = computed(() => fields.value.every((f) => !missing(f)))

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
      {{ supportsSchedule4 ? 'Choose the brand, then upload the Schedule 4 to auto-fill the letter.' : 'Choose the brand, then fill in the letter details.' }}
    </p>

    <!-- Brand -->
    <div class="mt-6">
      <BrandSelector />
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

    <!-- Manual entry: the input questions (only when Create Manually is chosen) -->
    <template v-else>
      <div v-for="section in sections" :key="section" class="mt-8">
        <h3 class="border-b border-slate-100 pb-2 text-base font-semibold text-slate-900">{{ section }}</h3>
        <div class="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <div
            v-for="f in fieldsIn(section)"
            :key="f.id"
            :class="f.type === 'textarea' ? 'sm:col-span-2' : ''"
          >
            <label :for="f.id" class="block text-sm font-medium text-slate-700">
              {{ f.label }} <span v-if="f.required" class="text-red-500">*</span>
            </label>

            <textarea
              v-if="f.type === 'textarea'"
              :id="f.id"
              v-model="state.fieldValues[f.id]"
              :rows="f.rows ?? 2"
              :placeholder="f.placeholder"
              class="mt-1.5 block w-full rounded-lg border px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              :class="showErrors && missing(f) ? 'border-red-400' : 'border-slate-300'"
            />
            <select
              v-else-if="f.type === 'select'"
              :id="f.id"
              v-model="state.fieldValues[f.id]"
              class="mt-1.5 block w-full rounded-lg border bg-white px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              :class="showErrors && missing(f) ? 'border-red-400' : 'border-slate-300'"
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
              :class="showErrors && missing(f) ? 'border-red-400' : 'border-slate-300'"
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

    <div class="mt-8 flex items-center justify-end">
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
