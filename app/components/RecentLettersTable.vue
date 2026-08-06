<script setup lang="ts">
import type { LetterRecord } from '~/types'

const { getRecentLetters } = useLetterApi()
const { data: letters, pending } = await useAsyncData('recent-letters', () =>
  getRecentLetters(),
)

const rows = computed<LetterRecord[]>(() => letters.value ?? [])
</script>

<template>
  <section class="rounded-xl border border-slate-200 bg-white p-6">
    <h2 class="text-lg font-semibold text-slate-900">Recent Letters</h2>

    <div class="mt-4 overflow-x-auto">
      <table class="w-full text-left text-sm">
        <thead>
          <tr class="border-b border-slate-200 text-slate-500">
            <th class="py-3 pr-4 font-medium">Customer</th>
            <th class="py-3 pr-4 font-medium">Letter</th>
            <th class="py-3 pr-4 font-medium">Status</th>
            <th class="py-3 pr-4 font-medium">Created</th>
            <th class="py-3 pr-4 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="pending">
            <td colspan="5" class="py-6 text-center text-slate-400">Loading…</td>
          </tr>
          <tr
            v-for="row in rows"
            v-else
            :key="row.id"
            class="border-b border-slate-100 last:border-0"
          >
            <td class="py-4 pr-4 text-slate-900">{{ row.customer || '—' }}</td>
            <td class="py-4 pr-4 text-slate-600">{{ row.typeLabel }}</td>
            <td class="py-4 pr-4"><StatusBadge :status="row.status" /></td>
            <td class="py-4 pr-4 text-slate-600">{{ row.createdAt }}</td>
            <td class="py-4 pr-4">
              <button class="font-medium text-blue-600 hover:text-blue-700">
                {{ row.status === 'Draft' ? 'Edit' : 'View' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
