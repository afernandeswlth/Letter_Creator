<script setup lang="ts">
const { state, currentType, formFilename, back, requestGoHome } = useLetterWizard()
const { downloadFormPdf } = useLetterApi()

const downloading = ref(false)

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
    <h2 class="text-lg font-semibold text-slate-900">Download</h2>
    <p class="mt-1 text-sm text-slate-500">Download the branded letter as a PDF.</p>

    <!-- Download -->
    <div class="mt-6 flex items-center justify-between rounded-xl border border-slate-200 p-4">
      <div>
        <p class="text-sm font-medium text-slate-900">{{ formFilename }}.pdf</p>
        <p class="text-xs text-slate-500">The branded {{ currentType?.label }}.</p>
      </div>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-green-700 disabled:opacity-40"
        :disabled="downloading"
        @click="onDownload"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 3v12m0 0l-4-4m4 4l4-4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
        </svg>
        {{ downloading ? 'Preparing…' : 'Download PDF' }}
      </button>
    </div>

    <div class="mt-8 flex items-center justify-between">
      <button type="button" class="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="back">Back</button>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700"
        @click="requestGoHome"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
        Done
      </button>
    </div>
  </div>
</template>
