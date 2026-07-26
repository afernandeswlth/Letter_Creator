import { runEnginePdf } from '~~/server/utils/engine'

/**
 * POST /api/letters/pdf
 * Multipart: files[] = funder .docx, brand, ddBsb, ddAccount, partyIndex, name.
 * Returns the branded PDF for one party (WLTH letterhead, tables, footer).
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

  let pdf: Buffer
  try {
    pdf = await runEnginePdf(files, {
      brand: field('brand') ?? 'wlth',
      ddBsb: field('ddBsb') ?? '',
      ddAccount: field('ddAccount') ?? '',
      partyIndex: Number(field('partyIndex') ?? '0'),
    })
  } catch (err) {
    throw createError({ statusCode: 500, statusMessage: `Engine error: ${(err as Error).message}` })
  }

  const safe = (field('name') ?? 'WLTH Welcome Letter').replace(/[^\w .-]+/g, '').trim()
  setHeader(event, 'Content-Type', 'application/pdf')
  setHeader(event, 'Content-Disposition', `attachment; filename="${safe}.pdf"`)
  return pdf
})
