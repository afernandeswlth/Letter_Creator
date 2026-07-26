import { runEnginePreview } from '~~/server/utils/engine'

/**
 * POST /api/letters/preview
 * Multipart: files[] = funder .docx, brand, ddBsb, ddAccount, partyIndex.
 * Returns { pages: string[] } — the branded PDF rasterised to page images
 * (data URLs) so the letter renders in the browser without a PDF plugin.
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
  try {
    return await runEnginePreview(files, {
      brand: field('brand') ?? 'wlth',
      ddBsb: field('ddBsb') ?? '',
      ddAccount: field('ddAccount') ?? '',
      partyIndex: Number(field('partyIndex') ?? '0'),
    })
  } catch (err) {
    throw createError({ statusCode: 500, statusMessage: `Engine error: ${(err as Error).message}` })
  }
})
