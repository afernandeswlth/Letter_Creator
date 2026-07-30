<script setup lang="ts">
import { BRAND_LIST } from '~/utils/brands'
import type { BrandId, LetterTypeField } from '~/types'

const { state, currentType, setBrand, next } = useLetterWizard()

const showErrors = ref(false)

const today = new Date().toLocaleDateString('en-AU', { day: 'numeric', month: 'long', year: 'numeric' })

const fields = computed<LetterTypeField[]>(() => currentType.value?.fields ?? [])

// Ordered, unique section names.
const sections = computed(() => {
  const seen: string[] = []
  for (const f of fields.value) {
    const s = f.section ?? 'Details'
    if (!seen.includes(s)) seen.push(s)
  }
  return seen
})
const fieldsIn = (section: string) => fields.value.filter((f) => (f.section ?? 'Details') === section)

// Seed defaults (and blanks so the keys are reactive) once.
onMounted(() => {
  for (const f of fields.value) {
    const cur = state.value.fieldValues[f.id]
    if (cur == null || cur === '') {
      state.value.fieldValues[f.id] = f.default ?? (f.type === 'date' ? today : '')
    }
  }
})

const missing = (f: LetterTypeField) => f.required && !(state.value.fieldValues[f.id] ?? '').trim()
const isValid = computed(() => fields.value.every((f) => !missing(f)))

function onNext() {
  showErrors.value = true
  if (isValid.value) next()
}
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white p-6">
    <h2 class="text-lg font-semibold text-slate-900">Enter Details</h2>
    <p class="mt-1 text-sm text-slate-500">
      Fill in the fields below — the rest of the letter is standard wording.
    </p>

    <!-- Brand -->
    <div class="mt-6">
      <p class="text-sm font-medium text-slate-700">Brand</p>
      <div class="mt-2 grid grid-cols-2 gap-3 sm:max-w-lg">
        <button
          v-for="brand in BRAND_LIST"
          :key="brand.id"
          type="button"
          class="flex h-16 items-center justify-center rounded-lg border transition"
          :class="state.brand === brand.id ? 'border-blue-600 bg-blue-50 ring-1 ring-blue-600' : 'border-slate-200 bg-white hover:border-slate-300'"
          @click="setBrand(brand.id as BrandId)"
        >
          <img :src="brand.logo" :alt="brand.name" class="w-auto object-contain" :class="brand.id === 'wlth' ? 'max-h-5' : 'max-h-8'" />
        </button>
      </div>
    </div>

    <!-- Field sections -->
    <div v-for="section in sections" :key="section" class="mt-8">
      <h3 class="border-b border-slate-100 pb-2 text-base font-semibold text-slate-900">{{ section }}</h3>
      <div class="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2">
        <div
          v-for="f in fieldsIn(section)"
          :key="f.id"
          :class="f.type === 'textarea' ? 'sm:col-span-2' : ''"
        >
          <label :for="f.id" class="block text-sm font-medium text-slate-700">
            {{ f.label }} <span v-if="f.required" class="text-red-500">*</span>
          </label>

          <textarea
            v-if="f.type === 'textarea'"
            :id="f.id"
            v-model="state.fieldValues[f.id]"
            rows="2"
            :placeholder="f.placeholder"
            class="mt-1.5 block w-full rounded-lg border px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            :class="showErrors && missing(f) ? 'border-red-400' : 'border-slate-300'"
          />
          <select
            v-else-if="f.type === 'select'"
            :id="f.id"
            v-model="state.fieldValues[f.id]"
            class="mt-1.5 block w-full rounded-lg border bg-white px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            :class="showErrors && missing(f) ? 'border-red-400' : 'border-slate-300'"
          >
            <option v-for="opt in f.options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
          <input
            v-else
            :id="f.id"
            v-model="state.fieldValues[f.id]"
            :type="f.type === 'email' ? 'email' : 'text'"
            :placeholder="f.placeholder"
            class="mt-1.5 block w-full rounded-lg border px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            :class="showErrors && missing(f) ? 'border-red-400' : 'border-slate-300'"
          />

          <p v-if="f.help" class="mt-1 text-xs text-slate-400">{{ f.help }}</p>
          <p v-if="showErrors && missing(f)" class="mt-1 text-xs text-red-600">This field is required.</p>
        </div>
      </div>
    </div>

    <div class="mt-8 flex items-center justify-end">
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700"
        @click="onNext"
      >
        Next: Preview
      </button>
    </div>
  </div>
</template>
