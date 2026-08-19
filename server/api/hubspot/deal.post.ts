import { runEngineHubspotDeal } from '~~/server/utils/engine'

/** POST /api/hubspot/deal — { dealId } → { values } prefilled from the HubSpot deal. */
export default defineEventHandler(async (event) => {
  const body = await readBody<{ dealId?: string }>(event)
  const dealId = (body?.dealId ?? '').trim()
  if (!dealId) throw createError({ statusCode: 400, statusMessage: 'A HubSpot Deal ID is required.' })
  try {
    return await runEngineHubspotDeal(dealId)
  } catch (err) {
    // Surface the engine's friendly message (bad token, deal not found, …).
    throw createError({ statusCode: 502, statusMessage: (err as Error).message })
  }
})
