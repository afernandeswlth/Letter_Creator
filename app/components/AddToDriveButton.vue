<script setup lang="ts">
import type { DriveFile } from '~/composables/useGoogleDrive'

/**
 * "Add to Google Drive" button. Opens a custom folder chooser
 * (DriveFolderPicker) and reports the result. The parent supplies a `files`
 * getter (built lazily, on upload) and the `count` of letters (for labels).
 */
const props = defineProps<{
  files: () => Promise<DriveFile[]>
  count: number
}>()

const { isConfigured } = useGoogleDrive()

const open = ref(false)
const message = ref('')
const errored = ref(false)

function onUploaded(payload: { folderName: string; count: number }) {
  open.value = false
  errored.value = false
  message.value = `Saved ${payload.count} letter${payload.count === 1 ? '' : 's'} to “${payload.folderName}”.`
}
</script>

<template>
  <div class="inline-flex flex-col items-start gap-1">
    <button
      type="button"
      class="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
      :disabled="!isConfigured"
      :title="isConfigured ? undefined : 'Google Drive isn’t set up yet'"
      @click="message = ''; open = true"
    >
      <!-- Google Drive glyph -->
      <svg class="h-4 w-4" viewBox="0 0 87.3 78" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <path d="m6.6 66.85 3.85 6.65c.8 1.4 1.95 2.5 3.3 3.3l13.75-23.8h-27.5c0 1.55.4 3.1 1.2 4.5z" fill="#0066da" />
        <path d="m43.65 25-13.75-23.8c-1.35.8-2.5 1.9-3.3 3.3l-25.4 44a9.06 9.06 0 0 0-1.2 4.5h27.5z" fill="#00ac47" />
        <path d="m73.55 76.8c1.35-.8 2.5-1.9 3.3-3.3l1.6-2.75 7.65-13.25c.8-1.4 1.2-2.95 1.2-4.5h-27.502l5.852 11.5z" fill="#ea4335" />
        <path d="m43.65 25 13.75-23.8c-1.35-.8-2.9-1.2-4.5-1.2h-18.5c-1.6 0-3.15.45-4.5 1.2z" fill="#00832d" />
        <path d="m59.8 53h-32.3l-13.75 23.8c1.35.8 2.9 1.2 4.5 1.2h50.8c1.6 0 3.15-.45 4.5-1.2z" fill="#2684fc" />
        <path d="m73.4 26.5-12.7-22c-.8-1.4-1.95-2.5-3.3-3.3l-13.75 23.8 16.15 28h27.45c0-1.55-.4-3.1-1.2-4.5z" fill="#ffba00" />
      </svg>
      Add to Google Drive
    </button>
    <p v-if="!isConfigured" class="text-xs text-slate-400">Google Drive isn’t set up yet.</p>
    <p v-else-if="message" class="text-xs" :class="errored ? 'text-red-600' : 'text-green-700'">{{ message }}</p>

    <DriveFolderPicker
      v-if="open"
      :files="props.files"
      :count="props.count"
      @uploaded="onUploaded"
      @close="open = false"
    />
  </div>
</template>
