<script setup lang="ts">
definePageMeta({ layout: false })

const route = useRoute()
const { loggedIn } = useUserSession()

// Already signed in? go to the app.
watchEffect(() => {
  if (loggedIn.value) navigateTo('/')
})

const error = computed(() => {
  if (route.query.error === 'domain') return 'Please sign in with your @wlth.com account.'
  if (route.query.error === 'oauth') return 'Sign-in failed. Please try again.'
  return ''
})
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-50 px-4">
    <div class="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
      <div class="text-center">
        <p class="text-xl font-bold leading-tight text-slate-900">Welcome Letter</p>
        <p class="text-xl font-bold leading-tight text-blue-600">Generator</p>
      </div>

      <p class="mt-6 text-center text-sm text-slate-500">
        Sign in with your WLTH Google account to continue.
      </p>

      <a
        href="/auth/google"
        class="mt-6 flex w-full items-center justify-center gap-3 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
      >
        <svg class="h-5 w-5" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5a5.6 5.6 0 01-2.4 3.6v3h3.9c2.3-2.1 3.5-5.2 3.5-8.8z" />
          <path fill="#34A853" d="M12 24c3.2 0 6-1.1 8-2.9l-3.9-3c-1.1.7-2.5 1.2-4.1 1.2-3.1 0-5.8-2.1-6.7-5H1.3v3.1A12 12 0 0012 24z" />
          <path fill="#FBBC05" d="M5.3 14.3a7.2 7.2 0 010-4.6V6.6H1.3a12 12 0 000 10.8l4-3.1z" />
          <path fill="#EA4335" d="M12 4.8c1.8 0 3.3.6 4.5 1.8l3.4-3.4A12 12 0 001.3 6.6l4 3.1C6.2 6.9 8.9 4.8 12 4.8z" />
        </svg>
        Sign in with Google
      </a>

      <p v-if="error" class="mt-4 text-center text-sm text-red-600">{{ error }}</p>
      <p class="mt-6 text-center text-xs text-slate-400">Access is limited to @wlth.com accounts.</p>
    </div>
  </div>
</template>
