import { runEngineFormPdf } from '~~/server/utils/engine'

/** POST /api/forms/pdf — { letterType, brand, values, filename } → PDF bytes */
export default defineEventHandler(async (event) => {
  const body = await readBody<{
    letterType: string; brand?: string; values?: Record<string, unknown>; filename?: string
  }>(event)
  try {
    const pdf = await runEngineFormPdf(body.letterType, body.brand ?? 'wlth', body.values ?? {})
    setHeader(event, 'Content-Type', 'application/pdf')
    setHeader(event, 'Content-Disposition', `attachment; filename="${(body.filename || 'Letter')}.pdf"`)
    return pdf
  } catch (err) {
    throw createError({ statusCode: 500, statusMessage: `Engine error: ${(err as Error).message}` })
  }
})
