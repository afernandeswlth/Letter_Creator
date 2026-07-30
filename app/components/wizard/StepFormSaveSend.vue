<script setup lang="ts">
const { state, currentType, formFilename, back } = useLetterWizard()
const { downloadFormPdf, createFormEmailDraft } = useLetterApi()

const email = ref(state.value.fieldValues.borrowerEmail || '')
const downloading = ref(false)
const sending = ref(false)
const result = ref('')
const error = ref('')

const emailOk = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim()))

async function onDownload() {
  if (!currentType.value) return
  downloading.value = true
  try {
    await downloadFormPdf(currentType.value.engine, state.value.brand, state.value.fieldValues, formFilename.value)
  } finally {
    downloading.value = false
  }
}

async function onCreateDraft() {
  if (!currentType.value || !emailOk.value) return
  sending.value = true
  result.value = ''
  error.value = ''
  try {
    const res = await createFormEmailDraft(
      currentType.value.engine,
      state.value.brand,
      state.value.fieldValues,
      email.value.trim(),
      formFilename.value,
    )
    result.value = res.message
  } catch (e) {
    error.value = `Could not create the draft. ${(e as Error).message}`
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white p-6">
    <h2 class="text-lg font-semibold text-slate-900">Save &amp; Send</h2>
    <p class="mt-1 text-sm text-slate-500">Download the letter, or create a draft email with it attached.</p>

    <!-- Download -->
    <div class="mt-6 flex items-center justify-between rounded-xl border border-slate-200 p-4">
      <div>
        <p class="text-sm font-medium text-slate-900">{{ formFilename }}.pdf</p>
        <p class="text-xs text-slate-500">The branded {{ currentType?.label }}.</p>
      </div>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-40"
        :disabled="downloading"
        @click="onDownload"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 3v12m0 0l-4-4m4 4l4-4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
        </svg>
        {{ downloading ? 'Preparing…' : 'Download PDF' }}
      </button>
    </div>

    <!-- Email draft -->
    <div class="mt-4 rounded-xl border border-slate-200 p-4">
      <p class="text-sm font-medium text-slate-900">Create a draft email</p>
      <p class="mt-0.5 text-xs text-slate-500">Creates a draft in hello@wlth.com with the letter attached (does not send).</p>
      <div class="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center">
        <input
          v-model="email"
          type="email"
          placeholder="borrower@example.com"
          class="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:max-w-xs"
        />
        <button
          type="button"
          class="inline-flex flex-none items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-40"
          :disabled="!emailOk || sending"
          @click="onCreateDraft"
        >
          {{ sending ? 'Creating…' : 'Create Draft Email' }}
        </button>
      </div>
      <p v-if="result" class="mt-3 text-sm text-green-700">{{ result }}</p>
      <p v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</p>
    </div>

    <div class="mt-8 flex items-center justify-between">
      <button type="button" class="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="back">Back</button>
    </div>
  </div>
</template>
