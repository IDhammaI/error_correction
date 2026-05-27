<script setup>
/**
 * BaseTabs.vue
 * 通用标签页切换组件，只负责 tab header 和 modelValue 同步。
 */
defineProps({
  modelValue: { type: String, required: true },
  items: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <div class="flex border-b border-gray-200 px-4 dark:border-white/[0.06]">
    <button
      v-for="item in items"
      :key="item.value"
      type="button"
      class="inline-flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-bold transition-colors"
      :class="modelValue === item.value
        ? 'border-[rgb(var(--accent-rgb))] accent-text'
        : 'border-transparent text-gray-500 hover:text-gray-800 dark:text-[#8a8f98] dark:hover:text-[#d0d6e0]'"
      @click="emit('update:modelValue', item.value)"
    >
      <i v-if="item.icon" class="fa-solid text-xs" :class="item.icon"></i>
      {{ item.label }}
      <span v-if="item.badge" class="rounded-full bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500 dark:bg-white/[0.06] dark:text-[#8a8f98]">
        {{ item.badge }}
      </span>
    </button>
  </div>
</template>
