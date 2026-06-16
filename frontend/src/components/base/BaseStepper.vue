<script setup>
defineProps({
  modelValue: { type: [String, Number], default: '' },
  steps: { type: Array, default: () => [] },
  direction: { type: String, default: 'horizontal' },
})

const emit = defineEmits(['update:modelValue', 'change'])

function statusOf(step, index, steps, modelValue) {
  if (step.status) return step.status
  const currentIndex = steps.findIndex(item => item.value === modelValue)
  if (index < currentIndex) return 'done'
  if (index === currentIndex) return 'current'
  return 'pending'
}

function select(step) {
  if (step.disabled) return
  emit('update:modelValue', step.value)
  emit('change', step.value, step)
}
</script>

<template>
  <ol
    class="grid gap-3"
    :class="direction === 'vertical' ? 'grid-cols-1' : 'grid-cols-1 sm:grid-cols-[repeat(var(--step-count),minmax(0,1fr))]'"
    :style="{ '--step-count': steps.length }"
  >
    <li
      v-for="(step, index) in steps"
      :key="step.value"
      class="relative"
    >
      <button
        type="button"
        class="group flex w-full items-start gap-3 rounded-xl p-2 text-left transition-colors"
        :class="step.disabled ? 'cursor-not-allowed opacity-50' : 'hover:bg-slate-100 dark:hover:bg-white/[0.05]'"
        @click="select(step)"
      >
        <span
          class="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-xs font-bold transition-colors"
          :class="[
            statusOf(step, index, steps, modelValue) === 'done'
              ? 'border-transparent bg-emerald-500 text-white'
              : statusOf(step, index, steps, modelValue) === 'current'
                ? 'accent-bg border-transparent text-white'
                : 'border-slate-200 bg-white text-slate-400 dark:border-white/[0.08] dark:bg-white/[0.04] dark:text-[#8a8f98]',
          ]"
        >
          <i v-if="statusOf(step, index, steps, modelValue) === 'done'" class="fa-solid fa-check text-[10px]"></i>
          <span v-else>{{ index + 1 }}</span>
        </span>
        <span class="min-w-0">
          <span class="block truncate text-sm font-semibold text-slate-900 dark:text-[#f7f8f8]">{{ step.label }}</span>
          <span v-if="step.description" class="mt-0.5 block text-xs leading-5 text-slate-500 dark:text-[#8a8f98]">
            {{ step.description }}
          </span>
        </span>
      </button>
    </li>
  </ol>
</template>
