<script setup lang="ts">
interface NavItem {
  label: string
  to: string
  icon: string
  disabled?: boolean
}

// WLTH (lucide) icon names — see WIcon.vue.
const nav: NavItem[] = [
  { label: 'Dashboard', to: '/', icon: 'house' },
  { label: 'All Letters', to: '/letters', disabled: true, icon: 'file-text' },
  { label: 'Templates', to: '/templates', icon: 'file-text' },
  { label: 'Settings', to: '/settings', disabled: true, icon: 'settings' },
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
          <WIcon name="file-text" class="h-4 w-4" />
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
        <WIcon name="panel-left" class="h-5 w-5" />
      </button>
    </div>

    <hr class="my-5 border-slate-200" />

    <nav class="flex flex-1 flex-col gap-1">
      <NuxtLink
        v-for="item in nav"
        :key="item.to"
        :to="item.disabled ? '' : item.to"
        :title="collapsed ? item.label : undefined"
        class="group flex items-center rounded-lg py-2.5 text-sm font-medium text-slate-600 transition"
        :class="[
          collapsed ? 'justify-center px-0' : 'gap-3 px-3',
          item.disabled ? 'pointer-events-none cursor-not-allowed opacity-40' : 'hover:bg-slate-50',
        ]"
        :aria-disabled="item.disabled || undefined"
        active-class="!bg-blue-50 !text-blue-700"
      >
        <WIcon :name="item.icon" class="h-5 w-5 flex-none" />
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
      <WIcon v-if="!collapsed" name="chevron-down" class="h-4 w-4 flex-none text-slate-400" />
    </div>
  </aside>
</template>
