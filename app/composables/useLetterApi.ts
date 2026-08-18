import type { BrandId, DeliveryResult, EngineResult, LetterRecord } from '~/types'

/**
 * Front-end API layer.
 *
 * These call the REAL Nitro endpoints (locally) / Flask (production), backed by
 * the Python letter engine and, for history, Supabase.
 */

function formData(files: File[], fields: Record<string, string> = {}): FormData {
  const fd = new FormData()
  for (const f of files) fd.append('files', f, f.name)
  for (const [k, v] of Object.entries(fields)) fd.append(k, v)
  return fd
}

export function useLetterApi() {
  /** POST /api/letters/parse — detect loan type + parties from funder docs. */
  async function parseFunderDocs(files: File[]): Promise<EngineResult> {
    return $fetch<EngineResult>('/api/letters/parse', {
      method: 'POST',
      body: formData(files),
    })
  }

  /** POST /api/letters/render — merge each party's letter (brand + BSB/account). */
  async function renderLetters(
    files: File[],
    brand: BrandId,
    ddBsb: string,
    ddAccount: string,
  ): Promise<EngineResult> {
    return $fetch<EngineResult>('/api/letters/render', {
      method: 'POST',
      body: formData(files, { brand: brand === 'mortgage-mart' ? 'mma' : 'wlth', ddBsb, ddAccount }),
    })
  }

  /** POST /api/letters/zip — download a ZIP of every party's branded PDF. */
  async function downloadZip(
    files: File[],
    brand: BrandId,
    ddBsb: string,
    ddAccount: string,
    name: string,
  ): Promise<void> {
    const blob = await $fetch<Blob>('/api/letters/zip', {
      method: 'POST',
      body: formData(files, {
        brand: brand === 'mortgage-mart' ? 'mma' : 'wlth',
        ddBsb,
        ddAccount,
        name,
      }),
      responseType: 'blob',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${name}.zip`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  /** POST /api/letters/email — create a Gmail DRAFT (letter attached) in the
   *  hello@wlth.com inbox. `template` is chosen from the "linked to offset" answer. */
  async function createEmailDraft(
    files: File[],
    brand: BrandId,
    ddBsb: string,
    ddAccount: string,
    partyIndex: number,
    to: string,
    name: string,
    filename: string,
    opts: { offset: 'yes' | 'no'; isTrust: boolean; trustName: string; accountNumber: string },
    cc?: string,
  ): Promise<DeliveryResult> {
    const res = await $fetch<{ link: string; to: string; cc?: string; via: string }>('/api/letters/email', {
      method: 'POST',
      body: formData(files, {
        brand: brand === 'mortgage-mart' ? 'mma' : 'wlth',
        ddBsb,
        ddAccount,
        partyIndex: String(partyIndex),
        to,
        name,
        filename,
        offset: opts.offset,
        isTrust: String(opts.isTrust),
        trustName: opts.trustName,
        accountNumber: opts.accountNumber,
        ...(cc ? { cc } : {}),
      }),
    })
    const withForm = opts.offset === 'no' ? ' (with nomination form)' : ''
    const ccNote = res.cc ? `, Cc ${res.cc}` : ''
    return {
      ok: true,
      message:
        res.via === 'zapier'
          ? `Sent to Zapier for ${res.to}${ccNote}${withForm} — check hello@wlth.com Drafts.`
          : `Draft created for ${res.to}${ccNote}${withForm}.`,
      link: res.link,
    }
  }

  /** POST /api/letters/preview — branded PDF rasterised to page images (data URLs). */
  async function previewPages(
    files: File[],
    brand: BrandId,
    ddBsb: string,
    ddAccount: string,
    partyIndex: number,
  ): Promise<string[]> {
    const res = await $fetch<{ pages: string[] }>('/api/letters/preview', {
      method: 'POST',
      body: formData(files, {
        brand: brand === 'mortgage-mart' ? 'mma' : 'wlth',
        ddBsb,
        ddAccount,
        partyIndex: String(partyIndex),
      }),
    })
    return res.pages
  }

  /** POST /api/letters/pdf — fetch the branded PDF for one party as a Blob. */
  async function fetchPdf(
    files: File[],
    brand: BrandId,
    ddBsb: string,
    ddAccount: string,
    partyIndex: number,
    name = 'Welcome Letter',
  ): Promise<Blob> {
    const fd = formData(files, {
      brand: brand === 'mortgage-mart' ? 'mma' : 'wlth',
      ddBsb,
      ddAccount,
      partyIndex: String(partyIndex),
      name,
    })
    return $fetch<Blob>('/api/letters/pdf', { method: 'POST', body: fd, responseType: 'blob' })
  }

  /** POST /api/letters/docx — one party's Welcome letter as an editable Word doc. */
  async function fetchWelcomeDocx(
    files: File[],
    brand: BrandId,
    ddBsb: string,
    ddAccount: string,
    partyIndex: number,
    name = 'Welcome Letter',
  ): Promise<Blob> {
    const fd = formData(files, {
      brand: brand === 'mortgage-mart' ? 'mma' : 'wlth',
      ddBsb,
      ddAccount,
      partyIndex: String(partyIndex),
      name,
    })
    return $fetch<Blob>('/api/letters/docx', { method: 'POST', body: fd, responseType: 'blob' })
  }

  /** Download the branded PDF for one party. */
  async function downloadPdf(
    files: File[],
    brand: BrandId,
    ddBsb: string,
    ddAccount: string,
    partyIndex: number,
    name: string,
  ): Promise<void> {
    const blob = await fetchPdf(files, brand, ddBsb, ddAccount, partyIndex, name)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${name}.pdf` // `name` is already the full "WLTH Welcome Letter - …" base
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  // --- form-driven letter types (Formal Approval, etc.) -------------------
  const engineBrand = (brand: BrandId) => (brand === 'mortgage-mart' ? 'mma' : 'wlth')

  /** POST /api/forms/parse-source — extract field values from an uploaded
   *  source document (e.g. a Schedule 4) to auto-fill a form letter. */
  async function parseFormSource(
    letterType: string,
    brand: BrandId,
    file: File,
  ): Promise<Record<string, string>> {
    const fd = new FormData()
    fd.append('file', file, file.name)
    fd.append('letterType', letterType)
    fd.append('brand', engineBrand(brand))
    const res = await $fetch<{ values: Record<string, string> }>('/api/forms/parse-source', {
      method: 'POST',
      body: fd,
    })
    return res.values ?? {}
  }

  /** POST /api/forms/preview — rasterised page images for a form letter. */
  async function formPreview(
    letterType: string,
    brand: BrandId,
    values: Record<string, string>,
  ): Promise<string[]> {
    const res = await $fetch<{ pages: string[] }>('/api/forms/preview', {
      method: 'POST',
      body: { letterType, brand: engineBrand(brand), values },
    })
    return res.pages
  }

  /** POST /api/forms/pdf — fetch a form letter's branded PDF as a Blob. */
  async function fetchFormPdfBlob(
    letterType: string,
    brand: BrandId,
    values: Record<string, string>,
    filename: string,
  ): Promise<Blob> {
    return $fetch<Blob>('/api/forms/pdf', {
      method: 'POST',
      body: { letterType, brand: engineBrand(brand), values, filename },
      responseType: 'blob',
    })
  }

  /** POST /api/forms/pdf — download a form letter's branded PDF. */
  async function downloadFormPdf(
    letterType: string,
    brand: BrandId,
    values: Record<string, string>,
    filename: string,
  ): Promise<void> {
    const blob = await fetchFormPdfBlob(letterType, brand, values, filename)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${filename}.pdf`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  /** POST /api/forms/docx — fetch a form letter's editable Word doc as a Blob. */
  async function fetchFormDocxBlob(
    letterType: string,
    brand: BrandId,
    values: Record<string, string>,
    filename: string,
  ): Promise<Blob> {
    return $fetch<Blob>('/api/forms/docx', {
      method: 'POST',
      body: { letterType, brand: engineBrand(brand), values, filename },
      responseType: 'blob',
    })
  }

  /** POST /api/forms/docx — download a form letter as an editable Word doc. */
  async function downloadFormDocx(
    letterType: string,
    brand: BrandId,
    values: Record<string, string>,
    filename: string,
  ): Promise<void> {
    const blob = await fetchFormDocxBlob(letterType, brand, values, filename)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${filename}.docx`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  /** POST /api/forms/email — create a Gmail draft for a form letter. */
  async function createFormEmailDraft(
    letterType: string,
    brand: BrandId,
    values: Record<string, string>,
    to: string,
    filename: string,
    cc?: string,
  ): Promise<DeliveryResult> {
    const res = await $fetch<{ link: string; to: string; cc?: string; from?: string; via: string }>('/api/forms/email', {
      method: 'POST',
      body: { letterType, brand: engineBrand(brand), values, to, cc, filename },
    })
    const where = res.from ? `${res.from} Drafts` : 'Drafts'
    return {
      ok: true,
      message: `Draft created in ${where} — To ${res.to}${res.cc ? `, Cc ${res.cc}` : ''}. Review and send from Gmail.`,
      link: res.link,
    }
  }

  /** GET /api/letters/recent — recent letters for the dashboard table. */
  async function getRecentLetters(limit = 20): Promise<LetterRecord[]> {
    const res = await $fetch<{ letters: LetterRecord[] }>('/api/letters/recent', {
      params: { limit },
    })
    return res.letters ?? []
  }

  /** Open the stored PDF for a saved letter via a short-lived signed URL. */
  async function downloadStoredLetter(id: string): Promise<void> {
    const { url } = await $fetch<{ url: string }>('/api/letters/file', { params: { id } })
    window.open(url, '_blank', 'noopener')
  }

  return { parseFunderDocs, renderLetters, previewPages, fetchPdf, fetchWelcomeDocx, downloadPdf, downloadZip, createEmailDraft, parseFormSource, formPreview, downloadFormPdf, fetchFormPdfBlob, downloadFormDocx, fetchFormDocxBlob, createFormEmailDraft, getRecentLetters, downloadStoredLetter }
}
