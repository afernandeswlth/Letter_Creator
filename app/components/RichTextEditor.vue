<script setup lang="ts">
/**
 * A lightweight WYSIWYG editor for letter body text — bold, italic, underline,
 * font size and text colour — with no external dependencies. It edits a
 * `contenteditable` region and emits the region's HTML via v-model.
 *
 * The HTML it produces (using <b>/<i>/<u> and <font size color> tags, the
 * default output of execCommand) is converted to reportlab paragraph markup in
 * engine/custom_letter.py, so the PDF preview and download match what's typed.
 */
const props = defineProps<{
  modelValue: string
  placeholder?: string
  minHeight?: string
}>()
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>()

const el = ref<HTMLElement | null>(null)
const focused = ref(false)

// A plain-text value (e.g. a field's default, or a HubSpot import) is shown with
// its line breaks preserved; HTML is used as-is.
function toDisplayHtml(v: string): string {
  if (!v) return ''
  // Only a plain-text default/import (which contains real newlines) is escaped and
  // given <br>s. Editor HTML has no raw newlines and must be returned untouched —
  // escaping it re-escapes entities like &nbsp; to &amp;nbsp; on every keystroke.
  if (!v.includes('\n')) return v
  return v.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
}

// Keep the DOM in sync with the model without clobbering the caret while typing.
function setHtml(v: string) {
  const html = toDisplayHtml(v || '')
  if (el.value && el.value.innerHTML !== html) el.value.innerHTML = html
}
onMounted(() => setHtml(props.modelValue))
watch(
  () => props.modelValue,
  (v) => {
    if (!focused.value) setHtml(v)
  },
)

function sync() {
  emit('update:modelValue', el.value?.innerHTML ?? '')
}

function cmd(command: string, value?: string) {
  el.value?.focus()
  // execCommand is deprecated but still supported everywhere and keeps this
  // component dependency-free; default output is <b>/<i>/<u>/<font> tags.
  document.execCommand(command, false, value)
  sync()
}

// Tab / Shift-Tab nests and un-nests list items (and indents plain lines).
function onKey(e: KeyboardEvent) {
  if (e.key === 'Tab') {
    e.preventDefault()
    document.execCommand(e.shiftKey ? 'outdent' : 'indent')
    sync()
  }
}

const isEmpty = computed(() => {
  const v = (props.modelValue || '').replace(/<[^>]+>/g, '').replace(/&nbsp;|\s| /g, '')
  return v === ''
})

// Font size in points; the value is the HTML <font size="1-7"> scale the engine
// maps back to points (engine/richtext.py `_FONT_PT`).
const SIZES = [
  { label: '9', v: '2' },
  { label: '10', v: '3' },
  { label: '11', v: '4' },
  { label: '12', v: '5' },
  { label: '14', v: '6' },
  { label: '18', v: '7' },
]
const COLORS = [
  { name: 'Black', hex: '#111827' },
  { name: 'WLTH Blue', hex: '#1E63E9' },
  { name: 'Red', hex: '#DC2626' },
  { name: 'Green', hex: '#059669' },
  { name: 'Amber', hex: '#D97706' },
  { name: 'Purple', hex: '#7C3AED' },
]

const sizeOpen = ref(false)
const colorOpen = ref(false)
function pickSize(v: string) {
  cmd('fontSize', v)
  sizeOpen.value = false
}
function pickColor(hex: string) {
  cmd('foreColor', hex)
  colorOpen.value = false
}
</script>

