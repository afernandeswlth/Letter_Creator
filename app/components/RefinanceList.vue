<script setup lang="ts">
// A dynamic list of refinance notes (1-5). Starts with one "Refinance 1 notes"
// input; once it has text an "Add" button reveals the next, up to five. The value
// is stored as a JSON array of strings so the PDF/Word renderer can turn each into
// a table row ("Refinance N" | notes).
const props = defineProps<{ modelValue?: string; placeholder?: string }>()
const emit = defineEmits<{ 'update:modelValue': [string] }>()

const MAX = 5

function parse(raw?: string): string[] {
  if (!raw) return ['']
  try {
    const a = JSON.parse(raw)
    if (Array.isArray(a)) return a.length ? a.map((x) => String(x)) : ['']
  } catch {
    return [raw]
  }
  return ['']
}

const items = ref<string[]>(parse(props.modelValue))

// Keep in sync when the value is set externally (e.g. a HubSpot import prefill).
watch(
  () => props.modelValue,
  (v) => {
    const next = parse(v)
    if (JSON.stringify(next) !== JSON.stringify(items.value)) items.value = next
  },
)

function commit() {
  emit('update:modelValue', JSON.stringify(items.value))
}

function onInput(i: number, val: string) {
  items.value[i] = val
  commit()
}

function add() {
  if (items.value.length < MAX) {
    items.value.push('')
    commit()
  }
}

function remove(i: number) {
  items.value.splice(i, 1)
  if (!items.value.length) items.value = ['']
  commit()
}

const canAdd = computed(
  () => items.value.length < MAX && (items.value[items.value.length - 1] || '').trim() !== '',
)
</script>

<template>
  <div class="mt-1.5 space-y-3">
    <div v-for="(item, i) in items" :key="i">
      <div class="flex items-center justify-between">
        <span class="text-xs font-medium text-slate-600">Refinance {{ i + 1 }} notes</span>
        <button
          v-if="items.length > 1"
          type="button"
          class="text-xs font-medium text-slate-400 hover:text-red-600"
          @click="remove(i)"
        >
          Remove
        </button>
      </div>
      <input
        :value="item"
        :placeholder="placeholder || 'e.g. Firstmac — $258,500.00'"
        class="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
        @input="onInput(i, ($event.target as HTMLInputElement).value)"
      />
    </div>
    <button
      v-if="canAdd"
      type="button"
      class="inline-flex items-center gap-1 rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
      @click="add"
    >
      + Add
    </button>
  </div>
</template>
