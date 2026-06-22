<script setup>
defineProps({
  label: { type: String, default: '' },
  icon: { type: String, default: '' },
  current: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['click'])
</script>

<template>
  <button
    type="button"
    class="inline-flex min-w-0 items-center gap-2 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgb(var(--accent-rgb)/0.45)]"
    :class="[
      current ? 'font-semibold text-slate-900 dark:text-[#f7f8f8]' : 'text-slate-500 hover:text-slate-900 dark:text-[#8a8f98] dark:hover:text-[#f7f8f8]',
      disabled ? 'cursor-not-allowed opacity-50' : '',
    ]"
    :disabled="disabled || current"
    @click="emit('click')"
  >
    <i v-if="icon" class="fa-solid shrink-0 text-xs" :class="icon"></i>
    <span class="min-w-0 truncate">
      <slot>{{ label }}</slot>
    </span>
  </button>
</template>
