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

// Shared so it persists across page navigation.
const collapsed = useState('sidebar-collapsed', () => false)
</script>

<template>
  <aside
    class="flex h-full flex-none flex-col border-r border-slate-200 bg-white py-6 transition-all duration-200"
    :class="collapsed ? 'w-[72px] px-2' : 'w-64 px-4'"
  >
    <!-- WLTH wordmark -->
    <div v-if="!collapsed" class="px-2">
      <img src="/logos/wlth.png" alt="WLTH" class="h-7 w-auto object-contain" />
    </div>

    <!-- Product brand + collapse toggle -->
    <div class="mt-4 flex items-center" :class="collapsed ? 'justify-center' : 'justify-between px-2'">
      <div v-if="!collapsed" class="flex items-center gap-2">
        <span class="flex h-8 w-8 flex-none items-center justify-center rounded-lg bg-blue-600 text-white">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 4h12l4 4v12a1 1 0 01-1 1H4a1 1 0 01-1-1V5a1 1 0 011-1zM9 9h4M9 13h6M9 17h6" />
          </svg>
        </span>
        <div class="leading-tight">
          <p class="text-sm font-bold text-slate-900">Letter</p>
          <p class="text-sm font-bold text-blue-600">Generator</p>
        </div>
      </div>
      <button
        type="button"
        class="flex h-8 w-8 flex-none items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-100"
        :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        @click="collapsed = !collapsed"
      >
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="4" width="18" height="16" rx="2" />
          <path d="M9 4v16" />
          <path v-if="collapsed" d="M13 9l3 3-3 3" />
          <path v-else d="M16 9l-3 3 3 3" />
        </svg>
      </button>
    </div>

    <hr class="my-5 border-slate-200" />

    <nav class="flex flex-1 flex-col gap-1">
      <NuxtLink
        v-for="item in nav"
        :key="item.to"
        :to="item.to"
        :title="collapsed ? item.label : undefined"
        class="group flex items-center rounded-lg py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
        :class="collapsed ? 'justify-center px-0' : 'gap-3 px-3'"
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
        <span v-if="!collapsed">{{ item.label }}</span>
      </NuxtLink>
    </nav>

    <hr class="my-4 border-slate-200" />

    <!-- User chip -->
    <div class="flex items-center" :class="collapsed ? 'justify-center' : 'gap-3 px-1'">
      <span class="flex h-9 w-9 flex-none items-center justify-center rounded-full bg-slate-200 text-xs font-semibold text-slate-600">
        AU
      </span>
      <div v-if="!collapsed" class="min-w-0 flex-1">
        <p class="truncate text-sm font-medium text-slate-900">Admin User</p>
        <p class="truncate text-xs text-slate-400">admin@company.com</p>
      </div>
      <svg v-if="!collapsed" class="h-4 w-4 flex-none text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
        <path d="M6 9l6 6 6-6" />
      </svg>
    </div>
  </aside>
</template>
