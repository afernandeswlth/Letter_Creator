import { runEngine } from '~~/server/utils/engine'

/**
 * POST /api/letters/render
 * Multipart: files[] = funder .docx, brand, ddBsb, ddAccount.
 * Returns each party's fully merged letter text (ready for preview / PDF).
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
    return await runEngine('render', files, {
      brand: field('brand') ?? 'wlth',
      ddBsb: field('ddBsb') ?? '',
      ddAccount: field('ddAccount') ?? '',
    })
  } catch (err) {
    throw createError({ statusCode: 500, statusMessage: `Engine error: ${(err as Error).message}` })
  }
})
