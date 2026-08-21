<script setup lang="ts">
import type { LetterTypeField } from '~/types'

const { state, currentType, back, next, themeClasses, startEditing } = useLetterWizard()
const { formPreview } = useLetterApi()

const pages = ref<string[]>([])
const loading = ref(false)     // initial render (blocks the preview)
const refreshing = ref(false)  // live update (keeps the current preview visible)
const error = ref('')
let renderSeq = 0

// Preview zoom (1 = fit). Buttons step 25%; zooming past the column scrolls.
const zoom = ref(1)
const zoomPct = computed(() => Math.round(zoom.value * 100))
function zoomIn() {
  zoom.value = Math.min(2, Math.round((zoom.value + 0.25) * 100) / 100)
}
function zoomOut() {
  zoom.value = Math.max(0.5, Math.round((zoom.value - 0.25) * 100) / 100)
}

const previewScroll = ref<HTMLElement | null>(null)
// Vertical position (0-1 of the document) of each field's section, from the
// engine — so an edit scrolls the preview to the right place.
const fieldPositions = ref<Record<string, number>>({})
let pendingScrollField: string | null = null

// Centre the edited field's section in the preview. Uses the engine-reported
// position; falls back to the field's order when none is available.
function scrollPreviewToField(fieldId: string) {
  const el = previewScroll.value
  if (!el) return
  let frac = fieldPositions.value[fieldId]
  if (frac == null) {
    const idx = fields.value.findIndex(f => f.id === fieldId)
    if (idx < 0) return
    frac = idx / Math.max(1, fields.value.length - 1)
  }
  nextTick(() => {
    const y = frac * el.scrollHeight - el.clientHeight / 2 // centre the section
    el.scrollTo({ top: Math.max(0, y), behavior: 'smooth' })
  })
}

async function renderPreview(initial = false) {
  if (!currentType.value) return
  const seq = ++renderSeq
  if (initial) loading.value = true
  else refreshing.value = true
  error.value = ''
  try {
    const r = await formPreview(currentType.value.engine, state.value.brand, state.value.fieldValues)
    if (seq === renderSeq) {
      pages.value = r.pages // latest request wins
      fieldPositions.value = r.positions
    }
  } catch (e) {
    if (seq === renderSeq) error.value = `Could not render the letter. ${(e as Error).message}`
  } finally {
    if (seq === renderSeq) {
      loading.value = false
      refreshing.value = false
      if (!initial && pendingScrollField) {
        scrollPreviewToField(pendingScrollField)
        pendingScrollField = null
      }
    }
  }
}

// --- Inline edit of every letter field, applied live --------------------------
// The editable fields (and their order/sections) come straight from the letter
// type's registry, so the editor mirrors the letter. Edits flow to the letter
// values immediately and re-render the preview (debounced) — no Apply step.
const fields = computed<LetterTypeField[]>(() => currentType.value?.fields ?? [])
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
  return !c || (draft[c.field] ?? '') === c.equals
}
const fieldsIn = (section: string) =>
  fields.value.filter((f) => (f.section ?? 'Details') === section && isVisible(f))

// Review borders — only when the form was prefilled from a HubSpot deal: red on
// empty fields, amber on fields still holding their template default.
// A few fields opt out: Mortgage Manager (always WLTH) and Additional Notes
// (optional) never get a review border.
const NO_REVIEW = new Set(['mortgageManager', 'additionalNotes'])
function tableEmpty(v: string) {
  if (!v) return true
  try {
    const a = JSON.parse(v)
    if (Array.isArray(a)) {
      return a.every(row =>
        Array.isArray(row) ? row.every(c => !String(c).trim()) : !String(row).trim())
    }
  } catch { /* not JSON */ }
  return !v.trim()
}
function fieldEmpty(f: LetterTypeField) {
  const v = draft[f.id] ?? ''
  if (f.type === 'signature') return !v
  if (f.type === 'table') return tableEmpty(v)
  if (f.type === 'richtext') return v.replace(/<[^>]+>/g, '').replace(/&nbsp;|\s/g, '') === ''
  return v.trim() === ''
}
// Review borders fire whenever the form was auto-prefilled from a source —
// a HubSpot deal (CAM) or a Schedule 4 upload (Formal Approval).
const scheduleImported = computed(
  () => !!state.value.formParsed && currentType.value?.source === 'schedule4',
)
const sourcePrefilled = computed(() => state.value.hubspotImported || scheduleImported.value)
function reviewMark(f: LetterTypeField): 'red' | 'amber' | null {
  if (!sourcePrefilled.value || NO_REVIEW.has(f.id)) return null
  if (fieldEmpty(f)) {
    // A Schedule 4 import flags only the mandatory fields the assessor still
    // has to enter by hand (the letter can go out without the optional ones);
    // a HubSpot import flags every empty field, as before.
    if (scheduleImported.value && !state.value.hubspotImported) return f.required ? 'red' : null
    return 'red'
  }
  if (f.default && (draft[f.id] ?? '') === f.default) return 'amber'
  return null
}
const borderClass = (f: LetterTypeField) =>
  reviewMark(f) === 'red' ? 'border-red-400' : reviewMark(f) === 'amber' ? 'border-amber-400' : 'border-slate-300'
