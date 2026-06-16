<script setup>
import { computed } from 'vue'

const props = defineProps({
  src: { type: String, default: '' },
  name: { type: String, default: '' },
  icon: { type: String, default: '' },
  size: { type: String, default: 'md' },
  tone: { type: String, default: 'accent' },
})

const initials = computed(() => {
  const text = props.name.trim()
  if (!text) return ''
  const words = text.split(/\s+/).filter(Boolean)
  if (words.length > 1) return words.slice(0, 2).map(word => word[0]).join('').toUpperCase()
  return text.slice(0, 2).toUpperCase()
})

const sizeClass = {
  xs: 'h-6 w-6 text-[10px]',
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-12 w-12 text-base',
}

const toneClass = {
  accent: 'accent-bg-soft accent-text',
  neutral: 'bg-slate-100 text-slate-600 dark:bg-white/[0.08] dark:text-[#d0d6e0]',
  blue: 'bg-blue-500/10 text-blue-600 dark:text-blue-300',
  emerald: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-300',
  rose: 'bg-rose-500/10 text-rose-600 dark:text-rose-300',
}
</script>

<template>
  <span
    class="inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full font-bold ring-1 ring-black/[0.04] dark:ring-white/[0.08]"
    :class="[sizeClass[size] || sizeClass.md, toneClass[tone] || toneClass.accent]"
    :title="name"
  >
    <img v-if="src" :src="src" :alt="name || 'avatar'" class="h-full w-full object-cover" />
    <i v-else-if="icon" class="fa-solid" :class="icon"></i>
    <span v-else>{{ initials || '?' }}</span>
  </span>
</template>