<template>
  <div
    class="rounded-lg border bg-white shadow-sm transition"
    :class="focused ? 'border-blue-500 ring-1 ring-blue-500' : 'border-slate-300'"
  >
    <!-- Toolbar -->
    <div class="flex flex-wrap items-center gap-1 border-b border-slate-200 px-2 py-1.5">
      <button type="button" title="Bold" class="tb-btn font-bold" @mousedown.prevent @click="cmd('bold')">B</button>
      <button type="button" title="Italic" class="tb-btn italic" @mousedown.prevent @click="cmd('italic')">I</button>
      <button type="button" title="Underline" class="tb-btn underline" @mousedown.prevent @click="cmd('underline')">U</button>

      <span class="mx-1 h-5 w-px bg-slate-200" />

      <!-- Text size -->
      <div class="relative">
        <button type="button" title="Text size" class="tb-btn gap-1 px-2" @mousedown.prevent @click="sizeOpen = !sizeOpen; colorOpen = false">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7V5h16v2M9 5v14M7 19h4" /><path d="M14 13v-1h6v1M16 12v7M15 19h2" /></svg>
          <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6" /></svg>
        </button>
        <div v-if="sizeOpen" class="absolute left-0 top-full z-20 mt-1 w-36 overflow-hidden rounded-lg border border-slate-200 bg-white py-1 shadow-lg">
          <button v-for="s in SIZES" :key="s.v" type="button" class="block w-full px-3 py-1.5 text-left text-sm text-slate-700 hover:bg-slate-50" @mousedown.prevent @click="pickSize(s.v)">{{ s.label }} pt</button>
        </div>
      </div>

      <!-- Text colour -->
      <div class="relative">
        <button type="button" title="Text colour" class="tb-btn gap-1 px-2" @mousedown.prevent @click="colorOpen = !colorOpen; sizeOpen = false">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h16M7 16l5-12 5 12M8.5 12h7" /></svg>
          <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6" /></svg>
        </button>
        <div v-if="colorOpen" class="absolute left-0 top-full z-20 mt-1 grid w-40 grid-cols-3 gap-1 rounded-lg border border-slate-200 bg-white p-2 shadow-lg">
          <button v-for="c in COLORS" :key="c.hex" type="button" :title="c.name" class="flex h-7 items-center justify-center rounded-md ring-1 ring-inset ring-slate-200 transition hover:scale-105" :style="{ backgroundColor: c.hex }" @mousedown.prevent @click="pickColor(c.hex)" />
        </div>
      </div>

      <span class="mx-1 h-5 w-px bg-slate-200" />

      <button type="button" title="Bullet list" class="tb-btn px-2" @mousedown.prevent @click="cmd('insertUnorderedList')">
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 6h13M8 12h13M8 18h13" /><circle cx="3.5" cy="6" r="1.2" fill="currentColor" stroke="none" /><circle cx="3.5" cy="12" r="1.2" fill="currentColor" stroke="none" /><circle cx="3.5" cy="18" r="1.2" fill="currentColor" stroke="none" /></svg>
      </button>
      <button type="button" title="Numbered list" class="tb-btn px-2" @mousedown.prevent @click="cmd('insertOrderedList')">
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 6h11" /><path d="M10 12h11" /><path d="M10 18h11" /><path d="M4 6h1v4" /><path d="M4 10h2" /><path d="M6 18H4c0-1 2-2 2-3s-1-1.5-2-1" /></svg>
      </button>

      <span class="mx-1 h-5 w-px bg-slate-200" />

      <button type="button" title="Clear formatting" class="tb-btn px-2" @mousedown.prevent @click="cmd('removeFormat')">
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7V5h13v2M10 5l-2 14M6 19h6M15 15l6 6M21 15l-6 6" /></svg>
      </button>
    </div>

    <!-- Editable region -->
    <div class="relative">
      <div
        ref="el"
        contenteditable="true"
        role="textbox"
        aria-multiline="true"
        class="rt-body w-full overflow-y-auto px-3 py-2.5 text-sm leading-relaxed text-slate-900 outline-none"
        :style="{ minHeight: minHeight || '16rem', maxHeight: '32rem' }"
        @input="sync"
        @keydown="onKey"
        @focus="focused = true"
        @blur="focused = false; sync()"
      />
      <div v-if="isEmpty && placeholder" class="pointer-events-none absolute left-3 top-2.5 text-sm text-slate-400">{{ placeholder }}</div>
    </div>
  </div>
</template>

<style scoped>
.tb-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.9rem;
  height: 1.9rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: rgb(51 65 85);
  transition: background-color 0.15s;
}
.tb-btn:hover {
  background-color: rgb(241 245 249);
}
/* Preserve blank lines the user types between paragraphs. */
.rt-body :deep(div) {
  min-height: 1.2em;
}
/* Tailwind's preflight strips list markers/indent; restore them here so the
   bullet + numbered-list buttons show, and nest 1. → a. → i. as in the doc. */
.rt-body :deep(ul),
.rt-body :deep(ol) {
  padding-left: 1.6rem;
  margin: 0.3rem 0;
}
.rt-body :deep(ul) { list-style: disc; }
.rt-body :deep(ol) { list-style: decimal; }
.rt-body :deep(ol ol) { list-style: lower-alpha; }
.rt-body :deep(ol ol ol) { list-style: lower-roman; }
.rt-body :deep(ul ul) { list-style: circle; }
.rt-body :deep(ul ul ul) { list-style: square; }
.rt-body :deep(li) { margin: 0.14rem 0; }

</style>
