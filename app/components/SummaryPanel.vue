<script setup lang="ts">
const { state, currentBrand } = useLetterWizard()
</script>

<template>
  <aside class="rounded-xl border border-slate-200 bg-slate-50 p-6">
    <h3 class="text-base font-semibold text-slate-900">Summary</h3>

    <dl class="mt-5 space-y-5 text-sm">
      <div>
        <dt class="font-semibold text-slate-900">Brand</dt>
        <dd class="mt-0.5 text-slate-600">{{ currentBrand.name }}</dd>
      </div>
      <div>
        <dt class="font-semibold text-slate-900">Funder documents</dt>
        <dd class="mt-0.5 text-slate-600">
          {{ state.files.length ? `${state.files.length} uploaded` : 'None uploaded' }}
        </dd>
      </div>
      <div v-if="state.parse">
        <dt class="font-semibold text-slate-900">Loan type</dt>
        <dd class="mt-0.5 text-slate-600">
          {{ state.parse.loanType }} · {{ state.parse.parties.length }} letter(s)
        </dd>
      </div>
      <div v-if="state.ddBsb || state.ddAccount">
        <dt class="font-semibold text-slate-900">Direct debit</dt>
        <dd class="mt-0.5 text-slate-600">
          BSB {{ state.ddBsb || '—' }} · Acct {{ state.ddAccount || '—' }}
        </dd>
      </div>
    </dl>
  </aside>
</template>
