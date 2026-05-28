<script setup>
/**
 * BaseStat.vue
 * 通用统计卡片组件，用于展示数值、单位、说明和图标。
 */
const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: 0 },
  suffix: { type: String, default: '' },
  hint: { type: String, default: '' },
  icon: { type: String, default: '' },
  tone: { type: String, default: 'accent' },
})

const toneClass = {
  accent: 'accent-bg-soft accent-text',
  blue: 'bg-blue-500/20 text-blue-300',
  rose: 'bg-rose-500/20 text-rose-300',
  amber: 'bg-amber-500/20 text-amber-300',
  emerald: 'bg-emerald-500/20 text-emerald-300',
  orange: 'bg-orange-500/20 text-orange-300',
}
</script>

<template>
  <div class="rounded-xl bg-white/85 p-4 shadow-sm shadow-black/[0.03] transition-colors duration-200 hover:bg-white dark:bg-white/[0.04] dark:shadow-black/20 dark:hover:bg-white/[0.065]">
    <div class="flex items-center gap-3">
      <div v-if="icon || $slots.icon" class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl" :class="toneClass[props.tone] || toneClass.accent">
        <slot name="icon">
          <i class="fa-solid" :class="icon"></i>
        </slot>
      </div>
      <div class="min-w-0">
        <p class="text-xs font-medium text-gray-500 dark:text-[#8a8f98]">{{ label }}</p>
        <p class="mt-0.5 text-2xl font-semibold text-gray-900 dark:text-[#f7f8f8]">
          {{ value }}<span v-if="suffix" class="ml-1 text-sm text-gray-500 dark:text-[#8a8f98]">{{ suffix }}</span>
        </p>
        <p v-if="hint" class="mt-0.5 truncate text-xs text-gray-400 dark:text-[#62666d]">{{ hint }}</p>
      </div>
    </div>
  </div>
</template>
