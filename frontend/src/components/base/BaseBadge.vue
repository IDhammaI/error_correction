<script setup>
defineProps({
  value: { type: [String, Number], default: '' },
  tone: { type: String, default: 'accent' },
  dot: { type: Boolean, default: false },
  max: { type: Number, default: 99 },
})

const toneClass = {
  accent: 'accent-bg text-white',
  neutral: 'bg-slate-500 text-white dark:bg-white/[0.18]',
  rose: 'bg-rose-500 text-white',
  amber: 'bg-amber-500 text-white',
  emerald: 'bg-emerald-500 text-white',
  blue: 'bg-blue-500 text-white',
}
</script>

<template>
  <span class="relative inline-flex">
    <slot />
    <span
      class="absolute -right-1.5 -top-1.5 inline-flex shrink-0 items-center justify-center rounded-full text-[10px] font-bold leading-none shadow-sm ring-2 ring-white dark:ring-[#0c0c0e]"
      :class="[
        toneClass[tone] || toneClass.accent,
        dot ? 'h-2.5 w-2.5' : 'min-w-5 h-5 px-1',
      ]"
    >
      <span v-if="!dot">{{ typeof value === 'number' && value > max ? `${max}+` : value }}</span>
    </span>
  </span>
</template>
