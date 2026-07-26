/**
 * Google OAuth login. Only @wlth.com accounts are allowed.
 * Env: NUXT_OAUTH_GOOGLE_CLIENT_ID, NUXT_OAUTH_GOOGLE_CLIENT_SECRET.
 */
export default defineOAuthGoogleEventHandler({
  config: {
    scope: ['email', 'profile'],
    // Restrict the Google account chooser to the WLTH workspace.
    authorizationParams: { hd: 'wlth.com', prompt: 'select_account' },
  },
  async onSuccess(event, { user }) {
    const domain = useRuntimeConfig(event).allowedEmailDomain || 'wlth.com'
    const email: string = (user.email || '').toLowerCase()
    const verified = user.email_verified === true || user.verified_email === true

    if (!verified || !email.endsWith(`@${domain}`)) {
      await clearUserSession(event)
      return sendRedirect(event, '/login?error=domain')
    }

    await setUserSession(event, {
      user: { email, name: user.name, picture: user.picture },
      loggedInAt: Date.now(),
    })
    return sendRedirect(event, '/')
  },
  onError(event, error) {
    console.error('[auth] google oauth error:', error)
    return sendRedirect(event, '/login?error=oauth')
  },
})
