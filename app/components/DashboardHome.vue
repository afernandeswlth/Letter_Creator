<script setup lang="ts">
import { LETTER_TYPES } from '~/utils/letterTypes'
import type { LetterStatus, LetterTypeId } from '~/types'

const { chooseType } = useLetterWizard()

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

// Placeholder recent-letters data (not yet wired to a store).
interface RecentRow { icon: string; type: string; customer: string; reference: string; modified: string; status: LetterStatus }
const recent: RecentRow[] = [
  { icon: 'mail', type: 'Welcome Letter', customer: 'John Doe', reference: 'L-2024-00521', modified: '21 May 2024, 10:24 AM', status: 'Draft' },
  { icon: 'clipboard-check', type: 'Conditional Approval Letter', customer: 'Jane Smith', reference: 'L-2024-00520', modified: '20 May 2024, 3:15 PM', status: 'Completed' },
  { icon: 'square-pen', type: 'Custom Letter', customer: 'ABC Construction Pty Ltd', reference: 'L-2024-00519', modified: '20 May 2024, 9:08 AM', status: 'Sent' },
]
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
        <button disabled class="cursor-not-allowed text-sm font-semibold text-blue-300">View all</button>
      </div>

      <div class="pointer-events-none mt-4 overflow-x-auto opacity-50">
        <table class="w-full text-left text-sm">
          <thead>
            <tr class="border-b border-slate-200 text-[11px] uppercase tracking-wide text-slate-400">
              <th class="py-3 pr-4 font-medium">Letter Type</th>
              <th class="py-3 pr-4 font-medium">Customer</th>
              <th class="py-3 pr-4 font-medium">Reference</th>
              <th class="py-3 pr-4 font-medium">Last Modified</th>
              <th class="py-3 pr-4 font-medium">Status</th>
              <th class="py-3 pr-4 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in recent" :key="row.reference" class="border-b border-slate-100 last:border-0">
              <td class="py-4 pr-4">
                <span class="flex items-center gap-2.5 text-slate-900">
                  <WIcon :name="row.icon" class="h-4 w-4 flex-none text-blue-500" />
                  {{ row.type }}
                </span>
              </td>
              <td class="py-4 pr-4 text-slate-600">{{ row.customer }}</td>
              <td class="py-4 pr-4 text-slate-600">{{ row.reference }}</td>
              <td class="py-4 pr-4 text-slate-600">{{ row.modified }}</td>
              <td class="py-4 pr-4"><StatusBadge :status="row.status" /></td>
              <td class="py-4 pr-4 text-slate-400">
                <button class="rounded p-1 hover:bg-slate-100" aria-label="Actions">
                  <svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="1.6" /><circle cx="12" cy="12" r="1.6" /><circle cx="19" cy="12" r="1.6" /></svg>
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
