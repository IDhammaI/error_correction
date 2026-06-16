<script setup>
defineProps({
  modelValue: { type: [String, Number], default: '' },
  items: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue', 'select'])

function select(item) {
  if (item.disabled) return
  emit('update:modelValue', item.value)
  emit('select', item)
}
</script>

<template>
  <nav class="grid gap-1 rounded-xl border border-slate-200 bg-white/70 p-1.5 dark:border-white/[0.08] dark:bg-white/[0.025]">
    <button
      v-for="item in items"
      :key="item.value"
      type="button"
      class="flex min-h-10 items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-medium transition-colors"
      :class="[
        modelValue === item.value
          ? 'accent-bg-soft accent-text'
          : 'text-slate-600 hover:bg-slate-100 dark:text-[#a8adb7] dark:hover:bg-white/[0.05]',
        item.disabled ? 'cursor-not-allowed opacity-50' : '',
      ]"
      :disabled="item.disabled"
      @click="select(item)"
    >
      <i v-if="item.icon" class="fa-solid w-4 shrink-0 text-center text-xs" :class="item.icon"></i>
      <span class="min-w-0 flex-1 truncate">{{ item.label }}</span>
      <span v-if="item.badge" class="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-bold text-slate-500 dark:bg-white/[0.08] dark:text-[#8a8f98]">
        {{ item.badge }}
      </span>
    </button>
  </nav>
</template>
