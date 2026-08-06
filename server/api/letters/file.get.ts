import { signedUrl } from '~~/server/utils/letterStore'

/** GET /api/letters/file?id=<uuid> — a short-lived signed download URL. */
export default defineEventHandler(async (event) => {
  const id = String(getQuery(event).id ?? '').trim()
  if (!id) throw createError({ statusCode: 400, statusMessage: 'Missing id' })
  const url = await signedUrl(id)
  if (!url) throw createError({ statusCode: 404, statusMessage: 'Not found' })
  return { url }
})
