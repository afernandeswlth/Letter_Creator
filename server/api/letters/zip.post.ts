import { runEngine, runEngineZip, runEnginePdf } from '~~/server/utils/engine'
import { isConfigured, saveLetter } from '~~/server/utils/letterStore'

/**
 * POST /api/letters/zip
 * Multipart: files[] = funder .docx, brand, ddBsb, ddAccount, name (zip base name).
 * Returns a ZIP of every party's branded PDF.
 */
export default defineEventHandler(async (event) => {
  const parts = (await readMultipartFormData(event)) ?? []
  const files = parts
    .filter((p) => p.filename && p.name === 'files')
    .map((p) => ({ filename: p.filename as string, data: p.data }))
  const field = (n: string) =>
    parts.find((p) => p.name === n && !p.filename)?.data.toString('utf-8')

  if (!files.length) {
    throw createError({ statusCode: 400, statusMessage: 'No .docx files found' })
  }

  const brand = field('brand') ?? 'wlth'
  const ddBsb = field('ddBsb') ?? ''
  const ddAccount = field('ddAccount') ?? ''
  const format = field('format') ?? 'both'

  let zip: Buffer
  try {
    zip = await runEngineZip(files, { brand, ddBsb, ddAccount, format })
  } catch (err) {
    throw createError({ statusCode: 500, statusMessage: `Engine error: ${(err as Error).message}` })
  }

  // Record each party's letter in the history (best-effort; only re-render the
  // per-party PDFs when a store is configured).
  if (isConfigured() && format !== 'docx') {
    try {
      const label = brand === 'mma' ? 'MMA' : 'WLTH'
      const { parties } = await runEngine('parse', files, { brand, ddBsb, ddAccount })
      for (let i = 0; i < parties.length; i++) {
        const name = parties[i].name.replace(/^(mr|mrs|ms|miss|dr)\.?\s+/i, '')
        const pdf = await runEnginePdf(files, { brand, ddBsb, ddAccount, partyIndex: i })
        await saveLetter(
          { letterType: 'welcome', brand, customer: name, reference: parties[i].loanFacilityNumber ?? null },
          pdf, `${label} Welcome Letter - ${name}`, 'Completed',
        )
      }
    } catch (err) {
      console.warn('[letters/zip] history save skipped:', (err as Error).message)
    }
  }

  const safe = (field('name') || 'Welcome Letters').replace(/[^\w .-]+/g, '').trim()
  setHeader(event, 'Content-Type', 'application/zip')
  setHeader(event, 'Content-Disposition', `attachment; filename="${safe}.zip"`)
  return zip
})
