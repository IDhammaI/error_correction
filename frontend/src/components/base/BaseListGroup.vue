<script setup>
/**
 * BaseListGroup
 * 类 Linear 设置项分组容器
 */
import BaseSurface from './BaseSurface.vue'

defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  borderless: { type: Boolean, default: false },
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
    <div
      v-if="borderless"
      class="overflow-hidden rounded-xl bg-transparent shadow-none border-transparent"
    >
      <div class="flex flex-col">
        <slot />
      </div>
    </div>
    <BaseSurface v-else>
      <div class="flex flex-col">
        <slot />
      </div>
    </BaseSurface>

    <!-- 分组描述/说明 -->
    <p v-if="description" class="mt-2 ml-1 text-xs text-gray-500 dark:text-[#8a8f98]">
      {{ description }}
    </p>
  </div>
</template>
