import { runEngineZip } from '~~/server/utils/engine'

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

  let zip: Buffer
  try {
    zip = await runEngineZip(files, {
      brand: field('brand') ?? 'wlth',
      ddBsb: field('ddBsb') ?? '',
      ddAccount: field('ddAccount') ?? '',
    })
  } catch (err) {
    throw createError({ statusCode: 500, statusMessage: `Engine error: ${(err as Error).message}` })
  }

  const safe = (field('name') || 'Welcome Letters').replace(/[^\w .-]+/g, '').trim()
  setHeader(event, 'Content-Type', 'application/zip')
  setHeader(event, 'Content-Disposition', `attachment; filename="${safe}.zip"`)
  return zip
})
