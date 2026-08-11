<script setup lang="ts">
import type { DriveFile, DriveFolder } from '~/composables/useGoogleDrive'

/**
 * Custom Google Drive folder chooser. Browses My Drive, Shared Drives and
 * "Shared with me", with a Back button + breadcrumb, a tick on the folder that
 * will receive the letters, and an "Upload here" action. Replaces Google's
 * (non-customisable) Picker.
 */
const props = defineProps<{
  files: () => Promise<DriveFile[]>
  count: number // how many letters will be uploaded (for the button label)
}>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'uploaded', payload: { folderName: string; count: number }): void
}>()

const { authorize, listSharedDrives, listFolders, listSharedWithMe, searchFolders, createFolder, uploadFiles } = useGoogleDrive()

type Kind = 'roots' | 'myDrive' | 'sharedWithMe' | 'sharedDrive' | 'folder'
interface Node { id: string; name: string; kind: Kind; driveId?: string }

const stack = ref<Node[]>([]) // breadcrumb path; empty = roots
const items = ref<Node[]>([]) // folders/entries shown in the current level
const loading = ref(true)
const error = ref('')
const uploading = ref(false)
const progress = ref('')

// Search across all drives (independent of where you're browsing).
const query = ref('')
const inSearch = ref(false)

// Create-a-folder state.
const creating = ref(false)
const newName = ref('')
const savingFolder = ref(false)

const current = computed<Node | null>(() => stack.value[stack.value.length - 1] ?? null)
// You can drop files into a real folder, My Drive, or a Shared Drive root —
// but not the top-level category list or the "Shared with me" grouping.
const canUploadHere = computed(
  () => !inSearch.value && current.value != null && ['myDrive', 'sharedDrive', 'folder'].includes(current.value.kind),
)

