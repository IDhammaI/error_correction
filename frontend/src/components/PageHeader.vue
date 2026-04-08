<script setup>
/**
 * PageHeader.vue
 * Linear 风格顶部导航栏 — 固定在内容面板顶部，底部 border 分割
 */
defineProps({
  title: { type: String, required: true },
})
</script>

<template>
  <header class="flex items-center justify-between h-12 px-6 border-b border-white/[0.08] shrink-0">
    <!-- 左侧：标题 + 操作图标 -->
    <div class="flex items-center gap-2">
      <h2 class="text-sm font-medium text-[#f7f8f8]">{{ title }}</h2>
      <!-- 左侧附加操作 -->
      <div v-if="$slots.actions" class="flex items-center gap-1 text-[#62666d]">
        <slot name="actions"></slot>
      </div>
    </div>

    <!-- 右侧操作区 -->
    <div v-if="$slots.default" class="flex shrink-0 items-center gap-3">
      <slot></slot>
    </div>
  </header>
</template>
