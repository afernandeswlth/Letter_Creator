<script setup lang="ts">
import { BRAND_LIST } from '~/utils/brands'
import type { BrandId } from '~/types'

// Shared brand picker used across the app so branding is consistent everywhere:
// Mortgage Mart on a dark button, WLTH on a purple button, both with the logo
// rendered white (brightness-0 invert).
const { state, setBrand } = useLetterWizard()

const selectedName = computed(
  () => BRAND_LIST.find((b) => b.id === state.value.brand)?.name ?? '',
)
</script>

<template>
  <div>
    <p class="text-sm font-medium text-slate-700">Brand</p>
    <div class="mt-2 grid grid-cols-2 gap-4 sm:max-w-lg">
      <button
        v-for="brand in BRAND_LIST"
        :key="brand.id"
        type="button"
        class="relative flex h-16 items-center justify-center rounded-xl transition-all duration-150"
        :class="[
          brand.id === 'wlth' ? 'bg-[#4f46e5]' : 'bg-neutral-900',
          state.brand === brand.id
            ? 'scale-[1.03] opacity-100 shadow-lg ring-4 ring-blue-500 ring-offset-2'
            : 'opacity-40 grayscale hover:opacity-70',
        ]"
        @click="setBrand(brand.id as BrandId)"
      >
        <img
          :src="brand.logo"
          :alt="brand.name"
          class="w-auto object-contain brightness-0 invert"
          :class="brand.id === 'wlth' ? 'max-h-5' : 'max-h-9'"
        />
        <span
          v-if="state.brand === brand.id"
          class="absolute -right-2.5 -top-2.5 flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-white shadow ring-2 ring-white"
        >
          <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 13l4 4L19 7" />
          </svg>
        </span>
      </button>
    </div>
    <p class="mt-2 text-xs text-slate-500">
      Selected: <span class="font-semibold text-slate-700">{{ selectedName }}</span>
    </p>
  </div>
</template>
