<script setup lang="ts">
import type { DeliveryResult } from '~/types'

const { state, back, reset } = useLetterWizard()
const { createEmailDraft, downloadZip } = useLetterApi()

const emails = reactive<Record<string, string>>({})
const results = reactive<Record<string, DeliveryResult>>({}) // per member name
const errors = reactive<Record<string, string>>({})
const creatingDrafts = ref(false)
const zipping = ref(false)
const zipError = ref('')

function stripTitle(name: string) {
  return name.replace(/^(mr|mrs|ms|miss|dr)\.?\s+/i, '')
}
const brandLabel = computed(() => (state.value.brand === 'mortgage-mart' ? 'MMA' : 'WLTH'))
function fileBaseFor(name: string) {
  return `${brandLabel.value} Welcome Letter - ${stripTitle(name)}`
}

// Members get an email; the entity does not.
const members = computed(() =>
  state.value.rendered.map((p, i) => ({ p, i })).filter((x) => !x.p.isEntity),
)

// Loan / trust details used in the email subject.
const isTrust = computed(() => (state.value.parse?.loanType ?? 'Standard') !== 'Standard')
const primaryParty = computed(() => {
  const parties = state.value.parse?.parties ?? []
  return parties.find((p) => p.isEntity) ?? parties[0]
})
const trustName = computed(() => primaryParty.value?.name ?? '')
const accountNumber = computed(() => primaryParty.value?.loanFacilityNumber ?? '')
const offset = computed<'yes' | 'no'>(() => (state.value.offsetLinked === 'no' ? 'no' : 'yes'))

// The loan name used for the ZIP + Drive-style grouping.
const loanName = computed(() => {
  const parties = state.value.parse?.parties ?? []
  const primary = parties.find((p) => p.isEntity) ?? parties[0]
  if (!primary) return 'Welcome Letters'
  const loanNo = primary.loanFacilityNumber ? ` - ${primary.loanFacilityNumber}` : ''
  return `${stripTitle(primary.name)}${loanNo}`
})

const emailRe = /^\S+@\S+\.\S+$/
const allMemberEmailsValid = computed(
  () => members.value.length > 0 && members.value.every(({ p }) => emailRe.test(emails[p.name] ?? '')),
)

async function onCreateDrafts() {
  if (!allMemberEmailsValid.value || creatingDrafts.value) return
  creatingDrafts.value = true
  try {
    for (const { p, i } of members.value) {
      errors[p.name] = ''
      try {
        results[p.name] = await createEmailDraft(
          state.value.files,
          state.value.brand,
          state.value.ddBsb,
          state.value.ddAccount,
          i,
          emails[p.name].trim(),
          p.name,
          fileBaseFor(p.name),
          {
            offset: offset.value,
            isTrust: isTrust.value,
            trustName: trustName.value,
            accountNumber: accountNumber.value,
          },
        )
      } catch (e) {
        const err = e as { data?: { statusMessage?: string }; statusMessage?: string; message?: string }
        errors[p.name] = err.data?.statusMessage || err.statusMessage || err.message || 'Could not create draft.'
      }
    }
  } finally {
    creatingDrafts.value = false
  }
}

async function onDownloadAll() {
  zipping.value = true
  zipError.value = ''
  try {
    await downloadZip(
      state.value.files,
      state.value.brand,
      state.value.ddBsb,
      state.value.ddAccount,
      `${loanName.value} Welcome Letters`,
    )
  } catch (e) {
    zipError.value = `Could not build the ZIP. ${(e as Error).message}`
  } finally {
    zipping.value = false
  }
}
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white p-6">
    <h2 class="text-lg font-semibold text-slate-900">4. Save &amp; Send</h2>
    <p class="mt-1 text-sm text-slate-500">
      Enter each member's email, then create the draft emails (letter attached)
      in your <span class="font-medium text-slate-700">hello inbox</span>.
      <template v-if="offset === 'no'">Since the offset account isn't linked, the Linked Account Nomination Form is attached too.</template>
      You can also download all the letters as a ZIP.
    </p>

    <div class="mt-6 space-y-3">
      <div
        v-for="p in state.rendered"
        :key="p.name"
        class="flex flex-col gap-3 rounded-xl border border-slate-200 p-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <div class="flex items-center gap-2">
          <span class="rounded bg-slate-100 px-2 py-0.5 text-xs font-medium" :class="p.isEntity ? 'text-teal-700' : 'text-slate-600'">{{ p.role }}</span>
          <span class="text-sm font-semibold text-slate-900">{{ p.name }}</span>
        </div>

        <!-- Members: email input. Entity: no email. -->
        <div v-if="!p.isEntity" class="w-full sm:w-80">
          <input
            v-model="emails[p.name]"
            type="email"
            placeholder="borrower@email.com"
            class="w-full rounded-md border px-3 py-1.5 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            :class="results[p.name] ? 'border-green-400' : errors[p.name] ? 'border-red-400' : 'border-slate-300'"
          />
          <p v-if="results[p.name]" class="mt-1 text-xs text-green-700">✓ {{ results[p.name].message }}</p>
          <p v-else-if="errors[p.name]" class="mt-1 text-xs text-red-600">✕ {{ errors[p.name] }}</p>
        </div>
        <span v-else class="text-xs text-slate-400">No email — included in the ZIP</span>
      </div>
    </div>

    <!-- Actions -->
    <div class="mt-6 flex flex-wrap items-center gap-3">
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
        :disabled="!allMemberEmailsValid || creatingDrafts"
        @click="onCreateDrafts"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 6h16v12H4zM4 7l8 6 8-6" />
        </svg>
        {{ creatingDrafts ? 'Creating drafts…' : 'Create Draft Email' }}
      </button>

      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-40"
        :disabled="zipping"
        @click="onDownloadAll"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 3v12m0 0l-4-4m4 4l4-4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
        </svg>
        {{ zipping ? 'Preparing ZIP…' : 'Download All' }}
      </button>
    </div>
    <p v-if="!allMemberEmailsValid" class="mt-2 text-xs text-slate-400">Enter a valid email for each member to create the drafts.</p>
    <p v-if="zipError" class="mt-2 text-xs text-red-600">{{ zipError }}</p>

    <div class="mt-8 flex items-center justify-between border-t border-slate-100 pt-6">
      <button type="button" class="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="back">Back</button>
      <button type="button" class="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="reset">Create another</button>
    </div>
  </div>
</template>
