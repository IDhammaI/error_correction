<script setup>
/**
 * SearchInput.vue
 * 搜索输入框（带图标 + 清除按钮）
 */
defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  placeholder: { type: String, default: '搜索...' },
  icon: { type: String, default: 'fa-solid fa-magnifying-glass' },
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <div>
    <label v-if="label" class="mb-1.5 block text-xs font-medium text-gray-600 dark:text-[#62666d]">{{ label }}</label>
    <div class="relative group">
      <i :class="icon" class="pointer-events-none absolute left-3 top-1/2 z-10 -translate-y-1/2 text-xs text-gray-400 dark:text-[#62666d] transition-colors group-focus-within:text-gray-500 dark:group-focus-within:text-[#8a8f98]"></i>
      <input
        :value="modelValue"
        @input="emit('update:modelValue', $event.target.value)"
        type="text"
        :placeholder="placeholder"
        class="h-9 w-full rounded-md border border-gray-200 bg-white pl-9 pr-3 text-sm font-medium text-gray-900 placeholder-gray-400 outline-none transition-colors hover:border-gray-300 focus:border-[rgb(var(--accent-rgb)/0.4)] dark:border-white/[0.08] dark:bg-white/[0.02] dark:text-[#f7f8f8] dark:placeholder-[#62666d] dark:hover:border-white/[0.12] dark:focus:border-[rgb(var(--accent-rgb)/0.4)] dark:border-t-white/[0.12]"
      />
    </div>
  </div>
</template>
