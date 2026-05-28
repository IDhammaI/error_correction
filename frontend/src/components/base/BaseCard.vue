<script setup>
/**
 * BaseCard.vue
 * 毛玻璃风格卡片容器
 */
defineProps({
  padding: { type: String, default: 'p-4' },
  rounded: { type: String, default: 'rounded-lg' },
})
</script>

<template>
  <div
    :class="[rounded, padding]"
    class="bg-white/85 shadow-sm shadow-black/[0.03] transition-colors duration-200 hover:bg-white dark:bg-white/[0.04] dark:shadow-black/20 dark:hover:bg-white/[0.065]"
  >
    <slot />
  </div>
</template>
