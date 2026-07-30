<script setup lang="ts">
import { LETTER_TYPE_LIST } from '~/utils/letterTypes'
import type { LetterStatus } from '~/types'

const { chooseType } = useLetterWizard()

// Placeholder recent-letters data (not yet wired to a store).
interface RecentRow {
  icon: string
  type: string
  customer: string
  reference: string
  modified: string
  status: LetterStatus
}
const recent: RecentRow[] = [
  { icon: LETTER_TYPE_LIST[0]!.icon, type: 'Welcome Letter', customer: 'John Doe', reference: 'L-2024-00521', modified: '21 May 2024, 10:24 AM', status: 'Draft' },
  { icon: LETTER_TYPE_LIST[1]!.icon, type: 'Formal Approval Letter', customer: 'Jane Smith', reference: 'L-2024-00520', modified: '21 May 2024, 9:15 AM', status: 'Completed' },
  { icon: LETTER_TYPE_LIST[3]!.icon, type: 'Conditional Approval Letter', customer: 'Michael Brown', reference: 'L-2024-00519', modified: '20 May 2024, 3:42 PM', status: 'Sent' },
  { icon: LETTER_TYPE_LIST[4]!.icon, type: 'Discharge Confirmation Letter', customer: 'ABC Pty Ltd', reference: 'L-2024-00518', modified: '20 May 2024, 11:03 AM', status: 'Completed' },
]
</script>

<template>
  <div>
    <!-- Greeting -->
    <div>
      <h1 class="text-2xl font-bold text-slate-900">Welcome back, Admin</h1>
      <p class="mt-1 text-sm text-slate-500">Create professional letters quickly and efficiently.</p>
    </div>

    <!-- Create New Letter -->
    <section class="mt-8">
      <h2 class="text-base font-semibold text-slate-900">Create New Letter</h2>
      <div class="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
        <button
          v-for="t in LETTER_TYPE_LIST"
          :key="t.id"
          type="button"
          class="group flex flex-col rounded-xl border border-slate-200 bg-white p-5 text-left transition hover:border-blue-300 hover:shadow-sm"
          @click="chooseType(t.id)"
        >
          <div class="flex items-start justify-between">
            <span class="flex h-11 w-11 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
              <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <path :d="t.icon" />
              </svg>
            </span>
            <span
              v-if="t.status === 'coming-soon'"
              class="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500"
            >
              Coming soon
            </span>
          </div>
          <h3 class="mt-4 text-sm font-semibold text-slate-900">{{ t.label }}</h3>
          <p class="mt-1 flex-1 text-sm text-slate-500">{{ t.description }}</p>
          <span class="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-blue-600 group-hover:gap-2 transition-all">
            Create Letter
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </span>
        </button>
      </div>
    </section>

    <!-- Recent Letters -->
    <section class="mt-8 rounded-xl border border-slate-200 bg-white p-6">
      <div class="flex items-center justify-between">
        <h2 class="text-base font-semibold text-slate-900">Recent Letters</h2>
        <button class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50">
          View all
        </button>
      </div>

      <div class="mt-4 overflow-x-auto">
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
                  <svg class="h-4 w-4 flex-none text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                    <path :d="row.icon" />
                  </svg>
                  {{ row.type }}
                </span>
              </td>
              <td class="py-4 pr-4 text-slate-600">{{ row.customer }}</td>
              <td class="py-4 pr-4 text-slate-600">{{ row.reference }}</td>
              <td class="py-4 pr-4 text-slate-600">{{ row.modified }}</td>
              <td class="py-4 pr-4"><StatusBadge :status="row.status" /></td>
              <td class="py-4 pr-4 text-slate-400">
                <button class="rounded p-1 hover:bg-slate-100" aria-label="Actions">
                  <svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/></svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p class="mt-4 text-xs text-slate-400">Showing 1 to {{ recent.length }} of {{ recent.length }} letters</p>
    </section>
  </div>
</template>
