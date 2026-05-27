<script setup>
/**
 * BaseSelect.vue
 * 自定义下拉选择器
 */
import { onBeforeUnmount, ref } from 'vue'
import { useClickOutside } from '@/composables/useClickOutside.js'

const props = defineProps({
  modelValue: { type: String, default: '' },
  options: { type: Array, default: () => [] },
  label: { type: String, default: '' },
  placeholder: { type: String, default: '全部' },
  icon: { type: Function, default: null },
  widthClass: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])
const open = ref(false)
const selectId = `base-select-${Math.random().toString(36).slice(2)}`

useClickOutside('.custom-select-wrapper', () => { open.value = false })

const closeOtherSelects = (event) => {
  if (event.detail !== selectId) open.value = false
}

window.addEventListener('base-filter-popover-open', closeOtherSelects)

onBeforeUnmount(() => {
  window.removeEventListener('base-filter-popover-open', closeOtherSelects)
})

const toggle = () => {
  const nextOpen = !open.value
  if (nextOpen) window.dispatchEvent(new CustomEvent('base-filter-popover-open', { detail: selectId }))
  open.value = nextOpen
}
const select = (val) => { emit('update:modelValue', val); open.value = false }
</script>

<template>
  <div class="custom-select-wrapper relative" :class="widthClass">
    <label v-if="label" class="mb-1.5 block text-xs font-medium text-slate-500 dark:text-[#62666d]">{{ label }}</label>
    <button
      type="button"
      @click.stop="toggle"
      class="flex h-9 w-full items-center justify-between rounded-md bg-white/80 px-3 text-left text-sm font-medium text-slate-500 ring-1 ring-inset ring-transparent transition-colors hover:bg-white dark:bg-white/[0.045] dark:hover:bg-white/[0.07]"
      :class="[
        open ? 'bg-white ring-[rgb(var(--accent-rgb)/0.24)] dark:bg-white/[0.08] dark:ring-[rgb(var(--accent-rgb)/0.35)]' : '',
        modelValue ? 'text-slate-800 dark:text-[#d0d6e0]' : 'text-slate-500 dark:text-[#62666d]',
      ]"
    >
      <span class="truncate">{{ modelValue || placeholder }}</span>
      <i class="fa-solid fa-chevron-down ml-2 text-[10px] text-slate-400 transition-transform duration-200 dark:text-[#62666d]" :class="open ? 'rotate-180' : ''"></i>
    </button>
    <Transition name="dropdown">
      <div v-if="open" class="absolute left-0 top-full z-50 mt-1 min-w-full overflow-hidden rounded-lg border border-gray-200 bg-white/95 p-1.5 shadow-lg shadow-slate-200/60 dark:border-white/[0.08] dark:bg-[#1f1f22] dark:shadow-black/40">
        <div class="no-scrollbar max-h-56 overflow-y-auto space-y-0.5">
          <button
            type="button"
            @click.stop="select('')"
            class="flex h-8 w-full items-center gap-2 rounded-md border px-2.5 text-left text-sm transition-colors"
            :class="modelValue === ''
              ? 'accent-bg-soft accent-text accent-border'
              : 'border-transparent text-slate-600 hover:bg-slate-100/80 dark:text-[#d0d6e0] dark:hover:bg-white/[0.07]'"
          >
            <span class="min-w-0 flex-1 truncate">{{ placeholder }}</span>
            <i v-if="modelValue === ''" class="fa-solid fa-check shrink-0 text-[10px] accent-text"></i>
          </button>
          <button
            v-for="opt in options" :key="opt"
            type="button"
            @click.stop="select(opt)"
            class="flex h-8 w-full items-center gap-2 rounded-md border px-2.5 text-left text-sm transition-colors"
            :class="modelValue === opt
              ? 'accent-bg-soft accent-text accent-border'
              : 'border-transparent text-slate-600 hover:bg-slate-100/80 dark:text-[#d0d6e0] dark:hover:bg-white/[0.07]'"
          >
            <span class="min-w-0 flex-1 truncate">{{ opt }}</span>
            <i v-if="modelValue === opt" class="fa-solid fa-check shrink-0 text-[10px] accent-text"></i>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease-out;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
