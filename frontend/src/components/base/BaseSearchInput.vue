<script setup>
/**
 * BaseSearchInput.vue
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
        class="h-9 w-full rounded-md bg-white/80 pl-9 pr-9 text-sm font-medium text-gray-900 placeholder-gray-400 outline-none ring-1 ring-inset ring-transparent transition-colors hover:bg-white focus:bg-white focus:ring-[rgb(var(--accent-rgb)/0.26)] dark:bg-white/[0.045] dark:text-[#f7f8f8] dark:placeholder-[#62666d] dark:hover:bg-white/[0.07] dark:focus:bg-white/[0.08] dark:focus:ring-[rgb(var(--accent-rgb)/0.35)]"
      />
      <button
        v-if="modelValue"
        type="button"
        aria-label="清空搜索"
        class="absolute right-2 top-1/2 flex h-5 w-5 -translate-y-1/2 items-center justify-center rounded-md text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:text-[#62666d] dark:hover:bg-white/[0.06] dark:hover:text-[#d0d6e0]"
        @click="emit('update:modelValue', '')"
      >
        <i class="fa-solid fa-xmark text-[10px]"></i>
      </button>
    </div>
  </div>
</template>
