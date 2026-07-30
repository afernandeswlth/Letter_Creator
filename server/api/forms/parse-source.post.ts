import { runEngineFormParse } from '~~/server/utils/engine'

/** POST /api/forms/parse-source — multipart (file, letterType, brand) →
 *  { values } extracted from the uploaded source document. */
export default defineEventHandler(async (event) => {
  const parts = (await readMultipartFormData(event)) ?? []
  const file = parts.find((p) => p.filename && p.name === 'file')
  const field = (n: string) => parts.find((p) => p.name === n && !p.filename)?.data.toString('utf-8')
  if (!file) throw createError({ statusCode: 400, statusMessage: 'No file uploaded' })
  try {
    return await runEngineFormParse(field('letterType') ?? '', field('brand') ?? 'wlth', {
      filename: file.filename as string,
      data: file.data,
    })
  } catch (err) {
    throw createError({ statusCode: 500, statusMessage: `Engine error: ${(err as Error).message}` })
  }
})
