<script setup lang="ts">
const { state, back, next } = useLetterWizard()
const { previewPages, downloadPdf } = useLetterApi()

const selected = ref(0)
const current = computed(() => state.value.rendered[selected.value])
const downloading = ref(false)

// PDF preview rendered as page images, cached per party index.
const pagesByParty = ref<Record<number, string[]>>({})
const loadingPdf = ref(false)
const pdfError = ref('')
const currentPages = computed(() => pagesByParty.value[selected.value] ?? [])

function fileBaseFor(name: string): string {
  const label = state.value.brand === 'mortgage-mart' ? 'MMA' : 'WLTH'
  const person = name.replace(/^(mr|mrs|ms|miss|dr)\.?\s+/i, '') // drop the title
  return `${label} Welcome Letter - ${person}`
}

async function loadPreview(index: number) {
  if (pagesByParty.value[index] || !state.value.rendered[index]) return
  loadingPdf.value = true
  pdfError.value = ''
  try {
    pagesByParty.value[index] = await previewPages(
      state.value.files,
      state.value.brand,
      state.value.ddBsb,
      state.value.ddAccount,
      index,
    )
  } catch (e) {
    pdfError.value = `Could not render the letter. ${(e as Error).message}`
  } finally {
    loadingPdf.value = false
  }
}

watch(selected, (i) => loadPreview(i), { immediate: true })

async function onDownload() {
  if (!current.value) return
  downloading.value = true
  try {
    await downloadPdf(
      state.value.files,
      state.value.brand,
      state.value.ddBsb,
      state.value.ddAccount,
      selected.value,
      fileBaseFor(current.value.name),
    )
  } finally {
    downloading.value = false
  }
}
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white p-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h2 class="text-lg font-semibold text-slate-900">3. Preview</h2>
        <p class="mt-1 text-sm text-slate-500">
          One branded letter per party. Review each before saving and sending.
        </p>
      </div>
      <button
        type="button"
        class="inline-flex flex-none items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-40"
        :disabled="downloading || !current"
        @click="onDownload"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 3v12m0 0l-4-4m4 4l4-4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
        </svg>
        {{ downloading ? 'Preparing…' : 'Download PDF' }}
      </button>
    </div>

    <!-- Party selector -->
    <div class="mt-5 flex flex-wrap gap-2">
      <button
        v-for="(p, i) in state.rendered"
        :key="p.name"
        type="button"
        class="rounded-lg border px-3 py-1.5 text-sm font-medium transition"
        :class="i === selected ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-slate-200 text-slate-600 hover:border-slate-300'"
        @click="selected = i"
      >
        <span class="mr-1 text-xs" :class="p.isEntity ? 'text-teal-600' : 'text-slate-400'">{{ p.role }}</span>
        {{ p.name.length > 28 ? p.name.slice(0, 28) + '…' : p.name }}
      </button>
    </div>

    <!-- Embedded PDF preview (rendered page images) -->
    <div class="relative mt-5 max-h-[75vh] overflow-y-auto rounded-xl border border-slate-200 bg-slate-200/70 p-4 sm:p-6">
      <div v-if="loadingPdf" class="flex items-center justify-center py-24">
        <div class="flex items-center gap-2 text-sm text-slate-500">
          <svg class="h-5 w-5 animate-spin text-blue-600" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
          Rendering letter…
        </div>
      </div>
      <p v-else-if="pdfError" class="py-24 text-center text-sm text-red-600">{{ pdfError }}</p>
      <div v-else class="mx-auto flex max-w-3xl flex-col gap-4">
        <img
          v-for="(page, i) in currentPages"
          :key="i"
          :src="page"
          :alt="`Page ${i + 1}`"
          class="w-full rounded-md bg-white shadow ring-1 ring-slate-300"
        />
      </div>
    </div>

    <div class="mt-8 flex items-center justify-between">
      <button type="button" class="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="back">Back</button>
      <button type="button" class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700" @click="next">Next: Save &amp; Send</button>
    </div>
  </div>
</template>
