<script setup lang="ts">
const { state, currentType, goTo, reset } = useLetterWizard()

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
          @click="reset"
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
        @click="reset"
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
  </div>
</template>
