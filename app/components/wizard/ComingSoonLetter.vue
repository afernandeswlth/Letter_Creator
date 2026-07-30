<script setup lang="ts">
const { currentType } = useLetterWizard()
</script>

<template>
  <div v-if="currentType" class="rounded-xl border border-slate-200 bg-white p-8">
    <div class="flex items-center gap-4">
      <span class="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
        <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
          <path :d="currentType.icon" />
        </svg>
      </span>
      <div>
        <h2 class="text-lg font-semibold text-slate-900">{{ currentType.label }}</h2>
        <span class="mt-1 inline-flex items-center rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-600/20">
          Coming soon
        </span>
      </div>
    </div>

    <p class="mt-5 max-w-2xl text-sm text-slate-600">
      This letter type is set up and ready — it just needs its official
      WLTH / Mortgage Mart template. Once the template is added, this screen
      becomes a fill-in form that generates the branded letter and email draft,
      exactly like the Welcome Letter.
    </p>

    <div v-if="currentType.fields?.length" class="mt-6">
      <p class="text-sm font-medium text-slate-700">Fields it will collect</p>
      <ul class="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
        <li
          v-for="f in currentType.fields"
          :key="f.id"
          class="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700"
        >
          <svg class="h-4 w-4 flex-none text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 7h16M4 12h16M4 17h10" />
          </svg>
          {{ f.label }}
          <span v-if="f.required" class="text-red-400">*</span>
        </li>
      </ul>
    </div>
  </div>
</template>
