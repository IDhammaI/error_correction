<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 },
  max: { type: Number, default: 100 },
  label: { type: String, default: '' },
  showValue: { type: Boolean, default: false },
  tone: { type: String, default: 'accent' },
  size: { type: String, default: 'md' },
})

const percent = computed(() => {
  if (!props.max) return 0
  return Math.min(100, Math.max(0, Math.round((props.value / props.max) * 100)))
})

const barClass = {
  accent: 'accent-gradient-bg',
  blue: 'bg-blue-500',
  emerald: 'bg-emerald-500',
  amber: 'bg-amber-500',
  rose: 'bg-rose-500',
}
</script>

<template>
  <div>
    <div v-if="label || showValue" class="mb-2 flex items-center justify-between gap-3">
      <span v-if="label" class="text-sm font-medium text-slate-700 dark:text-[#d0d6e0]">{{ label }}</span>
      <span v-if="showValue" class="text-xs font-semibold text-slate-500 dark:text-[#8a8f98]">{{ percent }}%</span>
    </div>
    <div
      class="overflow-hidden rounded-full bg-slate-200/80 dark:bg-white/[0.08]"
      :class="size === 'sm' ? 'h-1.5' : size === 'lg' ? 'h-3' : 'h-2'"
      role="progressbar"
      :aria-valuenow="percent"
      aria-valuemin="0"
      aria-valuemax="100"
    >
      <div
        class="h-full rounded-full transition-[width] duration-300"
        :class="barClass[tone] || barClass.accent"
        :style="{ width: `${percent}%` }"
      ></div>
    </div>
  </div>
</template>
