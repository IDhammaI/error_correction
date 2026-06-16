<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Number, default: 0 },
  min: { type: Number, default: 0 },
  max: { type: Number, default: 100 },
  step: { type: Number, default: 1 },
  label: { type: String, default: '' },
  showValue: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'change'])

const percent = computed(() => {
  if (props.max === props.min) return 0
  return Math.min(100, Math.max(0, ((props.modelValue - props.min) / (props.max - props.min)) * 100))
})

function update(event) {
  const value = Number(event.target.value)
  emit('update:modelValue', value)
  emit('change', value, event)
}
</script>

<template>
  <div>
    <div v-if="label || showValue" class="mb-2 flex items-center justify-between gap-3">
      <label v-if="label" class="text-sm font-medium text-slate-700 dark:text-[#d0d6e0]">{{ label }}</label>
      <span v-if="showValue" class="text-xs font-semibold text-slate-500 dark:text-[#8a8f98]">{{ modelValue }}</span>
    </div>
    <input
      type="range"
      class="base-slider h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-200 outline-none disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white/[0.08]"
      :style="{ '--slider-progress': `${percent}%` }"
      :value="modelValue"
      :min="min"
      :max="max"
      :step="step"
      :disabled="disabled"
      @input="update"
    />
  </div>
</template>

<style scoped>
.base-slider {
  background-image: linear-gradient(to right, rgb(var(--accent-rgb)) 0 var(--slider-progress), transparent var(--slider-progress));
}
.base-slider::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 999px;
  background: white;
  border: 3px solid rgb(var(--accent-rgb));
  box-shadow: 0 1px 4px rgb(15 23 42 / 0.25);
}
.base-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border: 3px solid rgb(var(--accent-rgb));
  border-radius: 999px;
  background: white;
  box-shadow: 0 1px 4px rgb(15 23 42 / 0.25);
}
</style>
