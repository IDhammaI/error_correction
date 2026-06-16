<script setup>
defineProps({
  variant: { type: String, default: 'rect' },
  lines: { type: Number, default: 1 },
  animated: { type: Boolean, default: true },
})
</script>

<template>
  <div v-if="variant === 'text'" class="space-y-2">
    <span
      v-for="line in lines"
      :key="line"
      class="block h-3 rounded bg-slate-200 dark:bg-white/[0.08]"
      :class="[
        animated ? 'animate-pulse' : '',
        line === lines ? 'w-2/3' : 'w-full',
      ]"
    ></span>
  </div>
  <span
    v-else
    class="block bg-slate-200 dark:bg-white/[0.08]"
    :class="[
      animated ? 'animate-pulse' : '',
      variant === 'circle' ? 'h-10 w-10 rounded-full' : 'h-24 w-full rounded-xl',
    ]"
  ></span>
</template>
