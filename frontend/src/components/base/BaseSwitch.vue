<script setup>
/**
 * BaseSwitch.vue
 * 通用开关控件，用于表达开启/关闭类设置。
 */
defineProps({
  modelValue: { type: Boolean, default: false },
  label: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'change'])

/**
 * 点击开关时切换布尔值；禁用状态下不响应交互。
 */
const toggle = (value, disabled) => {
  if (disabled) return
  emit('update:modelValue', value)
  emit('change', value)
}
</script>

<template>
  <button
    type="button"
    class="inline-flex items-center gap-2 transition-opacity"
    :class="disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'"
    :aria-pressed="modelValue"
    :disabled="disabled"
    @click="toggle(!modelValue, disabled)"
  >
    <span
      class="relative h-4 w-7 rounded-full transition-colors"
      :class="modelValue ? 'accent-bg' : 'bg-gray-300 dark:bg-white/[0.08]'"
    >
      <span
        class="absolute left-0.5 top-0.5 h-3 w-3 rounded-full bg-white transition-transform"
        :class="modelValue ? 'translate-x-3' : 'translate-x-0'"
      ></span>
    </span>
    <span v-if="label" class="text-xs text-gray-500 transition-colors dark:text-[#8a8f98]">
      {{ label }}
    </span>
    <slot />
  </button>
</template>
