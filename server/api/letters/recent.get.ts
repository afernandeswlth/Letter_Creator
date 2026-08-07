import { recentLetters } from '~~/server/utils/letterStore'

/** GET /api/letters/recent?limit=20 — recent letters for the dashboard. */
export default defineEventHandler(async (event) => {
  const q = getQuery(event)
  const n = Math.min(Math.max(Number(q.limit ?? 20) || 20, 1), 500)
  return { letters: await recentLetters(n) }
})
