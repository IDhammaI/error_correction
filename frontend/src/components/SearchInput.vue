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
    <label v-if="label" class="mb-2 block text-[11px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-500">{{ label }}</label>
    <div class="relative group">
      <i :class="icon" class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-500 transition-colors dark:group-focus-within:text-indigo-400"></i>
      <input
        :value="modelValue"
        @input="emit('update:modelValue', $event.target.value)"
        type="text"
        :placeholder="placeholder"
        class="h-11 w-full rounded-xl border border-slate-200/60 bg-white/70 pl-11 pr-4 text-sm font-bold shadow-sm backdrop-blur-xl outline-none transition-all hover:border-blue-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-white/10 dark:bg-white/[0.06] dark:text-white dark:hover:border-indigo-500/30 dark:focus:border-indigo-500/50 dark:focus:ring-indigo-500/20"
      />
    </div>
  </div>
</template>
