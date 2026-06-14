<script setup>
/**
 * BaseToolbarButton.vue
 * 通用小型工具栏按钮，适合图标按钮或“图标 + 文本”的局部操作。
 */
defineProps({
  icon: { type: String, default: '' },
  variant: { type: String, default: 'neutral' },
  active: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  title: { type: String, default: '' },
})

const emit = defineEmits(['click'])
</script>

<template>
  <button
    type="button"
    :title="title"
    :disabled="disabled"
    class="inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50"
    :class="[
      active
        ? 'bg-gray-200 text-gray-900 dark:bg-white/[0.08] dark:text-[#f7f8f8]'
        : variant === 'primary'
          ? 'accent-bg text-white hover:bg-[rgb(var(--accent-hover-rgb))]'
          : variant === 'danger'
            ? 'bg-rose-500/12 text-rose-500 hover:bg-rose-500/18 dark:text-rose-400'
            : 'bg-white/80 text-gray-700 hover:bg-white dark:bg-white/[0.045] dark:text-[#d0d6e0] dark:hover:bg-white/[0.07]',
    ]"
    @click="emit('click', $event)"
  >
    <i v-if="icon" class="fa-solid text-[10px]" :class="icon"></i>
    <slot />
  </button>
</template>
