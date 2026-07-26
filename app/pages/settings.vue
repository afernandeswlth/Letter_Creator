<script setup lang="ts">
import { BRAND_LIST } from '~/utils/brands'
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-slate-900">Settings</h1>
    <p class="mt-1 text-sm text-slate-500">
      Brand configuration. These values will drive the backend (Drive folders,
      sender addresses) once it is connected.
    </p>

    <div class="mt-6 space-y-6">
      <div
        v-for="brand in BRAND_LIST"
        :key="brand.id"
        class="rounded-xl border border-slate-200 bg-white p-6"
      >
        <p class="text-base font-semibold text-slate-900">{{ brand.name }}</p>
        <dl class="mt-4 grid grid-cols-1 gap-4 text-sm sm:grid-cols-2">
          <div>
            <dt class="font-medium text-slate-500">From email</dt>
            <dd class="mt-0.5 text-slate-900">{{ brand.fromEmail }}</dd>
          </div>
          <div>
            <dt class="font-medium text-slate-500">Google Drive folder</dt>
            <dd class="mt-0.5 text-slate-900">{{ brand.driveFolder }}</dd>
          </div>
        </dl>
      </div>
    </div>
  </div>
</template>
