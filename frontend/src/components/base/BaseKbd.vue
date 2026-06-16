<script setup>
defineProps({
  keys: { type: [String, Array], default: '' },
})
</script>

<template>
  <span class="inline-flex items-center gap-1">
    <template v-for="(key, index) in (Array.isArray(keys) ? keys : String(keys).split('+').filter(Boolean))" :key="`${key}-${index}`">
      <kbd class="inline-flex min-h-5 min-w-5 items-center justify-center rounded border border-slate-200 bg-white px-1.5 text-[11px] font-bold leading-none text-slate-500 shadow-sm dark:border-white/[0.08] dark:bg-white/[0.04] dark:text-[#a8adb7]">
        {{ key }}
      </kbd>
      <span v-if="index < (Array.isArray(keys) ? keys.length : String(keys).split('+').filter(Boolean).length) - 1" class="text-xs text-slate-400">+</span>
    </template>
  </span>
</template>
