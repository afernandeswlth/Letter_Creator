<template>
  <div class="flex h-screen overflow-hidden bg-slate-50">
    <AppSidebar />
    <main class="flex-1 overflow-y-auto">
      <div class="mx-auto max-w-[90rem] px-8 py-8">
        <slot />
      </div>
    </main>
  </div>
</template>
