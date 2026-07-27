<script setup lang="ts">
const { state, back, next } = useLetterWizard()
const { renderLetters } = useLetterApi()

const busy = ref(false)
const showErrors = ref(false)
const error = ref('')

const offsetOptions = [
  { value: 'yes' as const, label: 'Yes / No Offset Account' },
  { value: 'no' as const, label: 'No' },
]

const bsbOk = computed(
  () => state.value.noDirectDebit || /^\d{3}-?\d{3}$/.test(state.value.ddBsb.trim()),
)
const accountOk = computed(
  () => state.value.noDirectDebit || state.value.ddAccount.trim().length >= 5,
)
const offsetOk = computed(() => state.value.offsetLinked !== null)
const isValid = computed(() => bsbOk.value && accountOk.value && offsetOk.value)

// "No Direct Debit" clears the fields so the letter omits the DD table.
watch(
  () => state.value.noDirectDebit,
  (v) => {
    if (v) {
      state.value.ddBsb = ''
      state.value.ddAccount = ''
    }
  },
)

async function onNext() {
  showErrors.value = true
  if (!isValid.value) return
  busy.value = true
  error.value = ''
  try {
    const res = await renderLetters(
      state.value.files,
      state.value.brand,
      state.value.ddBsb.trim(),
      state.value.ddAccount.trim(),
    )
    state.value.rendered = res.parties
    next()
  } catch (e) {
    error.value = `Could not generate the letters. ${(e as Error).message}`
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white p-6">
    <h2 class="text-lg font-semibold text-slate-900">2. BSB &amp; Account</h2>
    <p class="mt-1 text-sm text-slate-500">
      Everything else is read from the funder documents. Enter the nominated
      direct-debit account — the only detail added by hand. It applies to every
      letter on this loan.
    </p>

    <!-- Detected parties -->
    <div v-if="state.parse" class="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
      <div class="flex items-center gap-2">
        <span class="text-sm font-semibold text-slate-900">Detected:</span>
        <span class="rounded-md bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-600/20">
          {{ state.parse.loanType }}
        </span>
        <span class="text-sm text-slate-500">· {{ state.parse.parties.length }} letter(s)</span>
      </div>
      <ul class="mt-3 space-y-1.5">
        <li v-for="p in state.parse.parties" :key="p.name" class="flex items-center gap-2 text-sm">
          <span class="w-16 flex-none text-xs font-medium" :class="p.isEntity ? 'text-teal-700' : 'text-slate-500'">
            {{ p.role }}
          </span>
          <span class="text-slate-800">{{ p.name }}</span>
          <span class="text-slate-400">· Customer #{{ p.customerNumber }}</span>
        </li>
      </ul>
    </div>

    <!-- Direct Debit Details -->
    <h3 class="mt-6 text-base font-semibold text-slate-900">Direct Debit Details</h3>
    <label class="mt-2 inline-flex items-center gap-2 text-sm text-slate-700">
      <input
        v-model="state.noDirectDebit"
        type="checkbox"
        class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
      />
      No Direct Debit Set Up
    </label>
    <div class="mt-3 grid grid-cols-1 gap-5 sm:max-w-md sm:grid-cols-2">
      <div>
        <label for="bsb" class="block text-sm font-medium text-slate-700">BSB Number <span v-if="!state.noDirectDebit" class="text-red-500">*</span></label>
        <input
          id="bsb" v-model="state.ddBsb" type="text" placeholder="182-512"
          :disabled="state.noDirectDebit"
          class="mt-1.5 block w-full rounded-lg border px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400"
          :class="showErrors && !bsbOk ? 'border-red-400' : 'border-slate-300'"
        />
        <p v-if="showErrors && !bsbOk" class="mt-1 text-xs text-red-600">Enter a valid BSB (e.g. 182-512).</p>
      </div>
      <div>
        <label for="acct" class="block text-sm font-medium text-slate-700">Account Number <span v-if="!state.noDirectDebit" class="text-red-500">*</span></label>
        <input
          id="acct" v-model="state.ddAccount" type="text" placeholder="974761371"
          :disabled="state.noDirectDebit"
          class="mt-1.5 block w-full rounded-lg border px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400"
          :class="showErrors && !accountOk ? 'border-red-400' : 'border-slate-300'"
        />
        <p v-if="showErrors && !accountOk" class="mt-1 text-xs text-red-600">Enter the account number.</p>
      </div>
    </div>

    <!-- Offset question (mandatory — drives the email template) -->
    <div class="mt-6">
      <p class="text-sm font-medium text-slate-700">
        Account linked to Offset? <span class="text-red-500">*</span>
      </p>
      <p class="mt-0.5 text-xs text-slate-400">Determines which email template the borrower receives.</p>
      <div class="mt-2 flex gap-3">
        <button
          v-for="opt in offsetOptions"
          :key="opt.value"
          type="button"
          class="rounded-lg border px-6 py-2 text-sm font-medium transition"
          :class="
            state.offsetLinked === opt.value
              ? 'border-blue-600 bg-blue-50 text-blue-700 ring-1 ring-blue-600'
              : 'border-slate-300 text-slate-700 hover:border-slate-400'
          "
          @click="state.offsetLinked = opt.value"
        >
          {{ opt.label }}
        </button>
      </div>
      <p v-if="showErrors && !offsetOk" class="mt-1 text-xs text-red-600">Please select Yes or No.</p>
    </div>

    <p v-if="error" class="mt-4 text-sm text-red-600">{{ error }}</p>

    <div class="mt-8 flex items-center justify-between">
      <button type="button" class="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="back">Back</button>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-40"
        :disabled="busy"
        @click="onNext"
      >
        {{ busy ? 'Generating letters…' : 'Next: Preview' }}
      </button>
    </div>
  </div>
</template>
