<script setup lang="ts">
const { state, currentType, formFilename, back, requestGoHome, themeClasses } = useLetterWizard()
const { downloadFormPdf, fetchFormPdfBlob, createFormEmailDraft } = useLetterApi()

// Build the PDF blob(s) for the "Add to Drive" button (lazily, on click).
async function driveFiles() {
  if (!currentType.value) return []
  const blob = await fetchFormPdfBlob(currentType.value.engine, state.value.brand, state.value.fieldValues, formFilename.value)
  return [{ name: `${formFilename.value}.pdf`, blob }]
}

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

// --- Email draft (only when the letter type opts in) -----------------------
const emailCfg = computed(() => currentType.value?.email ?? null)
const toEmail = ref('')
const ccEmails = ref<string[]>([]) // one per ccLabels
watchEffect(() => {
  if (emailCfg.value) ccEmails.value = (emailCfg.value.ccLabels ?? []).map(() => '')
})

const isEmail = (s: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s.trim())
const canSend = computed(() => isEmail(toEmail.value))

const sending = ref(false)
const emailResult = ref('')
const emailError = ref('')

async function onCreateDraft() {
  if (!currentType.value || !canSend.value) return
  sending.value = true
  emailResult.value = ''
  emailError.value = ''
  try {
    // Each Cc field may hold several addresses (e.g. both borrowers), so split
    // on commas/semicolons before validating — otherwise a multi-address field
    // fails the single-email check and gets dropped.
    const cc = ccEmails.value
      .flatMap((e) => e.split(/[,;]/))
      .map((e) => e.trim())
      .filter(isEmail)
      .join(', ')
    const res = await createFormEmailDraft(
      currentType.value.engine,
      state.value.brand,
      state.value.fieldValues,
      toEmail.value.trim(),
      formFilename.value,
      cc || undefined,
    )
    emailResult.value = res.message
  } catch (e) {
    emailError.value = `Could not create the draft. ${(e as Error).message}`
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white p-6">
    <h2 class="text-lg font-semibold text-slate-900">Download</h2>
    <p class="mt-1 text-sm text-slate-500">Download the branded letter as a PDF{{ emailCfg ? ', or email it to the builder.' : '.' }}</p>

    <!-- Download -->
    <div class="mt-6 flex flex-col gap-3 rounded-xl border border-slate-200 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p class="text-sm font-medium text-slate-900">{{ formFilename }}.pdf</p>
        <p class="text-xs text-slate-500">The branded {{ currentType?.label }}.</p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <AddToDriveButton :files="driveFiles" :count="1" />
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
    </div>

    <!-- Email the builder (opt-in per letter type) -->
    <div v-if="emailCfg" class="mt-4 rounded-xl border border-slate-200 p-4">
      <p class="text-sm font-medium text-slate-900">Email the letter</p>
      <p class="mt-0.5 text-xs text-slate-500">
        Creates a draft in <span class="font-medium text-slate-700">{{ emailCfg.from }}</span> with the letter and Progress Payment Guidelines attached — the builder as the recipient, the broker and borrowers CC’d. Review and send it from Gmail.
      </p>

      <div class="mt-3 space-y-3">
        <div>
          <label class="block text-xs font-medium text-slate-600">{{ emailCfg.toLabel }} <span class="text-red-500">*</span></label>
          <input
            v-model="toEmail"
            type="email"
            placeholder="builder@example.com"
            class="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:max-w-md"
          />
        </div>
        <div v-for="(label, i) in emailCfg.ccLabels ?? []" :key="label">
          <label class="block text-xs font-medium text-slate-600">{{ label }} <span class="font-normal text-slate-400">(Cc, optional)</span></label>
          <input
            v-model="ccEmails[i]"
            type="text"
            :placeholder="i === 0 ? 'broker@example.com' : 'borrower@example.com, partner@example.com'"
            class="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:max-w-md"
          />
        </div>
      </div>

      <div class="mt-4 flex items-center gap-3">
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold text-white transition disabled:opacity-40"
          :class="themeClasses.btn"
          :disabled="!canSend || sending"
          @click="onCreateDraft"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 6h16v12H4z" /><path d="m4 7 8 6 8-6" />
          </svg>
          {{ sending ? 'Creating draft…' : 'Create email draft' }}
        </button>
        <a v-if="emailResult" href="https://mail.google.com/mail/u/0/#drafts" target="_blank" rel="noopener" class="text-sm font-medium text-blue-600 hover:text-blue-700">Open Gmail Drafts →</a>
      </div>
      <p v-if="emailResult" class="mt-3 text-sm text-green-700">{{ emailResult }}</p>
      <p v-if="emailError" class="mt-3 text-sm text-red-600">{{ emailError }}</p>
    </div>

    <div class="mt-8 flex items-center justify-between">
      <button type="button" class="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="back">Back</button>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-white transition"
        :class="themeClasses.btn"
        @click="requestGoHome"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
        Done
      </button>
    </div>
  </div>
</template>
