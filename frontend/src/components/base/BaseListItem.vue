<script setup>
/**
 * BaseListItem.vue
 * 列表/设置项条目
 */
defineProps({
  label: { type: String, default: '' },
  description: { type: String, default: '' },
  value: { type: String, default: '' },
  interactive: { type: Boolean, default: false },
  danger: { type: Boolean, default: false },
  showArrow: { type: Boolean, default: false },
  layout: { type: String, default: 'horizontal' }, // 'horizontal' | 'vertical'
  skeleton: { type: Boolean, default: false }, // 新增骨架屏模式
})
</script>

<template>
  <li 
    class="group relative flex min-h-[56px]"
    :class="[
      interactive && !skeleton ? 'cursor-pointer hover:bg-gray-50 dark:hover:bg-white/[0.04] transition-colors' : '',
      'items-center justify-between px-4 py-3 gap-4'
    ]"
    @click="interactive && !skeleton && $emit('click')"
  >
    <!-- 内部底边框（不连接外边框的分割线） -->
    <div class="absolute bottom-0 left-4 right-4 h-px bg-gray-100 group-last:hidden dark:bg-white/[0.04]"></div>

    <!-- 左侧区域：Label 和 Description -->
    <div class="flex flex-col shrink-0 min-w-0 max-w-[50%]">
      <template v-if="skeleton">
        <div class="h-4 w-16 rounded bg-gray-200 dark:bg-white/[0.08]"></div>
        <div class="mt-1.5 h-3 w-28 rounded bg-gray-200 dark:bg-white/[0.08]"></div>
      </template>
      <template v-else>
        <div class="flex items-center gap-2">
          <slot name="icon" />
          <span 
            class="truncate text-sm font-medium"
            :class="danger ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-[#f7f8f8]'"
          >
            {{ label }}
          </span>
        </div>
        <span v-if="description" class="mt-1 truncate text-xs text-gray-500 dark:text-[#62666d]">
          {{ description }}
        </span>
      </template>
    </div>

    <!-- 右侧区域：展示值、输入框或控件 -->
    <div class="flex items-center justify-end gap-3 min-w-0" :class="{ 'w-44 max-w-full': skeleton }">
      <template v-if="skeleton">
        <slot name="skeleton-right">
          <div class="h-4 w-20 rounded bg-gray-200 dark:bg-white/[0.08] ml-auto"></div>
        </slot>
      </template>
      <template v-else>
        <span v-if="value" class="truncate text-sm text-gray-500 dark:text-[#8a8f98]">
          {{ value }}
        </span>
        
        <!-- 当存在默认插槽（如 input）时，让其占据合理的宽度并靠右对齐 -->
        <div v-if="$slots.default" class="w-44 max-w-full">
          <slot />
        </div>

        <i v-if="showArrow" class="fa-solid fa-chevron-right text-[10px] text-gray-400 dark:text-[#62666d] ml-1 shrink-0"></i>
      </template>
    </div>
  </li>
</template>
