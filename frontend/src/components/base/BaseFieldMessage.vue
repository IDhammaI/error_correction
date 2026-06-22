<script setup>
defineProps({
  message: { type: String, default: '' },
  type: { type: String, default: 'hint' },
})

const toneClass = {
  hint: 'text-slate-500 dark:text-[#8a8f98]',
  error: 'text-rose-500 dark:text-rose-300',
  success: 'text-emerald-600 dark:text-emerald-300',
  warning: 'text-amber-600 dark:text-amber-300',
}

const iconClass = {
  hint: 'fa-circle-info',
  error: 'fa-circle-exclamation',
  success: 'fa-circle-check',
  warning: 'fa-triangle-exclamation',
}
</script>

<template>
  <p
    v-if="message || $slots.default"
    class="mt-1.5 flex items-start gap-1.5 text-xs leading-5"
    :class="toneClass[type] || toneClass.hint"
  >
    <i class="fa-solid mt-1 shrink-0 text-[10px]" :class="iconClass[type] || iconClass.hint"></i>
    <span class="min-w-0">
      <slot>{{ message }}</slot>
    </span>
  </p>
</template>
