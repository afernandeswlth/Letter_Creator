<script setup lang="ts">
import { LETTER_TYPES } from '~/utils/letterTypes'
import type { BrandId, LetterTypeId } from '~/types'

const { downloadFormPdf } = useLetterApi()

// WLTH (lucide) icon per letter type.
const TYPE_ICON: Record<LetterTypeId, string> = {
  welcome: 'mail',
  approval: 'file-check',
  commencement: 'building-2',
  'pre-approval': 'user',
  'conditional-approval': 'clipboard-check',
  'credit-approval-memorandum': 'file-text',
  discharge: 'shield-check',
  custom: 'square-pen',
}

interface Row { id: LetterTypeId; word: boolean; pdf: boolean; pdfStatic?: boolean }
interface Group { name: string; icon: string; theme: 'blue' | 'green' | 'purple'; rows: Row[] }
// word = a source .docx is hosted; pdf = a blank PDF can be rendered by the engine.
const GROUPS: Group[] = [
  { name: 'Credit Team', icon: 'shield', theme: 'blue', rows: [
    { id: 'pre-approval', word: true, pdf: true },
    { id: 'conditional-approval', word: true, pdf: true },
    { id: 'approval', word: true, pdf: true },
    { id: 'credit-approval-memorandum', word: true, pdf: true },
  ] },
  { name: 'Customer Service Team', icon: 'users', theme: 'green', rows: [
    { id: 'welcome', word: true, pdf: true, pdfStatic: true },
    { id: 'commencement', word: true, pdf: true },
    { id: 'discharge', word: true, pdf: true },
  ] },
  { name: 'All Teams', icon: 'square-pen', theme: 'purple', rows: [
    { id: 'custom', word: true, pdf: true },
  ] },
]
const THEME = {
  blue: { chip: 'bg-blue-100 text-blue-600', title: 'text-blue-700' },
  green: { chip: 'bg-emerald-100 text-emerald-600', title: 'text-emerald-700' },
  purple: { chip: 'bg-violet-100 text-violet-600', title: 'text-violet-700' },
} as const
const BRANDS: { id: BrandId; label: string; suffix: string }[] = [
  { id: 'wlth', label: 'WLTH', suffix: 'wlth' },
  { id: 'mortgage-mart', label: 'Mortgage Mart', suffix: 'mma' },
]

const busy = ref('')
async function onPdf(id: LetterTypeId, brand: BrandId, brandLabel: string) {
  busy.value = `${id}-${brand}`
  try {
    await downloadFormPdf(LETTER_TYPES[id].engine, brand, {}, `${brandLabel} ${LETTER_TYPES[id].label} Template`)
  } finally {
    busy.value = ''
  }
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-slate-900">Templates</h1>
    <p class="mt-1 text-sm text-slate-500">Download a blank template for each letter — as an editable Word document or a PDF.</p>

    <div v-for="g in GROUPS" :key="g.name" class="mt-8">
      <div class="flex items-center gap-2.5">
        <span class="flex h-8 w-8 items-center justify-center rounded-lg" :class="THEME[g.theme].chip">
          <WIcon :name="g.icon" class="h-5 w-5" />
        </span>
        <h2 class="text-base font-semibold" :class="THEME[g.theme].title">{{ g.name }}</h2>
      </div>

      <div class="mt-3 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div v-for="row in g.rows" :key="row.id" class="rounded-xl border border-slate-200 bg-white p-5">
          <div class="flex items-center gap-3">
            <WIcon :name="TYPE_ICON[row.id]" class="h-5 w-5 flex-none text-slate-500" />
            <h3 class="text-sm font-semibold text-slate-900">{{ LETTER_TYPES[row.id].label }}</h3>
          </div>

          <div class="mt-4 space-y-3">
            <div v-for="b in BRANDS" :key="b.id">
              <p class="text-xs font-medium text-slate-500">{{ b.label }}</p>
              <div class="mt-1.5 flex flex-wrap items-center gap-2">
                <a
                  v-if="row.word"
                  :href="`/letter-templates/${row.id}-${b.suffix}.docx`"
                  download
                  class="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  <WIcon name="file-text" class="h-4 w-4 text-blue-600" /> Word
                </a>
                <span v-else class="text-xs text-slate-400">Word coming soon</span>

                <a
                  v-if="row.pdf && row.pdfStatic"
                  :href="`/letter-templates/${row.id}-${b.suffix}.pdf`"
                  download
                  class="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  <WIcon name="file-check" class="h-4 w-4 text-rose-500" /> PDF
                </a>
                <button
                  v-else-if="row.pdf"
                  type="button"
                  :disabled="busy === `${row.id}-${b.id}`"
                  class="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-40"
                  @click="onPdf(row.id, b.id, b.label)"
                >
                  <WIcon name="file-check" class="h-4 w-4 text-rose-500" /> {{ busy === `${row.id}-${b.id}` ? 'Preparing…' : 'PDF' }}
                </button>
                <span v-else class="text-xs text-slate-400">PDF coming soon</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