const ringClass = (f: LetterTypeField) =>
  reviewMark(f) === 'red' ? 'ring-1 ring-red-400' : reviewMark(f) === 'amber' ? 'ring-1 ring-amber-400' : ''

const editing = ref(false)
const draft = reactive<Record<string, string>>({})

let skipWatch = false
function syncDraft() {
  skipWatch = true // seeding the draft shouldn't count as an edit
  for (const f of fields.value) draft[f.id] = state.value.fieldValues[f.id] ?? ''
  nextTick(() => { skipWatch = false })
}
function openEditor() {
  syncDraft()
  editing.value = true
}
function toggleEditor() {
  if (editing.value) editing.value = false
  else openEditor()
}

// Live: push edits to the letter values and re-render the preview, debounced so
// the engine isn't hit on every keystroke.
let debounceT: ReturnType<typeof setTimeout> | undefined
watch(
  draft,
  () => {
    if (skipWatch) return
    // Remember which field changed so the preview can jump to it after re-render.
    const changed = fields.value.find(f => (state.value.fieldValues[f.id] ?? '') !== (draft[f.id] ?? ''))
    if (changed) pendingScrollField = changed.id
    for (const f of fields.value) state.value.fieldValues[f.id] = draft[f.id] ?? ''
    clearTimeout(debounceT)
    debounceT = setTimeout(() => renderPreview(false), 600)
  },
  { deep: true },
)

