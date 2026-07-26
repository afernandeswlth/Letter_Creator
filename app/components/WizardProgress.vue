<script setup lang="ts">
import { WIZARD_STEPS } from '~/composables/useLetterWizard'

const props = defineProps<{ current: number }>()
const emit = defineEmits<{ (e: 'select', step: number): void }>()

function stateOf(id: number): 'done' | 'active' | 'todo' {
  if (id < props.current) return 'done'
  if (id === props.current) return 'active'
  return 'todo'
}
</script>

<template>
  <div
    class="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-6 py-5"
  >
    <template v-for="(step, i) in WIZARD_STEPS" :key="step.id">
      <button
        type="button"
        class="flex items-center gap-3 text-left"
        :disabled="stateOf(step.id) === 'todo'"
        :class="stateOf(step.id) === 'todo' ? 'cursor-not-allowed' : 'cursor-pointer'"
        @click="emit('select', step.id)"
      >
        <span
          class="flex h-8 w-8 flex-none items-center justify-center rounded-full text-sm font-semibold transition"
          :class="{
            'bg-blue-600 text-white': stateOf(step.id) === 'active',
            'bg-blue-100 text-blue-700': stateOf(step.id) === 'done',
            'bg-slate-100 text-slate-400': stateOf(step.id) === 'todo',
          }"
        >
          <svg
            v-if="stateOf(step.id) === 'done'"
            class="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="3"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M5 13l4 4L19 7" />
          </svg>
          <template v-else>{{ step.id }}</template>
        </span>
        <span
          class="text-sm font-medium"
          :class="stateOf(step.id) === 'todo' ? 'text-slate-400' : 'text-slate-900'"
        >
          {{ step.label }}
        </span>
      </button>

      <div
        v-if="i < WIZARD_STEPS.length - 1"
        class="mx-4 h-px flex-1 bg-slate-200"
      />
    </template>
  </div>
</template>
