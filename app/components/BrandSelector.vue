<script setup lang="ts">
import { BRAND_LIST } from '~/utils/brands'
import type { BrandId } from '~/types'

// Shared brand picker used across the app so branding is consistent everywhere:
// Mortgage Mart on a dark button, WLTH on a purple button, both with the logo
// rendered white (brightness-0 invert).
const { state, setBrand } = useLetterWizard()
</script>

<template>
  <div>
    <p class="text-sm font-medium text-slate-700">Brand</p>
    <div class="mt-2 grid grid-cols-2 gap-3 sm:max-w-lg">
      <button
        v-for="brand in BRAND_LIST"
        :key="brand.id"
        type="button"
        class="flex h-16 items-center justify-center rounded-xl transition"
        :class="[
          brand.id === 'wlth' ? 'bg-[#4f46e5]' : 'bg-neutral-900',
          state.brand === brand.id
            ? 'ring-2 ring-offset-2 ring-slate-400'
            : 'opacity-80 hover:opacity-100',
        ]"
        @click="setBrand(brand.id as BrandId)"
      >
        <img
          :src="brand.logo"
          :alt="brand.name"
          class="w-auto object-contain brightness-0 invert"
          :class="brand.id === 'wlth' ? 'max-h-5' : 'max-h-9'"
        />
      </button>
    </div>
  </div>
</template>
