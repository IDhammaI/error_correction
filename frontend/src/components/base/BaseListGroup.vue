<script setup>
/**
 * BaseListGroup
 * 类 Linear 设置项分组容器
 */
defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
})
</script>

<template>
  <div class="mb-8">
    <!-- 分组标题 -->
    <slot name="header">
      <h3 v-if="title" class="mb-3 ml-1 text-lg font-bold text-gray-900 dark:text-[#f7f8f8]">
        {{ title }}
      </h3>
    </slot>
    
    <!-- 列表容器 -->
    <div class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-white/[0.08] dark:bg-[#1b1b1d]">
      <ul class="flex flex-col">
        <slot />
      </ul>
    </div>

    <!-- 分组描述/说明 -->
    <p v-if="description" class="mt-2 ml-1 text-xs text-gray-500 dark:text-[#8a8f98]">
      {{ description }}
    </p>
  </div>
</template>
