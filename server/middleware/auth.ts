/**
 * Require a signed-in session for the letter API. Auth routes and the login
 * page stay public so users can actually sign in.
 */
export default defineEventHandler(async (event) => {
  const path = getRequestURL(event).pathname
  if (!path.startsWith('/api/letters')) return

  const session = await getUserSession(event)
  if (!session?.user) {
    throw createError({ statusCode: 401, statusMessage: 'Not signed in' })
  }
})
