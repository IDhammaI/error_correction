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
    <label v-if="label" class="mb-2 block text-xs font-black uppercase tracking-widest text-slate-500 dark:text-slate-500">{{ label }}</label>
    <button
      type="button"
      @click.stop="toggle"
      class="flex h-10 w-full items-center justify-between rounded-xl border border-slate-200/80 bg-white/70 px-4 text-left text-sm font-bold backdrop-blur-xl transition-all dark:border-white/10 dark:bg-slate-800/60"
      :class="[
        open ? 'border-blue-400 ring-2 ring-blue-500/20 dark:border-indigo-500/50 dark:ring-indigo-500/20' : 'hover:border-blue-300 dark:hover:border-indigo-500/30',
        modelValue ? 'text-slate-800 dark:text-slate-200' : 'text-slate-400 dark:text-slate-500',
      ]"
    >
      <span class="truncate">{{ modelValue || placeholder }}</span>
      <i class="fa-solid fa-chevron-down ml-2 text-xs text-slate-400 transition-transform duration-300" :class="open ? 'rotate-180' : ''"></i>
    </button>
    <Transition name="dropdown">
      <div v-if="open" class="absolute left-0 top-full z-50 mt-1 max-h-56 w-full overflow-y-auto rounded-xl border border-slate-200/60 bg-white/80 py-1 shadow-md backdrop-blur-2xl dark:border-white/10 dark:bg-slate-800/70 dark:backdrop-blur-2xl">
        <button
          type="button"
          @click.stop="select('')"
          class="flex w-full items-center gap-2 px-4 py-2 text-left text-sm transition-colors hover:bg-blue-50/80 dark:hover:bg-blue-500/10"
          :class="modelValue === '' ? 'font-bold text-blue-600 dark:text-blue-400' : 'text-slate-700 dark:text-slate-300'"
        >
          <i v-if="modelValue === ''" class="fa-solid fa-check text-xs text-blue-500"></i>
          <span :class="modelValue !== '' ? 'pl-[18px]' : ''">
            <i v-if="icon" class="fa-solid fa-layer-group mr-2 text-xs text-slate-400 dark:text-slate-500"></i>{{ placeholder }}
          </span>
        </button>
        <button
          v-for="opt in options" :key="opt"
          type="button"
          @click.stop="select(opt)"
          class="flex w-full items-center gap-2 px-4 py-2 text-left text-sm transition-colors hover:bg-blue-50/80 dark:hover:bg-blue-500/10"
          :class="modelValue === opt ? 'font-bold text-blue-600 dark:text-blue-400' : 'text-slate-700 dark:text-slate-300'"
        >
          <i v-if="modelValue === opt" class="fa-solid fa-check text-xs text-blue-500"></i>
          <span :class="modelValue !== opt ? 'pl-[18px]' : ''">
            <i v-if="icon" class="fa-solid mr-2 text-xs" :class="icon(opt)"></i>{{ opt }}
          </span>
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
