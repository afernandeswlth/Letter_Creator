<script setup lang="ts">
import { LETTER_TYPES } from '~/utils/letterTypes'
import type { LetterTypeId } from '~/types'

const { chooseType } = useLetterWizard()
const { getRecentLetters, downloadStoredLetter } = useLetterApi()

// Letters grouped by the team that uses them (matches the WLTH team layout).
interface Group {
  name: string
  desc: string
  theme: 'blue' | 'green' | 'purple'
  icon: string // WLTH (lucide) icon name
  ids: LetterTypeId[]
}
const GROUPS: Group[] = [
  { name: 'Credit Team', desc: 'Letters for credit review and approval processes.', theme: 'blue', icon: 'shield', ids: ['pre-approval', 'conditional-approval', 'approval'] },
  { name: 'Customer Service Team', desc: 'Letters for customer communication and updates.', theme: 'green', icon: 'users', ids: ['welcome', 'commencement', 'discharge'] },
  { name: 'All Teams', desc: 'Create custom letters for any situation.', theme: 'purple', icon: 'square-pen', ids: ['custom'] },
]

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

// Full class strings (so Tailwind keeps them) keyed by theme.
const THEME = {
  blue: { card: 'border-blue-100 bg-gradient-to-b from-blue-50/70 to-white', chip: 'bg-blue-100 text-blue-600', title: 'text-blue-700', rowIcon: 'text-blue-500', hover: 'hover:border-blue-300 hover:shadow-sm' },
  green: { card: 'border-emerald-100 bg-gradient-to-b from-emerald-50/70 to-white', chip: 'bg-emerald-100 text-emerald-600', title: 'text-emerald-700', rowIcon: 'text-emerald-500', hover: 'hover:border-emerald-300 hover:shadow-sm' },
  purple: { card: 'border-violet-100 bg-gradient-to-b from-violet-50/70 to-white', chip: 'bg-violet-100 text-violet-600', title: 'text-violet-700', rowIcon: 'text-violet-500', hover: 'hover:border-violet-300 hover:shadow-sm' },
} as const

const typeOf = (id: LetterTypeId) => LETTER_TYPES[id]

// Recent letters — real history from the store (Supabase, via /api/letters/recent).
const { data: recent, pending, refresh } = useAsyncData('dashboard-recent', () => getRecentLetters(8), {
  default: () => [],
})

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
  <div>
    <!-- Greeting + quick action -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Welcome back, Admin</h1>
        <p class="mt-1 text-sm text-slate-500">Create professional letters quickly and efficiently.</p>
      </div>
      <button
        type="button"
        class="inline-flex flex-none items-center gap-3 rounded-xl bg-blue-600 px-5 py-3 text-left text-white shadow-sm transition hover:bg-blue-700"
        @click="chooseType('custom')"
      >
        <WIcon name="plus" class="h-5 w-5" />
        <span class="leading-tight">
          <span class="block text-sm font-semibold">Custom Letter</span>
          <span class="block text-xs text-blue-100">For all teams</span>
        </span>
      </button>
    </div>

    <!-- Choose a letter type -->
    <section class="mt-8">
      <h2 class="text-base font-semibold text-slate-900">Choose a Letter Type</h2>
      <div class="mt-4 grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div
          v-for="g in GROUPS"
          :key="g.name"
          class="rounded-2xl border p-6"
          :class="THEME[g.theme].card"
        >
          <span class="flex h-12 w-12 items-center justify-center rounded-xl" :class="THEME[g.theme].chip">
            <WIcon :name="g.icon" class="h-6 w-6" />
          </span>
          <h3 class="mt-4 text-lg font-semibold" :class="THEME[g.theme].title">{{ g.name }}</h3>
          <p class="mt-1 text-sm text-slate-500">{{ g.desc }}</p>

          <div class="mt-5 space-y-2.5">
            <button
              v-for="id in g.ids"
              :key="id"
              type="button"
              class="group flex w-full items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 text-left transition"
              :class="THEME[g.theme].hover"
              @click="chooseType(id)"
            >
              <span class="flex items-center gap-3">
                <WIcon :name="TYPE_ICON[id]" class="h-5 w-5 flex-none" :class="THEME[g.theme].rowIcon" />
                <span class="text-sm font-medium text-slate-800">{{ typeOf(id).label }}</span>
              </span>
              <WIcon name="chevron-right" class="h-4 w-4 flex-none text-slate-400 transition group-hover:translate-x-0.5" />
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Recent Letters -->
    <section class="mt-8 rounded-2xl border border-slate-200 bg-white p-6">
      <div class="flex items-center justify-between">
        <h2 class="text-base font-semibold text-slate-900">Recent Letters</h2>
        <button
          type="button"
          class="inline-flex items-center gap-1.5 text-sm font-semibold text-blue-600 transition hover:text-blue-700"
          @click="refresh()"
        >
          <WIcon name="file-text" class="h-4 w-4" />
          Refresh
        </button>
      </div>

      <!-- Loading -->
      <div v-if="pending && !recent.length" class="mt-6 flex items-center justify-center py-10 text-sm text-slate-400">
        <svg class="mr-2 h-5 w-5 animate-spin text-blue-600" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
        Loading recent letters…
      </div>

      <!-- Empty -->
      <div v-else-if="!recent.length" class="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 py-10 text-center">
        <WIcon name="file-text" class="h-7 w-7 text-slate-300" />
        <p class="mt-2 text-sm font-medium text-slate-600">No letters yet</p>
        <p class="mt-0.5 text-xs text-slate-400">Every letter you download or draft will appear here.</p>
      </div>

      <!-- Table -->
      <div v-else class="mt-4 overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead>
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
            <tr v-for="row in recent" :key="row.id" class="border-b border-slate-100 last:border-0">
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
    </section>

    <!-- Help footer -->
    <div class="mt-6 flex justify-center">
      <div class="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
        <WIcon name="lightbulb" class="h-4 w-4 flex-none text-amber-500" />
        Need help choosing the right letter? Contact your team lead or check our
        <span class="font-medium text-blue-600">templates</span>.
      </div>
    </div>
  </div>
</template>
