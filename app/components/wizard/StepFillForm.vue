<script setup lang="ts">
import { BRAND_LIST } from '~/utils/brands'
import type { BrandId, LetterTypeField } from '~/types'

const { state, currentType, setBrand, next } = useLetterWizard()
const { parseFormSource } = useLetterApi()

const showErrors = ref(false)

const today = new Date().toLocaleDateString('en-GB') // dd/mm/yyyy

const fields = computed<LetterTypeField[]>(() => currentType.value?.fields ?? [])

// Ordered, unique section names.
const sections = computed(() => {
  const seen: string[] = []
  for (const f of fields.value) {
    const s = f.section ?? 'Details'
    if (!seen.includes(s)) seen.push(s)
  }
  return seen
})
const fieldsIn = (section: string) => fields.value.filter((f) => (f.section ?? 'Details') === section)

// Seed defaults (and blanks so the keys are reactive) once.
function seedDefaults() {
  for (const f of fields.value) {
    const cur = state.value.fieldValues[f.id]
    if (cur == null || cur === '') {
      state.value.fieldValues[f.id] = f.default ?? (f.type === 'date' ? today : '')
    }
  }
}
onMounted(seedDefaults)

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
}
function removeFile() {
  state.value.files = []
  readMsg.value = ''
}

async function readSchedule4() {
  if (!currentType.value || !state.value.files.length) return
  reading.value = true
  readErr.value = ''
  readMsg.value = ''
  try {
    const values = await parseFormSource(currentType.value.engine, state.value.brand, state.value.files[0]!)
    const keys = Object.keys(values).filter((k) => values[k])
    for (const k of keys) state.value.fieldValues[k] = values[k]!
    readMsg.value = keys.length
      ? `Read ${keys.length} field${keys.length === 1 ? '' : 's'} from the Schedule 4 — please review below.`
      : 'Uploaded. No fields could be read automatically yet — please complete the details below.'
  } catch (e) {
    readErr.value = `Could not read the Schedule 4. ${(e as Error).message}`
  } finally {
    reading.value = false
  }
}

function setMode(mode: 'manual' | 'schedule4') {
  state.value.formMode = mode
}

function onNext() {
  showErrors.value = true
  if (isValid.value) next()
}
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white p-6">
    <h2 class="text-lg font-semibold text-slate-900">Enter Details</h2>
    <p class="mt-1 text-sm text-slate-500">
      Choose the brand, then create the letter manually or auto-fill it from a Schedule 4.
    </p>

    <!-- Brand -->
    <div class="mt-6">
      <p class="text-sm font-medium text-slate-700">Brand</p>
      <div class="mt-2 grid grid-cols-2 gap-3 sm:max-w-lg">
        <button
          v-for="brand in BRAND_LIST"
          :key="brand.id"
          type="button"
          class="flex h-16 items-center justify-center rounded-lg border transition"
          :class="state.brand === brand.id ? 'border-blue-600 bg-blue-50 ring-1 ring-blue-600' : 'border-slate-200 bg-white hover:border-slate-300'"
          @click="setBrand(brand.id as BrandId)"
        >
          <img :src="brand.logo" :alt="brand.name" class="w-auto object-contain" :class="brand.id === 'wlth' ? 'max-h-5' : 'max-h-8'" />
        </button>
      </div>
    </div>

    <!-- Mode: manual vs Schedule 4 upload -->
    <div class="mt-6">
      <p class="text-sm font-medium text-slate-700">How do you want to create it?</p>
      <div class="mt-2 grid grid-cols-1 gap-3 sm:max-w-lg sm:grid-cols-2">
        <button
          type="button"
          class="rounded-lg border px-4 py-3 text-left transition"
          :class="state.formMode === 'manual' ? 'border-blue-600 bg-blue-50 ring-1 ring-blue-600' : 'border-slate-200 hover:border-slate-300'"
          @click="setMode('manual')"
        >
          <span class="block text-sm font-semibold text-slate-900">Manually Create</span>
          <span class="mt-0.5 block text-xs text-slate-500">Type the loan details in by hand.</span>
        </button>
        <button
          type="button"
          class="rounded-lg border px-4 py-3 text-left transition"
          :class="state.formMode === 'schedule4' ? 'border-blue-600 bg-blue-50 ring-1 ring-blue-600' : 'border-slate-200 hover:border-slate-300'"
          @click="setMode('schedule4')"
        >
          <span class="block text-sm font-semibold text-slate-900">Upload Schedule 4</span>
          <span class="mt-0.5 block text-xs text-slate-500">Auto-fill from the Schedule 4 document.</span>
        </button>
      </div>
    </div>

    <!-- Schedule 4 upload -->
    <div v-if="state.formMode === 'schedule4'" class="mt-5">
      <div
        v-if="!state.files.length"
        class="flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-8 text-center transition"
        :class="dragging ? 'border-blue-500 bg-blue-50/50' : 'border-slate-300'"
        @dragover.prevent="dragging = true"
        @dragleave.prevent="dragging = false"
        @drop.prevent="dragging = false; onFile($event.dataTransfer?.files)"
      >
        <svg class="h-7 w-7 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 15V3m0 0L8 7m4-4l4 4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
        </svg>
        <p class="mt-2 text-sm text-slate-500">Drag and drop the Schedule 4 here</p>
        <p class="my-1 text-xs text-slate-400">or</p>
        <button type="button" class="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" @click="pickFile">Browse Files</button>
        <input ref="fileInput" type="file" accept=".docx,.pdf" class="hidden" @change="onFile(($event.target as HTMLInputElement).files)" />
      </div>

      <div v-else class="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3">
        <span class="flex items-center gap-3 text-sm text-slate-800">
          <span class="flex h-7 w-7 items-center justify-center rounded bg-blue-600 text-[10px] font-bold text-white">S4</span>
          {{ state.files[0]?.name }}
        </span>
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-40"
            :disabled="reading"
            @click="readSchedule4"
          >
            {{ reading ? 'Reading…' : 'Read Schedule 4' }}
          </button>
          <button class="text-sm font-medium text-slate-400 hover:text-red-600" @click="removeFile">Remove</button>
        </div>
      </div>

      <p v-if="readMsg" class="mt-2 text-xs text-green-700">{{ readMsg }}</p>
      <p v-if="readErr" class="mt-2 text-xs text-red-600">{{ readErr }}</p>
    </div>

    <!-- Field sections (shown for both modes; Schedule 4 pre-fills them for review) -->
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
            rows="2"
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

    <div class="mt-8 flex items-center justify-end">
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700"
        @click="onNext"
      >
        Next: Preview
      </button>
    </div>
  </div>
</template>
