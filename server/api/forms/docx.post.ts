import { runEngineFormDocx } from '~~/server/utils/engine'

/** POST /api/forms/docx — { letterType, brand, values, filename } → .docx bytes */
export default defineEventHandler(async (event) => {
  const body = await readBody<{
    letterType: string; brand?: string; values?: Record<string, string>; filename?: string
  }>(event)
  try {
    const docx = await runEngineFormDocx(body.letterType, body.brand ?? 'wlth', body.values ?? {})
    const filename = (body.filename || 'Letter').trim()
    setHeader(event, 'Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    setHeader(event, 'Content-Disposition', `attachment; filename="${filename}.docx"`)
    return docx
  } catch (err) {
    throw createError({ statusCode: 500, statusMessage: `Engine error: ${(err as Error).message}` })
  }
})
