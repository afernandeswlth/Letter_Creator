<script setup lang="ts">
const { state, goTo, reset } = useLetterWizard()
</script>

<template>
  <div>
    <!-- Page header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">New Welcome Letter</h1>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        @click="reset"
      >
        <svg
          class="h-4 w-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M4 4v6h6M20 20v-6h-6M20 8A8 8 0 006 5.3L4 7m0 10a8 8 0 0014 2.7l2-1.7" />
        </svg>
        Reset
      </button>
    </div>

    <!-- Progress -->
    <div class="mt-6">
      <WizardProgress :current="state.step" @select="goTo" />
    </div>

    <!-- Wizard (full width) -->
    <div class="mt-6">
      <WizardStepUpload v-if="state.step === 1" />
      <WizardStepFillDetails v-else-if="state.step === 2" />
      <WizardStepPreview v-else-if="state.step === 3" />
      <WizardStepSaveSend v-else-if="state.step === 4" />
    </div>
  </div>
</template>
