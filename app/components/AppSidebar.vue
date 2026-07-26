<script setup lang="ts">
interface NavItem {
  label: string
  to: string
  icon: string
}

// Simple inline icon paths (Heroicons-style, 24x24 outline).
const nav: NavItem[] = [
  { label: 'Dashboard', to: '/', icon: 'M3 12l9-9 9 9M5 10v10a1 1 0 001 1h4v-6h4v6h4a1 1 0 001-1V10' },
  { label: 'All Letters', to: '/letters', icon: 'M4 4h12l4 4v12a1 1 0 01-1 1H4a1 1 0 01-1-1V5a1 1 0 011-1zM9 9h6M9 13h6M9 17h4' },
  { label: 'Templates', to: '/templates', icon: 'M4 4h12l4 4v12a1 1 0 01-1 1H4a1 1 0 01-1-1V5a1 1 0 011-1zM9 9h6M9 13h6M9 17h4' },
  { label: 'Settings', to: '/settings', icon: 'M10.3 3.2a1 1 0 011.4 0l.9.9a1 1 0 00.9.3l1.2-.2a1 1 0 011.1.8l.3 1.2a1 1 0 00.6.7l1.1.5a1 1 0 01.6 1.3l-.5 1.1a1 1 0 000 .9l.5 1.1a1 1 0 01-.6 1.3l-1.1.5a1 1 0 00-.6.7l-.3 1.2a1 1 0 01-1.1.8l-1.2-.2a1 1 0 00-.9.3l-.9.9a1 1 0 01-1.4 0l-.9-.9a1 1 0 00-.9-.3l-1.2.2a1 1 0 01-1.1-.8l-.3-1.2a1 1 0 00-.6-.7l-1.1-.5a1 1 0 01-.6-1.3l.5-1.1a1 1 0 000-.9l-.5-1.1a1 1 0 01.6-1.3l1.1-.5a1 1 0 00.6-.7l.3-1.2a1 1 0 011.1-.8l1.2.2a1 1 0 00.9-.3zM12 15a3 3 0 100-6 3 3 0 000 6z' },
]

const { user, clear } = useUserSession()

async function signOut() {
  await $fetch('/auth/logout', { method: 'POST' })
  await clear()
  await navigateTo('/login')
}
</script>

<template>
  <aside
    class="flex h-full w-64 flex-none flex-col border-r border-slate-200 bg-white px-4 py-6"
  >
    <div class="px-2">
      <p class="text-lg font-bold leading-tight text-slate-900">Welcome Letter</p>
      <p class="text-lg font-bold leading-tight text-blue-600">Generator</p>
    </div>

    <hr class="my-5 border-slate-200" />

    <nav class="flex flex-1 flex-col gap-1">
      <NuxtLink
        v-for="item in nav"
        :key="item.to"
        :to="item.to"
        class="group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
        active-class="!bg-blue-50 !text-blue-700"
      >
        <svg
          class="h-5 w-5 flex-none"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.7"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path :d="item.icon" />
        </svg>
        {{ item.label }}
      </NuxtLink>
    </nav>

    <hr class="my-4 border-slate-200" />

    <p v-if="user?.email" class="truncate px-3 pb-1 text-xs text-slate-400" :title="user.email">
      {{ user.email }}
    </p>
    <button
      type="button"
      class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
      @click="signOut"
    >
      <svg
        class="h-5 w-5 flex-none"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.7"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M15 12H3m0 0l4-4m-4 4l4 4M15 4h4a1 1 0 011 1v14a1 1 0 01-1 1h-4" />
      </svg>
      Sign Out
    </button>
  </aside>
</template>
