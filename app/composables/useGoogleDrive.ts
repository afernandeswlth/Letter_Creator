/**
 * Google Drive integration for the "Add to Drive" button — a CUSTOM folder
 * chooser (see DriveFolderPicker.vue) rather than Google's Picker, so we control
 * the UX (Back button, a tick on the selected folder, "upload to this folder").
 *
 * Flow: load Google Identity Services on demand → request a Drive access token
 * (a one-time consent) → list folders via the Drive REST API as the user browses
 * → upload each PDF into the chosen folder.
 *
 * Scope note: browsing arbitrary folders and writing into the one the user picks
 * needs full `drive` scope (the narrow `drive.file` scope only covers files the
 * app itself created). For an *Internal* Workspace app this needs no Google
 * review. Only the OAuth client id is required now (no API key).
 *
 * Config (public, from NUXT_PUBLIC_GOOGLE_* / nuxt.config defaults):
 *   googleClientId — OAuth 2.0 Web client id
 */
const GSI_SRC = 'https://accounts.google.com/gsi/client'
const DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive'
const FOLDER_MIME = 'application/vnd.google-apps.folder'
const API = 'https://www.googleapis.com/drive/v3'

export interface DriveFile {
  name: string
  blob: Blob
}
export interface DriveFolder {
  id: string
  name: string
  driveId?: string // set when the folder lives in a Shared Drive
}

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) return resolve()
    const s = document.createElement('script')
    s.src = src
    s.async = true
    s.defer = true
    s.onload = () => resolve()
    s.onerror = () => reject(new Error(`Could not load ${src}`))
    document.head.appendChild(s)
  })
}

export function useGoogleDrive() {
  const cfg = useRuntimeConfig().public
  const clientId = cfg.googleClientId as string
  const isConfigured = computed(() => Boolean(clientId))

  let tokenClient: any = null
  let accessToken = ''

  /** Load GIS + obtain a Drive access token (prompts for consent the first time). */
  async function authorize(): Promise<string> {
    await loadScript(GSI_SRC)
    return new Promise((resolve, reject) => {
      const google = (window as any).google
      if (!tokenClient) {
        tokenClient = google.accounts.oauth2.initTokenClient({
          client_id: clientId,
          scope: DRIVE_SCOPE,
          callback: () => {},
        })
      }
      tokenClient.callback = (resp: any) => {
        if (resp.error) return reject(new Error(resp.error))
        accessToken = resp.access_token
        resolve(accessToken)
      }
      tokenClient.requestAccessToken({ prompt: accessToken ? '' : 'consent' })
    })
  }

  function authHeaders() {
    return { Authorization: `Bearer ${accessToken}` }
  }

  async function driveGet(path: string, params: Record<string, string>) {
    const qs = new URLSearchParams(params).toString()
    const res = await fetch(`${API}${path}?${qs}`, { headers: authHeaders() })
    if (!res.ok) {
      const text = await res.text().catch(() => '')
      throw new Error(`Drive request failed (${res.status}). ${text.slice(0, 160)}`)
    }
    return res.json()
  }

  /** Shared Drives the user can access (empty if none / not available). */
  async function listSharedDrives(): Promise<DriveFolder[]> {
    try {
      const j = await driveGet('/drives', { pageSize: '100', fields: 'drives(id,name)' })
      return j.drives ?? []
    } catch {
      return []
    }
  }

  /** Folders directly inside `parentId`. Pass `driveId` when inside a Shared Drive. */
  async function listFolders(parentId: string, driveId?: string): Promise<DriveFolder[]> {
    const params: Record<string, string> = {
      q: `'${parentId}' in parents and mimeType = '${FOLDER_MIME}' and trashed = false`,
      fields: 'files(id,name)',
      orderBy: 'name',
      pageSize: '200',
      supportsAllDrives: 'true',
      includeItemsFromAllDrives: 'true',
    }
    if (driveId) {
      params.corpora = 'drive'
      params.driveId = driveId
    }
    const j = await driveGet('/files', params)
    return j.files ?? []
  }

  /** Search folders by name across My Drive and all accessible Shared Drives. */
  async function searchFolders(query: string): Promise<DriveFolder[]> {
    const safe = query.replace(/['\\]/g, '\\$&')
    const j = await driveGet('/files', {
      q: `name contains '${safe}' and mimeType = '${FOLDER_MIME}' and trashed = false`,
      fields: 'files(id,name,driveId)',
      pageSize: '50',
      corpora: 'allDrives',
      supportsAllDrives: 'true',
      includeItemsFromAllDrives: 'true',
    })
    return j.files ?? []
  }

  /** Folders shared directly with the user ("Shared with me"). */
  async function listSharedWithMe(): Promise<DriveFolder[]> {
    const j = await driveGet('/files', {
      q: `sharedWithMe and mimeType = '${FOLDER_MIME}' and trashed = false`,
      fields: 'files(id,name)',
      orderBy: 'name',
      pageSize: '200',
      supportsAllDrives: 'true',
      includeItemsFromAllDrives: 'true',
    })
    return j.files ?? []
  }

  async function uploadFile(folderId: string, file: DriveFile) {
    const metadata = { name: file.name, parents: [folderId], mimeType: 'application/pdf' }
    const form = new FormData()
    form.append('metadata', new Blob([JSON.stringify(metadata)], { type: 'application/json' }))
    form.append('file', file.blob)
    const res = await fetch(
      'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true',
      { method: 'POST', headers: authHeaders(), body: form },
    )
    if (!res.ok) {
      const text = await res.text().catch(() => '')
      throw new Error(`Upload failed (${res.status}). ${text.slice(0, 160)}`)
    }
    return res.json()
  }

  /** Upload every file into `folderId`, reporting progress. */
  async function uploadFiles(
    folderId: string,
    files: DriveFile[],
    onProgress?: (done: number, total: number) => void,
  ): Promise<number> {
    let done = 0
    for (const f of files) {
      await uploadFile(folderId, f)
      done += 1
      onProgress?.(done, files.length)
    }
    return done
  }

  return {
    isConfigured,
    authorize,
    listSharedDrives,
    listFolders,
    listSharedWithMe,
    searchFolders,
    uploadFiles,
  }
}
