import type { BrandId, DeliveryResult, EngineResult, LetterRecord } from '~/types'

/**
 * Front-end API layer.
 *
 * `parseFunderDocs` and `renderLetters` call the REAL Nitro endpoints backed by
 * the Python letter engine. Drive/email/recent-letters are still mocked until
 * those integrations are wired.
 */

function delay<T>(value: T, ms = 500): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms))
}

let idCounter = 0
function makeId(prefix: string): string {
  idCounter += 1
  return `${prefix}_${idCounter}_${Math.random().toString(36).slice(2, 8)}`
}

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
    template: 'Offset' | 'Standard',
  ): Promise<DeliveryResult> {
    const res = await $fetch<{ link: string; to: string; via: string }>('/api/letters/email', {
      method: 'POST',
      body: formData(files, {
        brand: brand === 'mortgage-mart' ? 'mma' : 'wlth',
        ddBsb,
        ddAccount,
        partyIndex: String(partyIndex),
        to,
        name,
        filename,
        template,
      }),
    })
    return {
      ok: true,
      message:
        res.via === 'zapier'
          ? `Sent to Zapier for ${res.to} (${template} template) — check hello@wlth.com Drafts.`
          : `Draft created for ${res.to} (${template} template).`,
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

  /** GET /api/letters — recent letters for the dashboard table (mock). */
  async function getRecentLetters(): Promise<LetterRecord[]> {
    return delay([
      { id: 'l1', borrowerName: 'A&M Stevens Pty Ltd (SMSF)', template: 'WLTH Welcome Letter', status: 'Completed', createdAt: '24 Jun 2026, 6:52 PM' },
      { id: 'l2', borrowerName: 'Mr Matthew Stevens', template: 'WLTH Welcome Letter', status: 'Sent', createdAt: '24 Jun 2026, 6:52 PM' },
      { id: 'l3', borrowerName: 'Mrs Ashleigh Stevens', template: 'WLTH Welcome Letter', status: 'Draft', createdAt: '24 Jun 2026, 6:51 PM' },
    ])
  }

  return { parseFunderDocs, renderLetters, previewPages, fetchPdf, downloadPdf, downloadZip, createEmailDraft, getRecentLetters }
}
