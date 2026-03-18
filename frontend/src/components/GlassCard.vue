<script setup>
defineProps({
  padding: { type: String, default: 'p-6' },
  rounded: { type: String, default: 'rounded-2xl' },
})
</script>

<template>
  <div
    :class="[rounded, padding]"
    class="border border-slate-200/60 bg-white/70 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-white/[0.03]"
  >
    <slot />
  </div>
</template>
