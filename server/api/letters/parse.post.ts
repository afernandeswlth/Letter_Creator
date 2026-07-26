import { runEngine } from '~~/server/utils/engine'

export default defineEventHandler(async (event) => {
  const parts = (await readMultipartFormData(event)) ?? []
  const files = parts
    .filter((p) => p.filename && p.name === 'files')
    .map((p) => ({ filename: p.filename as string, data: p.data }))
  if (!files.length) {
    throw createError({ statusCode: 400, statusMessage: 'No .docx files found' })
  }
  try {
    return await runEngine('parse', files)
  } catch (err) {
    throw createError({ statusCode: 500, statusMessage: `Engine error: ${(err as Error).message}` })
  }
})