async function runSearch() {
  const q = query.value.trim()
  if (!q) return clearSearch()
  inSearch.value = true
  creating.value = false
  loading.value = true
  error.value = ''
  try {
    const folders = await searchFolders(q)
    items.value = folders.map((f): Node => ({ id: f.id, name: f.name, kind: 'folder', driveId: f.driveId }))
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}
function clearSearch() {
  query.value = ''
  if (!inSearch.value) return
  inSearch.value = false
  const c = current.value
  if (c) loadChildren(c)
  else loadRoots()
}
// Open a search result: jump straight into that folder as the upload target.
function openResult(node: Node) {
  inSearch.value = false
  query.value = ''
  stack.value = [node]
  loadChildren(node)
}

async function loadRoots() {
  loading.value = true
  error.value = ''
  creating.value = false
  try {
    const drives = await listSharedDrives()
    items.value = [
      { id: 'root', name: 'My Drive', kind: 'myDrive' },
      { id: 'sharedWithMe', name: 'Shared with me', kind: 'sharedWithMe' },
      ...drives.map((d: DriveFolder): Node => ({ id: d.id, name: d.name, kind: 'sharedDrive', driveId: d.id })),
    ]
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

async function loadChildren(node: Node) {
  loading.value = true
  error.value = ''
  creating.value = false
  try {
    let folders: DriveFolder[] = []
    if (node.kind === 'myDrive') folders = await listFolders('root')
    else if (node.kind === 'sharedWithMe') folders = await listSharedWithMe()
    else if (node.kind === 'sharedDrive') folders = await listFolders(node.driveId!, node.driveId)
    else folders = await listFolders(node.id, node.driveId)
    items.value = folders.map((f): Node => ({ id: f.id, name: f.name, kind: 'folder', driveId: node.driveId }))
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

function open(node: Node) {
  stack.value = [...stack.value, node]
  loadChildren(node)
}
function back() {
  stack.value = stack.value.slice(0, -1)
  const c = current.value
  if (c) loadChildren(c)
  else loadRoots()
}
function goTo(index: number) {
  // -1 = roots
  stack.value = index < 0 ? [] : stack.value.slice(0, index + 1)
  const c = current.value
  if (c) loadChildren(c)
  else loadRoots()
}

async function createNewFolder() {
  const name = newName.value.trim()
  if (!name || !current.value || savingFolder.value) return
  savingFolder.value = true
  error.value = ''
  try {
    const folder = await createFolder(name, current.value.id)
    newName.value = ''
    // Jump into the new folder so it's the upload target, ready to go.
    open({ id: folder.id, name: folder.name, kind: 'folder', driveId: current.value.driveId })
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    savingFolder.value = false
  }
}

async function uploadHere() {
  if (!canUploadHere.value || !current.value || uploading.value) return
  uploading.value = true
  error.value = ''
  progress.value = ''
  try {
    const files = await props.files()
    if (!files.length) throw new Error('There are no letters to upload.')
    await uploadFiles(current.value.id, files, (done, total) => {
      progress.value = total > 1 ? `Uploading ${done}/${total}…` : 'Uploading…'
    })
    emit('uploaded', { folderName: current.value.name, count: files.length })
  } catch (e) {
    error.value = (e as Error).message || 'Could not upload to Google Drive.'
  } finally {
    uploading.value = false
  }
}

onMounted(async () => {
  try {
    await authorize() // one-time Google consent
    await loadRoots()
  } catch (e) {
    loading.value = false
    error.value = (e as Error).message === 'access_denied'
      ? 'Google access was declined. Grant access to save to Drive.'
      : `Could not connect to Google Drive. ${(e as Error).message}`
  }
})
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-slate-900/40" @click="!uploading && emit('close')" />
    <div class="relative flex max-h-[80vh] w-full max-w-lg flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <h3 class="text-base font-semibold text-slate-900">Choose a folder</h3>
        <button type="button" class="rounded-lg p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600" aria-label="Close" @click="emit('close')">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6l12 12M18 6L6 18" /></svg>
        </button>
      </div>

      <!-- Breadcrumb + Back -->
      <div class="flex items-center gap-2 border-b border-slate-100 px-5 py-2.5 text-sm">
        <button
          type="button"
          class="inline-flex items-center gap-1 rounded-md px-2 py-1 font-medium text-slate-600 transition hover:bg-slate-100 disabled:opacity-40"
          :disabled="!stack.length || uploading"
          @click="back"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6" /></svg>
          Back
        </button>
        <div class="flex min-w-0 flex-1 items-center gap-1 overflow-x-auto whitespace-nowrap text-slate-500">
          <button type="button" class="rounded px-1 hover:text-slate-700" @click="goTo(-1)">Drive</button>
          <template v-for="(node, i) in stack" :key="node.id + i">
            <span class="text-slate-300">/</span>
            <button type="button" class="max-w-[10rem] truncate rounded px-1 hover:text-slate-700" :class="i === stack.length - 1 ? 'font-semibold text-slate-800' : ''" @click="goTo(i)">{{ node.name }}</button>
          </template>
        </div>
      </div>

      <!-- Search -->
      <div class="flex items-center gap-2 border-b border-slate-100 px-5 py-2.5">
        <div class="relative flex-1">
          <svg class="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>
          <input
            v-model="query"
            type="text"
            placeholder="Search folders…"
            class="w-full rounded-lg border border-slate-300 py-1.5 pl-8 pr-8 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            @keyup.enter="runSearch"
          />
          <button v-if="query" type="button" class="absolute right-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-slate-400 hover:text-slate-600" aria-label="Clear search" @click="clearSearch">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6l12 12M18 6L6 18" /></svg>
          </button>
        </div>
        <button type="button" class="rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-200" @click="runSearch">Search</button>
      </div>

      <!-- Target banner (the tick — where the letters will land) -->
      <div v-if="canUploadHere" class="flex items-center gap-2 bg-emerald-50 px-5 py-2.5 text-sm text-emerald-800">
        <svg class="h-4 w-4 flex-none text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5" /></svg>
        Letters will be saved to <span class="font-semibold">{{ current?.name }}</span>
      </div>

      <!-- Folder list -->
      <div class="min-h-[12rem] flex-1 overflow-y-auto px-2 py-2">
        <div v-if="loading" class="flex items-center justify-center py-12 text-sm text-slate-400">
          <svg class="mr-2 h-5 w-5 animate-spin text-blue-600" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
          Loading…
        </div>
        <p v-else-if="error" class="px-3 py-10 text-center text-sm text-red-600">{{ error }}</p>
        <p v-else-if="inSearch && !items.length" class="px-3 py-10 text-center text-sm text-slate-400">
          No folders match “{{ query }}”.
        </p>
        <p v-else-if="!items.length" class="px-3 py-10 text-center text-sm text-slate-400">
          No sub-folders here{{ canUploadHere ? ' — you can save into this folder.' : '.' }}
        </p>
        <ul v-else class="space-y-0.5">
          <li v-if="inSearch" class="px-3 pb-1 pt-1 text-[11px] font-medium uppercase tracking-wide text-slate-400">Search results</li>
          <li v-for="node in items" :key="node.id">
            <button
              type="button"
              class="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
              :disabled="uploading"
              @click="inSearch ? openResult(node) : open(node)"
            >
              <DriveKindIcon :kind="node.kind" class="h-5 w-5 flex-none text-[#5f6368]" />
              <span class="flex-1 truncate">{{ node.name }}</span>
              <svg class="h-4 w-4 flex-none text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6" /></svg>
            </button>
          </li>
        </ul>
      </div>

      <!-- Create a new folder inside the current one -->
      <div v-if="canUploadHere && !inSearch" class="border-t border-slate-100 px-5 py-2.5">
        <button
          v-if="!creating"
          type="button"
          class="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 transition hover:text-blue-700"
          @click="creating = true; newName = ''"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14" /></svg>
          New folder
        </button>
        <div v-else class="flex items-center gap-2">
          <input
            v-model="newName"
            type="text"
            :placeholder="`New folder in ${current?.name}`"
            class="flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            @keyup.enter="createNewFolder"
          />
          <button
            type="button"
            class="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-40"
            :disabled="!newName.trim() || savingFolder"
            @click="createNewFolder"
          >
            {{ savingFolder ? 'Creating…' : 'Create' }}
          </button>
          <button
            type="button"
            class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-40"
            :disabled="savingFolder"
            @click="creating = false"
          >
            Cancel
          </button>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-between gap-3 border-t border-slate-200 px-5 py-4">
        <p v-if="progress" class="text-xs text-slate-500">{{ progress }}</p>
        <span v-else />
        <div class="flex items-center gap-3">
          <button type="button" class="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-40" :disabled="uploading" @click="emit('close')">Cancel</button>
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="!canUploadHere || uploading"
            @click="uploadHere"
          >
            <svg v-if="uploading" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
            </svg>
            {{ uploading ? 'Uploading…' : `Upload ${props.count} letter${props.count === 1 ? '' : 's'} here` }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
