<script setup>
/**
 * BaseTag.vue
 * 通用标签组件，用于状态、分类、知识点等短文本标记。
 */
const props = defineProps({
  tone: { type: String, default: 'neutral' },
  size: { type: String, default: 'sm' },
  active: { type: Boolean, default: false },
})

const toneClass = {
  neutral: 'border-gray-200 bg-gray-100/80 text-gray-500 dark:border-white/[0.06] dark:bg-white/[0.045] dark:text-[#8a8f98]',
  accent: 'accent-bg-soft accent-text accent-border',
  rose: 'border-rose-500/20 bg-rose-500/10 text-rose-500 dark:text-rose-300',
  amber: 'border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-300',
  emerald: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300',
  blue: 'border-blue-500/20 bg-blue-500/10 text-blue-600 dark:text-blue-300',
}
</script>

<template>
  <span
    class="inline-flex max-w-full items-center gap-1 rounded-full border font-bold leading-none transition-colors"
    :class="[
      props.size === 'xs' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-0.5 text-[11px]',
      toneClass[props.tone] || toneClass.neutral,
      props.active ? 'ring-1 ring-[rgb(var(--accent-rgb)/0.35)]' : '',
    ]"
  >
    <slot />
  </span>
</template>
