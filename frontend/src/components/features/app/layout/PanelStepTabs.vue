<script setup>
/**
 * PanelStepTabs.vue
 * 内容面板顶部的小型步骤切换条。
 */
defineProps({
  steps: { type: Array, default: () => [] },
  currentStep: { type: Number, default: -1 },
})

const emit = defineEmits(['step-click'])
</script>

<template>
  <div v-if="steps.length" class="ml-2 flex items-center gap-1">
    <button
      v-for="(step, index) in steps"
      :key="index"
      type="button"
      class="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs transition-colors"
      :class="index === currentStep
        ? 'brand-gradient-bg text-white shadow-sm font-medium'
        : step.done
          ? 'text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-[#8a8f98] dark:hover:bg-white/[0.04] dark:hover:text-[#d0d6e0]'
          : 'cursor-default text-gray-400 dark:text-[#62666d]'"
      @click="emit('step-click', index)"
    >
      <span
        class="flex h-4 w-4 items-center justify-center rounded text-[10px] transition-colors"
        :class="step.done
          ? 'accent-bg text-white'
          : index === currentStep
            ? 'bg-white/20 text-white'
            : 'bg-gray-100 text-gray-400 dark:bg-white/[0.04] dark:text-[#62666d]'"
      >
        <i v-if="step.done" class="fa-solid fa-check text-[8px]"></i>
        <span v-else>{{ index + 1 }}</span>
      </span>
      <span>{{ step.label }}</span>
    </button>
  </div>
</template>
