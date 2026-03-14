<script setup>
defineProps({
  toasts: { type: Array, default: () => [] },
})
</script>

<template>
  <div class="pointer-events-none fixed left-1/2 top-4 z-50 flex w-[min(420px,calc(100vw-2rem))] -translate-x-1/2 flex-col gap-2">
    <div
      v-for="t in toasts"
      :key="t.id"
      class="pointer-events-auto rounded-xl px-4 py-3 text-sm font-medium shadow-lg ring-1"
      :class="
        t.type === 'success'
          ? 'bg-emerald-600 text-white ring-emerald-700/30'
          : t.type === 'error'
            ? 'bg-rose-600 text-white ring-rose-700/30'
            : t.type === 'warning'
              ? 'bg-amber-500 text-white ring-amber-600/30'
              : 'bg-slate-900 text-white ring-slate-700/30'
      "
    >
      {{ t.message }}
    </div>
  </div>
</template>
