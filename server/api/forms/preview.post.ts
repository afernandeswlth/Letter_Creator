import { runEngineFormPreview } from '~~/server/utils/engine'

/** POST /api/forms/preview — { letterType, brand, values } → { pages: dataURL[] } */
export default defineEventHandler(async (event) => {
  const body = await readBody<{ letterType: string; brand?: string; values?: Record<string, unknown> }>(event)
  try {
    return await runEngineFormPreview(body.letterType, body.brand ?? 'wlth', body.values ?? {})
  } catch (err) {
    throw createError({ statusCode: 500, statusMessage: `Engine error: ${(err as Error).message}` })
  }
})
