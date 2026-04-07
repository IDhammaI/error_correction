<script setup>
import { ref } from 'vue'
import { useClickOutside } from '../composables/useClickOutside.js'

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

useClickOutside('.custom-select-wrapper', () => { open.value = false })

const toggle = () => { open.value = !open.value }
const select = (val) => { emit('update:modelValue', val); open.value = false }
</script>

<template>
  <div class="custom-select-wrapper relative" :class="widthClass">
    <label v-if="label" class="mb-2 block text-[11px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-500">{{ label }}</label>
    <button
      type="button"
      @click.stop="toggle"
      class="flex h-11 w-full items-center justify-between rounded-xl border bg-white/60 px-4 text-left text-sm font-bold transition-all hover:border-slate-300 hover:bg-white/80 hover:shadow-sm dark:border-white/10 dark:bg-white/[0.03] dark:hover:border-white/20 dark:hover:shadow-white/5"
      :class="[
        open ? 'border-white/30 bg-white/80 shadow-sm ring-2 ring-white/10 dark:border-white/20 dark:bg-white/[0.06] dark:ring-white/5' : 'border-slate-200/60',
        modelValue ? 'text-slate-800 dark:text-slate-200' : 'text-slate-400 dark:text-slate-500',
      ]"
    >
      <span class="truncate">{{ modelValue || placeholder }}</span>
      <i class="fa-solid fa-chevron-down ml-2 text-xs text-slate-400 transition-transform duration-300 dark:text-slate-500" :class="open ? 'rotate-180' : ''"></i>
    </button>
    <Transition name="dropdown">
      <div v-if="open" class="absolute left-0 top-full z-50 mt-2 min-w-full w-max overflow-hidden rounded-2xl border border-slate-200/60 bg-white/95 p-1.5 shadow-xl dark:border-white/10 dark:bg-[#12121A]/90 dark:bg-gradient-to-b dark:from-white/[0.08] dark:to-transparent dark:shadow-[0_20px_50px_rgba(0,0,0,0.6)]">
        <div class="no-scrollbar max-h-56 space-y-0.5 overflow-y-auto">
          <button
            type="button"
            @click.stop="select('')"
            class="group flex w-full items-center gap-2 rounded-xl px-4 py-2.5 text-left text-sm font-bold transition-all hover:bg-white/60 hover:text-slate-800 dark:hover:bg-white/10 dark:hover:text-slate-100"
            :class="modelValue === '' ? 'bg-white/60 text-slate-800 dark:bg-white/10 dark:text-slate-100' : 'text-slate-600 dark:text-slate-300'"
          >
            <i v-if="icon" class="fa-solid fa-layer-group text-xs opacity-70"></i>
            <span>{{ placeholder }}</span>
            <i v-if="modelValue === ''" class="fa-solid fa-check ml-auto text-[10px]"></i>
          </button>
          <button
            v-for="opt in options" :key="opt"
            type="button"
            @click.stop="select(opt)"
            class="group flex w-full items-center gap-2 rounded-xl px-4 py-2.5 text-left text-sm font-bold transition-all hover:bg-white/60 hover:text-slate-800 dark:hover:bg-white/10 dark:hover:text-slate-100"
            :class="modelValue === opt ? 'bg-white/60 text-slate-800 dark:bg-white/10 dark:text-slate-100' : 'text-slate-600 dark:text-slate-300'"
          >
            <i v-if="icon" class="fa-solid text-xs opacity-70" :class="icon(opt)"></i>
            <span>{{ opt }}</span>
            <i v-if="modelValue === opt" class="fa-solid fa-check ml-auto text-[10px]"></i>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}
</style>
