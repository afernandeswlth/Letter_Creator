<script setup lang="ts">
import type { LetterStatus } from '~/types'

const props = defineProps<{ status: LetterStatus }>()

const styles: Record<LetterStatus, string> = {
  Completed: 'bg-green-50 text-green-700 ring-green-600/20',
  Draft: 'bg-slate-100 text-slate-600 ring-slate-500/20',
  Sent: 'bg-blue-50 text-blue-700 ring-blue-600/20',
}
</script>

<template>
  <span
    class="inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium ring-1 ring-inset"
    :class="styles[props.status]"
  >
    {{ props.status }}
  </span>
</template>
