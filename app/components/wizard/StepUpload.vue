<script setup lang="ts">
import { BRAND_LIST } from '~/utils/brands'
import type { BrandId } from '~/types'

const { state, setBrand, next } = useLetterWizard()
const { parseFunderDocs } = useLetterApi()

const dragging = ref(false)
const busy = ref(false)
const error = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

function pickFiles() {
  fileInput.value?.click()
}

function addFiles(list: FileList | null | undefined) {
  error.value = ''
  if (!list) return
  const docx = Array.from(list).filter((f) => f.name.toLowerCase().endsWith('.docx'))
  if (!docx.length) {
    error.value = 'Please select the funder’s Word documents (.docx).'
    return
  }
  const names = new Set(state.value.files.map((f) => f.name))
  state.value.files.push(...docx.filter((f) => !names.has(f.name)))
}

function removeFile(i: number) {
  state.value.files.splice(i, 1)
}

async function onNext() {
  if (!state.value.files.length) return
  busy.value = true
  error.value = ''
  try {
    state.value.parse = await parseFunderDocs(state.value.files)
    next()
  } catch (e) {
    error.value = `Could not read the funder documents. ${(e as Error).message}`
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white p-6">
    <h2 class="text-lg font-semibold text-slate-900">1. Upload Funder Documents</h2>
    <p class="mt-1 text-sm text-slate-500">
      Choose the brand, then upload the welcome letter(s) the funder sent — one
      <code class="rounded bg-slate-100 px-1 py-0.5 text-xs">.docx</code> per borrower.
      For an SMSF/Trust, upload the entity’s and each member’s document together.
    </p>

    <!-- Brand -->
    <div class="mt-6">
      <p class="text-sm font-medium text-slate-700">Brand</p>
      <div class="mt-2 grid grid-cols-2 gap-3 sm:max-w-lg">
        <button
          v-for="brand in BRAND_LIST"
          :key="brand.id"
          type="button"
          class="flex h-20 items-center justify-center rounded-lg border transition"
          :class="
            state.brand === brand.id
              ? 'border-blue-600 bg-blue-50 ring-1 ring-blue-600'
              : 'border-slate-200 bg-white hover:border-slate-300'
          "
          @click="setBrand(brand.id as BrandId)"
        >
          <img :src="brand.logo" :alt="brand.name" class="max-h-9 w-auto max-w-[70%] object-contain" />
        </button>
      </div>
    </div>

    <!-- Dropzone -->
    <div
      class="mt-6 flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition"
      :class="dragging ? 'border-blue-500 bg-blue-50/50' : 'border-slate-300'"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="dragging = false; addFiles($event.dataTransfer?.files)"
    >
      <svg class="h-8 w-8 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 15V3m0 0L8 7m4-4l4 4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
      </svg>
      <p class="mt-3 text-sm text-slate-500">Drag and drop the funder .docx files here</p>
      <p class="my-1 text-xs text-slate-400">or</p>
      <button type="button" class="mt-1 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" @click="pickFiles">
        Browse Files
      </button>
      <input ref="fileInput" type="file" accept=".docx" multiple class="hidden" @change="addFiles(($event.target as HTMLInputElement).files)" />
    </div>

    <p v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</p>

    <!-- Selected files -->
    <div v-if="state.files.length" class="mt-6">
      <p class="text-sm font-medium text-slate-700">
        Selected files ({{ state.files.length }})
      </p>
      <ul class="mt-2 space-y-2">
        <li v-for="(f, i) in state.files" :key="f.name" class="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3">
          <span class="flex items-center gap-3 text-sm text-slate-800">
            <span class="flex h-7 w-7 items-center justify-center rounded bg-blue-600 text-[10px] font-bold text-white">W</span>
            {{ f.name }}
          </span>
          <button class="text-sm font-medium text-slate-400 hover:text-red-600" @click="removeFile(i)">Remove</button>
        </li>
      </ul>
    </div>

    <div class="mt-6 flex justify-end">
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
        :disabled="!state.files.length || busy"
        @click="onNext"
      >
        {{ busy ? 'Reading documents…' : 'Next: BSB & Accounts' }}
      </button>
    </div>
  </div>
</template>