onMounted(async () => {
  await renderPreview(true)
  // A HubSpot import jumps straight here with the editor open.
  if (startEditing.value) {
    startEditing.value = false
    openEditor()
  }
})
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white p-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h2 class="text-lg font-semibold text-slate-900">Preview</h2>
        <p class="mt-1 text-sm text-slate-500">Review the letter before saving and sending.</p>
      </div>
      <div class="flex flex-none items-center gap-2">
        <!-- Zoom -->
        <div class="flex items-center gap-0.5 rounded-lg border border-slate-200 bg-white p-0.5">
          <button type="button" title="Zoom out" :disabled="zoom <= 0.5" class="flex h-8 w-8 items-center justify-center rounded-md text-slate-600 transition hover:bg-slate-100 disabled:opacity-40" @click="zoomOut">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14" /></svg>
          </button>
          <span class="w-11 text-center text-xs font-medium tabular-nums text-slate-600">{{ zoomPct }}%</span>
          <button type="button" title="Zoom in" :disabled="zoom >= 2" class="flex h-8 w-8 items-center justify-center rounded-md text-slate-600 transition hover:bg-slate-100 disabled:opacity-40" @click="zoomIn">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14" /></svg>
          </button>
        </div>
        <button
          type="button"
          class="inline-flex items-center justify-center gap-2 rounded-lg border border-transparent px-4 py-2 text-sm font-semibold text-white transition"
          :class="editing ? 'bg-red-500 hover:bg-red-500' : 'bg-red-400 hover:bg-red-500'"
          @click="toggleEditor"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
          {{ editing ? 'Close editor' : 'Edit' }}
        </button>
      </div>
    </div>

    <!-- Two columns while editing: the preview stays put on the left and the
         "Edit letter fields" panel scrolls on its own on the right. -->
    <div class="mt-5 flex flex-col gap-6 lg:flex-row lg:items-start">
      <!-- Preview (left) — takes the remaining width so the PDF is large -->
      <div :class="editing ? 'lg:sticky lg:top-6 lg:flex-1 lg:min-w-0 lg:self-start' : 'w-full'">
        <div ref="previewScroll" class="relative max-h-[82vh] overflow-auto rounded-xl border border-slate-200 bg-slate-200/70 p-4 sm:p-6">
          <div v-if="loading" class="flex items-center justify-center py-24">
            <div class="flex items-center gap-2 text-sm text-slate-500">
              <svg class="h-5 w-5 animate-spin text-blue-600" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              Rendering letter…
            </div>
          </div>
          <p v-else-if="error" class="py-24 text-center text-sm text-red-600">{{ error }}</p>
          <div
            v-else
            class="mx-auto flex flex-col gap-4"
            :style="{ width: `${zoom * 56}rem`, maxWidth: zoom <= 1 ? '100%' : 'none' }"
          >
            <img
              v-for="(page, i) in pages"
              :key="i"
              :src="page"
              :alt="`Page ${i + 1}`"
              class="w-full rounded-md bg-white shadow ring-1 ring-slate-300"
            />
          </div>
          <!-- Live-update badge: the previous preview stays visible while it re-renders -->
          <div v-if="refreshing && !loading" class="pointer-events-none sticky bottom-2 mx-auto flex w-max items-center gap-1.5 rounded-full bg-white/95 px-3 py-1 text-xs font-medium text-slate-600 shadow ring-1 ring-slate-200">
            <svg class="h-3.5 w-3.5 animate-spin text-blue-600" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
            </svg>
            Updating preview…
          </div>
        </div>
      </div>

      <!-- Inline editor (right): its own scroll, header + apply bar pinned -->
      <div
        v-if="editing"
        class="flex max-h-[82vh] flex-col overflow-hidden rounded-xl border border-slate-200 bg-slate-50/70 lg:w-[380px] lg:flex-none"
      >
        <div class="flex flex-none items-center justify-between border-b border-slate-200 px-5 py-3">
          <h3 class="text-sm font-semibold text-slate-900">Edit letter fields</h3>
          <button type="button" class="text-slate-400 transition hover:text-slate-600" aria-label="Close editor" @click="editing = false">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6l12 12M18 6L6 18" /></svg>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto px-5 py-4">
          <!-- Colour legend for the review borders (HubSpot import only) -->
          <div v-if="sourcePrefilled" class="mb-2 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-slate-500">
            <span class="inline-flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded border-2 border-red-400" />Needs a value</span>
            <span class="inline-flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded border-2 border-amber-400" />Template default — review</span>
          </div>
          <div v-for="section in sections" :key="section" class="mt-5 first:mt-0">
            <h4 class="border-b border-slate-200 pb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{{ section }}</h4>
            <div class="mt-3 grid grid-cols-1 gap-4">
              <div v-for="f in fieldsIn(section)" :key="f.id">
                <label :for="`edit-${f.id}`" class="block text-sm font-medium text-slate-700">{{ f.label }}</label>

                <TableInput
                  v-if="f.type === 'table'"
                  v-model="draft[f.id]"
                  :columns="f.columns || []"
                  :row-label-prefix="f.rowLabelPrefix"
                  :flat="f.flat"
                  :show-header="f.showHeader"
                  :max-rows="f.maxRows"
                  :class="ringClass(f)"
                />
                <SignaturePad
                  v-else-if="f.type === 'signature'"
                  v-model="draft[f.id]"
                  :placeholder="f.placeholder"
                  :invalid="reviewMark(f) === 'red'"
                  class="mt-1.5"
                />
                <RichTextEditor
                  v-else-if="f.type === 'richtext'"
                  v-model="draft[f.id]"
                  :placeholder="f.placeholder"
                  :min-height="f.rows ? `${Math.max(4, f.rows) * 1.5}rem` : undefined"
                  class="mt-1.5 rounded-lg"
                  :class="ringClass(f)"
                />
                <textarea
                  v-else-if="f.type === 'textarea'"
                  :id="`edit-${f.id}`"
                  v-model="draft[f.id]"
                  :rows="f.rows ?? (f.id === 'specialConditions' ? 6 : 2)"
                  :placeholder="f.placeholder"
                  class="mt-1.5 block w-full rounded-lg border px-3 py-2 text-sm leading-relaxed shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  :class="borderClass(f)"
                />
                <select
                  v-else-if="f.type === 'select'"
                  :id="`edit-${f.id}`"
                  v-model="draft[f.id]"
                  class="mt-1.5 block w-full rounded-lg border bg-white px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  :class="borderClass(f)"
                >
                  <option v-for="opt in f.options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
                <input
                  v-else
                  :id="`edit-${f.id}`"
                  v-model="draft[f.id]"
                  :type="f.type === 'email' ? 'email' : 'text'"
                  :placeholder="f.placeholder"
                  class="mt-1.5 block w-full rounded-lg border px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  :class="borderClass(f)"
                />

                <p v-if="f.help" class="mt-1 text-xs text-slate-400">{{ f.help }}</p>
                <p v-if="f.required && reviewMark(f) === 'red'" class="mt-1 text-xs font-medium text-red-600">Required — manual input.</p>
              </div>
            </div>
          </div>
        </div>

        <div class="flex flex-none items-center gap-2 border-t border-slate-200 bg-white/60 px-5 py-2.5 text-xs font-medium text-slate-500">
          <svg v-if="refreshing" class="h-3.5 w-3.5 animate-spin text-blue-600" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
          <svg v-else class="h-3.5 w-3.5 text-green-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
          {{ refreshing ? 'Updating preview…' : 'Changes apply as you type' }}
        </div>
      </div>
    </div>

    <div class="mt-8 flex items-center justify-between">
      <button type="button" class="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="back">Back</button>
      <button type="button" class="inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-white transition" :class="themeClasses.btn" @click="next">Next: Download</button>
    </div>
  </div>
</template>
