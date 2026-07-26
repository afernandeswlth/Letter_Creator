<script setup lang="ts">
import { BRAND_LIST } from '~/utils/brands'

// Kept in script so the literal double-braces don't clash with Vue mustaches.
const tokenSyntax = '{{token}}'
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-slate-900">Templates</h1>
    <p class="mt-1 text-sm text-slate-500">
      Uploaded .docx templates per brand. Placeholders use
      <code class="rounded bg-slate-100 px-1 py-0.5 text-xs">{{ tokenSyntax }}</code>
      syntax.
    </p>

    <div class="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2">
      <div
        v-for="brand in BRAND_LIST"
        :key="brand.id"
        class="rounded-xl border border-slate-200 bg-white p-6"
      >
        <p class="text-base font-semibold text-slate-900">{{ brand.name }}</p>
        <div
          class="mt-4 flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3 text-sm"
        >
          <span class="flex items-center gap-3 text-slate-800">
            <span
              class="flex h-7 w-7 items-center justify-center rounded bg-blue-600 text-[10px] font-bold text-white"
            >
              W
            </span>
            Welcome_Letter_Template.docx
          </span>
          <button class="font-medium text-blue-600 hover:text-blue-700">View</button>
        </div>
      </div>
    </div>
  </div>
</template>
