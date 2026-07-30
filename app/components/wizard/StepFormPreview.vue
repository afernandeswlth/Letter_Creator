<script setup lang="ts">
const { state, currentType, formFilename, back, next } = useLetterWizard()
const { formPreview, downloadFormPdf } = useLetterApi()

const pages = ref<string[]>([])
const loading = ref(false)
const error = ref('')
const downloading = ref(false)

async function load() {
  if (!currentType.value) return
  loading.value = true
  error.value = ''
  try {
    pages.value = await formPreview(currentType.value.engine, state.value.brand, state.value.fieldValues)
  } catch (e) {
    error.value = `Could not render the letter. ${(e as Error).message}`
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function onDownload() {
  if (!currentType.value) return
  downloading.value = true
  try {
    await downloadFormPdf(currentType.value.engine, state.value.brand, state.value.fieldValues, formFilename.value)
  } finally {
    downloading.value = false
  }
}
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white p-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h2 class="text-lg font-semibold text-slate-900">Preview</h2>
        <p class="mt-1 text-sm text-slate-500">Review the letter before saving and sending.</p>
      </div>
      <button
        type="button"
        class="inline-flex flex-none items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-40"
        :disabled="downloading || loading"
        @click="onDownload"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 3v12m0 0l-4-4m4 4l4-4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
        </svg>
        {{ downloading ? 'Preparing…' : 'Download PDF' }}
      </button>
    </div>

    <div class="relative mt-5 max-h-[75vh] overflow-y-auto rounded-xl border border-slate-200 bg-slate-200/70 p-4 sm:p-6">
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
      <div v-else class="mx-auto flex max-w-3xl flex-col gap-4">
        <img
          v-for="(page, i) in pages"
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
