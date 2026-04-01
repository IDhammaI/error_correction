<script setup>
defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  placeholder: { type: String, default: '搜索...' },
  icon: { type: String, default: 'fa-solid fa-magnifying-glass' },
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <div>
    <label v-if="label" class="mb-2 block text-[11px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-400">{{ label }}</label>
    <div class="relative group">
      <i :class="icon" class="pointer-events-none absolute left-4 top-1/2 z-10 -translate-y-1/2 text-sm text-slate-400 transition-colors group-hover:text-slate-500 group-focus-within:text-slate-600 dark:text-slate-500 dark:group-hover:text-slate-300 dark:group-focus-within:text-slate-200"></i>
      <input
        :value="modelValue"
        @input="emit('update:modelValue', $event.target.value)"
        type="text"
        :placeholder="placeholder"
        class="h-11 w-full rounded-xl border border-slate-200/60 bg-white/60 pl-11 pr-4 text-sm font-bold backdrop-blur-xl outline-none transition-all hover:border-slate-300 hover:bg-white/80 hover:shadow-sm focus:border-white/30 focus:bg-white/80 focus:shadow-sm focus:ring-2 focus:ring-white/10 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-200 dark:placeholder:text-slate-500 dark:hover:border-white/20 dark:hover:shadow-white/5 dark:focus:border-white/20 dark:focus:bg-white/[0.06] dark:focus:shadow-white/5 dark:focus:ring-white/5"
      />
    </div>
  </div>
</template>
