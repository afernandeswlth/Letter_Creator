// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  ssr: false,
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  css: ['~/assets/css/main.css'],
  // Public Google config for the client-side Drive folder picker. These are
  // meant to be public (an OAuth *web* client id + a browser API key restricted
  // to the Picker API) and are baked into the client build — safe to commit.
  // A NUXT_PUBLIC_GOOGLE_* env var overrides the matching default if set.
  runtimeConfig: {
    public: {
      googleClientId: '475104042258-1p90gt45t1g1u596ge339a35oaqhp35a.apps.googleusercontent.com',
      googleApiKey: 'AIzaSyAR9D5IbwJiMDRrM9riAMflD5WyI2wNv4I',
      googleAppId: '475104042258', // Cloud project number (the id prefix); improves the Picker
    },
  },
  vite: {
    plugins: [tailwindcss()],
  },
  app: {
    head: {
      title: 'Letter Generator',
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      ],
    },
  },
})
