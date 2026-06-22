<script setup>
/**
 * BaseSurface.vue
 * 统一页面中的浅色/深色半透明容器外观，并支持按语义切换根标签。
 */
defineOptions({
  inheritAttrs: false,
})

defineProps({
  as: { type: String, default: 'div' },
  hoverable: { type: Boolean, default: true },
})
</script>

<template>
  <component
    :is="as"
    v-bind="$attrs"
    class="overflow-hidden rounded-xl border border-gray-100 bg-gray-50/80 shadow-sm transition-all dark:border-white/[0.08] dark:bg-white/[0.035]"
    :class="hoverable ? 'hover:bg-gray-100 dark:hover:bg-white/[0.06]' : ''"
  >
    <slot />
  </component>
</template>
