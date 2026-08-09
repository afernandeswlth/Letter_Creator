<script setup lang="ts">
const { getRecentLetters } = useLetterApi()

// The full letter history across everyone. (The dashboard's Recent Letters will
// later be scoped to the signed-in user; this page stays the all-users view.)
const { data: letters, pending, refresh } = useAsyncData('all-letters', () => getRecentLetters(500), {
  default: () => [],
})
</script>

<template>
  <div>
    <div class="flex items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">
          Recent Letters
          <span v-if="letters.length" class="ml-1.5 align-middle rounded-full bg-slate-100 px-2 py-0.5 text-sm font-medium text-slate-500">{{ letters.length }}</span>
        </h1>
        <p class="mt-1 text-sm text-slate-500">Every letter created across the team — download any as a PDF.</p>
      </div>
      <button
        type="button"
        class="inline-flex flex-none items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
        @click="refresh()"
      >
        <WIcon name="clock" class="h-4 w-4" />
        Refresh
      </button>
    </div>

    <div class="mt-6 rounded-2xl border border-slate-200 bg-white p-6">
      <LettersTable :rows="letters" :pending="pending" max-height="70vh" empty-hint="Letters created by anyone on the team will appear here." />
    </div>
  </div>
</template>
