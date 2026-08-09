<script setup lang="ts">
import type { LetterRecord, LetterTypeId } from '~/types'

/**
 * Shared letter-history table (loading / empty / scrollable table + per-row PDF
 * re-download). Used by both the dashboard's Recent Letters card and the
 * standalone /recent page, so the two stay in sync.
 */
const props = withDefaults(
  defineProps<{
    rows: LetterRecord[]
    pending?: boolean
    maxHeight?: string // CSS height for the scroll container
    emptyHint?: string
  }>(),
  { pending: false, maxHeight: '32rem', emptyHint: 'Every letter you download or draft will appear here.' },
)

const { downloadStoredLetter } = useLetterApi()

// WLTH (lucide) icon per letter type.
const TYPE_ICON: Record<LetterTypeId, string> = {
  welcome: 'mail',
  approval: 'file-check',
  commencement: 'building-2',
  'pre-approval': 'user',
  'conditional-approval': 'clipboard-check',
  discharge: 'shield-check',
  custom: 'square-pen',
}
const iconFor = (letterType: string) => TYPE_ICON[letterType as LetterTypeId] ?? 'file-text'
const brandLabel = (brand: string) => (brand === 'mma' ? 'MMA' : 'WLTH')
function fmtDate(iso: string) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('en-AU', {
    day: '2-digit', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true,
  })
}

const downloadingId = ref('')
async function onDownload(id: string) {
  downloadingId.value = id
  try {
    await downloadStoredLetter(id)
  } catch {
    // best-effort; the file may have been removed from storage
  } finally {
    downloadingId.value = ''
  }
}
</script>

<template>
  <!-- Loading -->
  <div v-if="props.pending && !props.rows.length" class="flex items-center justify-center py-10 text-sm text-slate-400">
    <svg class="mr-2 h-5 w-5 animate-spin text-blue-600" viewBox="0 0 24 24" fill="none">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
    Loading letters…
  </div>

  <!-- Empty -->
  <div v-else-if="!props.rows.length" class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 py-10 text-center">
    <WIcon name="file-text" class="h-7 w-7 text-slate-300" />
    <p class="mt-2 text-sm font-medium text-slate-600">No letters yet</p>
    <p class="mt-0.5 text-xs text-slate-400">{{ props.emptyHint }}</p>
  </div>

  <!-- Table (scrolls when the history is long; header stays visible) -->
  <div v-else class="overflow-x-auto overflow-y-auto" :style="{ maxHeight: props.maxHeight }">
    <table class="w-full text-left text-sm">
      <thead class="sticky top-0 z-10 bg-white">
        <tr class="border-b border-slate-200 text-[11px] uppercase tracking-wide text-slate-400">
          <th class="py-3 pr-4 font-medium">Letter Type</th>
          <th class="py-3 pr-4 font-medium">Customer</th>
          <th class="py-3 pr-4 font-medium">Reference</th>
          <th class="py-3 pr-4 font-medium">Created</th>
          <th class="py-3 pr-4 font-medium">Status</th>
          <th class="py-3 pr-4 font-medium">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in props.rows" :key="row.id" class="border-b border-slate-100 last:border-0">
          <td class="py-4 pr-4">
            <span class="flex items-center gap-2.5 text-slate-900">
              <WIcon :name="iconFor(row.letterType)" class="h-4 w-4 flex-none text-blue-500" />
              {{ row.typeLabel }}
              <span class="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-500">{{ brandLabel(row.brand) }}</span>
            </span>
          </td>
          <td class="py-4 pr-4 text-slate-600">{{ row.customer || '—' }}</td>
          <td class="py-4 pr-4 text-slate-600">{{ row.reference || '—' }}</td>
          <td class="py-4 pr-4 text-slate-600">{{ fmtDate(row.createdAt) }}</td>
          <td class="py-4 pr-4"><StatusBadge :status="row.status" /></td>
          <td class="py-4 pr-4">
            <button
              type="button"
              class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-40"
              :disabled="downloadingId === row.id"
              aria-label="Download PDF"
              @click="onDownload(row.id)"
            >
              <WIcon name="file-check" class="h-4 w-4 text-rose-500" />
              {{ downloadingId === row.id ? '…' : 'PDF' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
