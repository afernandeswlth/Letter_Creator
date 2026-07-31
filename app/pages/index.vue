<script setup lang="ts">
const { state, currentType, goTo, reset, resetForm, confirmingHome, requestGoHome, cancelGoHome, confirmGoHome } = useLetterWizard()

// The dashboard shows until a letter type is chosen. An 'available' type runs
// its wizard — 'upload' types (Welcome) use the funder-doc flow, 'form' types
// (Formal Approval) use the fill-in flow. Other statuses show a coming-soon panel.
const isAvailable = computed(() => currentType.value?.status === 'available')
const isUpload = computed(() => currentType.value?.inputModel === 'upload')
const showReset = computed(() => isAvailable.value)
</script>

<template>
  <!-- Landing dashboard -->
  <DashboardHome v-if="!state.letterType" />

  <!-- A letter type is selected -->
  <div v-else>
    <!-- Header: back to dashboard + type name + reset -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <button
          type="button"
          class="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-300 bg-white text-slate-600 transition hover:bg-slate-50"
          title="Back to dashboard"
          @click="requestGoHome"
        >
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
        <h1 class="text-2xl font-bold text-slate-900">{{ currentType?.label }}</h1>
      </div>
      <button
        v-if="showReset"
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-red-700"
        @click="resetForm"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 4v6h6M20 20v-6h-6M20 8A8 8 0 006 5.3L4 7m0 10a8 8 0 0014 2.7l2-1.7" />
        </svg>
        Reset
      </button>
    </div>

    <!-- Available: run the wizard for this type -->
    <template v-if="isAvailable">
      <div class="mt-6">
        <WizardProgress :current="state.step" @select="goTo" />
      </div>
      <div class="mt-6">
        <!-- upload flow (Welcome) -->
        <template v-if="isUpload">
          <WizardStepUpload v-if="state.step === 1" />
          <WizardStepFillDetails v-else-if="state.step === 2" />
          <WizardStepPreview v-else-if="state.step === 3" />
          <WizardStepSaveSend v-else-if="state.step === 4" />
        </template>
        <!-- form flow (Formal Approval, etc.) -->
        <template v-else>
          <WizardStepFillForm v-if="state.step === 1" />
          <WizardStepFormPreview v-else-if="state.step === 2" />
          <WizardStepFormSaveSend v-else-if="state.step === 3" />
        </template>
      </div>
    </template>

    <!-- Not yet available -->
    <div v-else class="mt-6">
      <WizardComingSoonLetter />
    </div>

    <!-- Confirm before returning to the landing page -->
    <div v-if="confirmingHome" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-slate-900/40" @click="cancelGoHome" />
      <div class="relative w-full max-w-sm rounded-xl border border-slate-200 bg-white p-6 shadow-xl">
        <h3 class="text-base font-semibold text-slate-900">Go back to home?</h3>
        <p class="mt-2 text-sm text-slate-500">Are you sure you want to go back to home? Any details entered for this letter will be cleared.</p>
        <div class="mt-6 flex justify-end gap-3">
          <button
            type="button"
            class="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            @click="cancelGoHome"
          >
            Cancel
          </button>
          <button
            type="button"
            class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
            @click="confirmGoHome"
          >
            Go to home
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
