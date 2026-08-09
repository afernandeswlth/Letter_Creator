<script setup lang="ts">
import { LETTER_TYPES } from '~/utils/letterTypes'
import type { LetterTypeId } from '~/types'

const { chooseType } = useLetterWizard()
const { getRecentLetters } = useLetterApi()

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
// (This dashboard view will become user-specific later; the /recent page keeps
// showing the full, all-users history.)
const { data: recent, pending, refresh } = useAsyncData('dashboard-recent', () => getRecentLetters(500), {
  default: () => [],
})
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
        <h2 class="text-base font-semibold text-slate-900">
          Recent Letters
          <span v-if="recent.length" class="ml-1.5 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">{{ recent.length }}</span>
        </h2>
        <button
          type="button"
          class="inline-flex items-center gap-1.5 text-sm font-semibold text-blue-600 transition hover:text-blue-700"
          @click="refresh()"
        >
          <WIcon name="file-text" class="h-4 w-4" />
          Refresh
        </button>
      </div>

      <div class="mt-4">
        <LettersTable :rows="recent" :pending="pending" />
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
