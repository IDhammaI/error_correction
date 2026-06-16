<script setup>
defineProps({
  label: { type: String, default: '' },
  orientation: { type: String, default: 'horizontal' },
})
</script>

<template>
  <div
    v-if="orientation === 'vertical'"
    class="mx-2 h-full min-h-6 w-px bg-slate-200 dark:bg-white/[0.08]"
    role="separator"
    aria-orientation="vertical"
  ></div>
  <div v-else class="flex items-center gap-3" role="separator">
    <span class="h-px flex-1 bg-slate-200 dark:bg-white/[0.08]"></span>
    <span v-if="label" class="text-xs font-semibold uppercase text-slate-400 dark:text-[#62666d]">{{ label }}</span>
    <span class="h-px flex-1 bg-slate-200 dark:bg-white/[0.08]"></span>
  </div>
</template>
