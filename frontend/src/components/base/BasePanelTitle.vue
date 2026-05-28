<script setup>
/**
 * BasePanelTitle.vue
 * BasePanel header 内统一使用的标题文本。
 */
defineProps({
  as: { type: String, default: 'h3' },
  icon: { type: String, default: '' },
})
</script>

<template>
  <component :is="as" class="flex min-w-0 items-center gap-2 text-sm font-bold leading-5 text-gray-900 dark:text-[#f7f8f8]">
    <i v-if="icon" class="fa-solid shrink-0 text-xs text-gray-400 dark:text-[#8a8f98]" :class="icon"></i>
    <span class="min-w-0 truncate">
      <slot />
    </span>
  </component>
</template>
