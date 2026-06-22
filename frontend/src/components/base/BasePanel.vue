<script setup>
/**
 * BasePanel.vue
 * 带 header / body / footer 插槽的工作台面板容器。
 */
defineProps({
  bodyClass: { type: String, default: 'p-4' },
  headerClass: { type: String, default: 'flex h-16 items-center px-4 py-3' },
  footerClass: { type: String, default: 'p-3' },
  scrollBody: { type: Boolean, default: true },
})
</script>

<template>
  <section class="flex min-h-0 flex-col overflow-hidden rounded-xl bg-white/85 shadow-sm shadow-black/[0.03] dark:bg-white/[0.04] dark:shadow-black/20">
    <header
      v-if="$slots.header"
      class="shrink-0 overflow-hidden bg-gray-50/70 dark:bg-white/[0.025]"
      :class="headerClass"
    >
      <slot name="header" />
    </header>

    <div
      class="min-h-0 flex-1"
      :class="[bodyClass, scrollBody ? 'overflow-y-auto custom-scrollbar' : 'overflow-visible']"
    >
      <slot />
    </div>

    <footer
      v-if="$slots.footer"
      class="shrink-0 bg-gray-50/70 dark:bg-white/[0.025]"
      :class="footerClass"
    >
      <slot name="footer" />
    </footer>
  </section>
</template>
