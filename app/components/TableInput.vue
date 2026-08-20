<script setup lang="ts">
// An editable table field — a header of column labels, a row of inputs per entry,
// and an "Add row" button (matching the tables in the CAM document). The value is
// stored as JSON so the engine can render one document-table row per entry:
//   • multi-column  → a 2D array, e.g. [["Home loan","$450k","Good"], …]
//   • flat (1 col)  → a 1D array of strings, e.g. ["Firstmac — $258k", …]
// `rowLabelPrefix` adds a read-only leading column that auto-numbers each row
// (e.g. "Refinance 1", "Refinance 2"); that label is derived, never stored.
interface TableColumn { label: string, placeholder?: string }

const props = defineProps<{
  modelValue?: string
  columns: TableColumn[]
  rowLabelPrefix?: string
  flat?: boolean
  showHeader?: boolean
  minRows?: number
  maxRows?: number
  addLabel?: string
}>()
const emit = defineEmits<{ 'update:modelValue': [string] }>()

const min = computed(() => props.minRows ?? 1)
const blankRow = () => props.columns.map(() => '')

function parse(raw?: string): string[][] {
  let rows: string[][] = []
  if (raw) {
    try {
      const a = JSON.parse(raw)
      if (Array.isArray(a)) {
        rows = a.map((r) => {
          const cells = Array.isArray(r) ? r : [r]
          return props.columns.map((_, i) => String(cells[i] ?? ''))
        })
      }
    } catch {
      rows = [[String(raw), ...blankRow().slice(1)]]
    }
  }
  while (rows.length < min.value) rows.push(blankRow())
  return rows
}

const rows = ref<string[][]>(parse(props.modelValue))

// Keep in sync when the value is set externally (e.g. a HubSpot import prefill).
watch(() => props.modelValue, (v) => {
  const next = parse(v)
  if (JSON.stringify(next) !== JSON.stringify(rows.value)) rows.value = next
})

function commit() {
  const payload = props.flat ? rows.value.map(r => r[0] ?? '') : rows.value
  emit('update:modelValue', JSON.stringify(payload))
}
function onInput(r: number, c: number, val: string) {
  rows.value[r]![c] = val
  commit()
}
function addRow() {
  if (!props.maxRows || rows.value.length < props.maxRows) {
    rows.value.push(blankRow())
    commit()
  }
}
function removeRow(r: number) {
  rows.value.splice(r, 1)
  if (rows.value.length < min.value) rows.value.push(blankRow())
  commit()
}
const canAdd = computed(() => !props.maxRows || rows.value.length < props.maxRows)
const showHead = computed(() => props.showHeader !== false)
</script>

<template>
  <div class="mt-1.5 overflow-hidden rounded-lg border border-slate-300">
    <table class="w-full border-collapse text-sm">
      <thead v-if="showHead">
        <tr class="bg-slate-50 text-left text-xs font-medium text-slate-600">
          <th v-if="rowLabelPrefix" class="w-32 border-b border-slate-200 px-3 py-2" />
          <th v-for="col in columns" :key="col.label" class="border-b border-slate-200 px-3 py-2">{{ col.label }}</th>
          <th class="w-10 border-b border-slate-200" />
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, r) in rows" :key="r" class="border-b border-slate-100 last:border-0">
          <td v-if="rowLabelPrefix" class="w-32 bg-slate-50 px-3 py-1.5 align-middle text-sm text-slate-600">
            {{ rowLabelPrefix }} {{ r + 1 }}
          </td>
          <td v-for="(col, c) in columns" :key="c" class="px-2 py-1.5 align-top">
            <input
              :value="row[c]"
              :placeholder="col.placeholder"
              class="block w-full rounded-md border border-slate-200 px-2 py-1.5 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              @input="onInput(r, c, ($event.target as HTMLInputElement).value)"
            />
          </td>
          <td class="px-1 text-center align-middle">
            <button
              v-if="rows.length > min"
              type="button"
              class="rounded p-1 text-slate-400 hover:text-red-600"
              title="Remove row"
              @click="removeRow(r)"
            >
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="canAdd" class="border-t border-slate-200 bg-slate-50 px-2 py-1.5">
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-md px-2 py-1 text-sm font-medium text-blue-600 hover:text-blue-700"
        @click="addRow"
      >
        <WIcon name="plus" class="h-4 w-4" /> {{ addLabel || 'Add row' }}
      </button>
    </div>
  </div>
</template>
