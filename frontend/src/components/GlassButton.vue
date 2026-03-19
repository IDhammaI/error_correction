<script setup>
defineProps({
  icon: { type: String, default: '' },
})
defineEmits(['click'])
</script>

<template>
  <button
    v-bind="$attrs"
    class="group inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-slate-200/60 bg-white/60 px-4 text-sm font-bold text-slate-700 backdrop-blur-xl transition-all hover:border-slate-300 hover:bg-white/80 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-300 dark:hover:border-white/20 dark:hover:bg-white/[0.06]"
  >
    <i v-if="icon" class="fa-solid transition-transform group-hover:scale-110" :class="icon"></i>
    <slot />
  </button>
</template>
