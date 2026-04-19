<script setup>
/**
 * EmptyState.vue
 * Linear 风格空状态组件 — 居中图标 + 标题 + 描述 + 操作按钮
 */
defineProps({
  icon: { type: String, default: '' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
})
</script>

<template>
  <div class="flex flex-1 flex-col items-center justify-center">
    <!-- 图标 -->
    <div v-if="icon" class="mb-6 flex h-16 w-16 items-center justify-center rounded-xl border border-gray-200 bg-white dark:border-white/[0.06] dark:bg-white/[0.02]">
      <i :class="icon" class="text-2xl text-gray-400 dark:text-[#62666d]"></i>
    </div>

    <!-- 标题 -->
    <h3 class="text-base font-medium text-gray-900 dark:text-[#f7f8f8]">{{ title }}</h3>

    <!-- 描述 -->
    <p v-if="description" class="mt-2 max-w-sm text-center text-sm text-gray-500 dark:text-[#62666d] leading-relaxed">{{ description }}</p>

    <!-- 操作按钮区 -->
    <div v-if="$slots.default" class="mt-6 flex items-center gap-3">
      <slot></slot>
    </div>
  </div>
</template>
