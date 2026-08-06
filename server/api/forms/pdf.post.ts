import { runEngineFormPdf } from '~~/server/utils/engine'
import { formMeta, saveLetter } from '~~/server/utils/letterStore'

/** POST /api/forms/pdf — { letterType, brand, values, filename } → PDF bytes */
export default defineEventHandler(async (event) => {
  const body = await readBody<{
    letterType: string; brand?: string; values?: Record<string, string>; filename?: string
  }>(event)
  try {
    const brand = body.brand ?? 'wlth'
    const values = body.values ?? {}
    const filename = (body.filename || 'Letter').trim()
    const pdf = await runEngineFormPdf(body.letterType, brand, values)
    // Blank template downloads (no field values) are not real letters — skip.
    if (Object.keys(values).length) {
      await saveLetter(formMeta(body.letterType, brand, values), pdf, filename, 'Completed')
    }
    setHeader(event, 'Content-Type', 'application/pdf')
    setHeader(event, 'Content-Disposition', `attachment; filename="${filename}.pdf"`)
    return pdf
  } catch (err) {
    throw createError({ statusCode: 500, statusMessage: `Engine error: ${(err as Error).message}` })
  }
})
