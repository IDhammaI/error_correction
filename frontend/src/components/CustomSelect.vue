<script setup>
/**
 * 自定义下拉选择框组件
 *
 * Props:
 *   modelValue  — 当前选中值（v-model）
 *   options     — 选项列表，字符串数组
 *   label       — 顶部标签文字
 *   placeholder — 未选中时的占位文字
 *   icon        — 选项前的图标映射函数 (可选)，(option) => iconClass
 */
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

const toggle = () => {
  open.value = !open.value
}

const select = (val) => {
  emit('update:modelValue', val)
  open.value = false
}
</script>

<template>
  <div class="custom-select-wrapper relative" :class="widthClass">
    <label v-if="label" class="mb-2 block text-[11px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">{{ label }}</label>
    <div @click="toggle"
         class="flex h-11 w-full cursor-pointer items-center justify-between rounded-xl border border-slate-200/60 bg-white/50 px-3 text-sm font-bold text-slate-700 shadow-sm backdrop-blur-sm hover:-translate-y-0.5 hover:border-blue-400/50 hover:bg-white/70 hover:shadow-md dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:hover:border-indigo-500/30 dark:hover:bg-white/10"
         :class="{ 'border-blue-400 ring-2 ring-blue-500/20 bg-white/80 dark:border-indigo-500 dark:ring-indigo-500/20': open }">
      <span class="truncate">{{ modelValue || placeholder }}</span>
      <i class="fa-solid fa-chevron-down text-slate-400 transition-transform duration-300" :class="{ '-rotate-180': open }"></i>
    </div>
    <Transition name="dropdown">
      <div v-if="open" class="absolute left-0 top-full z-50 mt-2 min-w-full w-max overflow-hidden rounded-2xl border border-slate-200 bg-white p-1.5 shadow-2xl shadow-black/10 dark:border-slate-600 dark:bg-slate-800">
        <div class="no-scrollbar max-h-56 space-y-1 overflow-y-auto pr-1">
          <!-- 全部（空值）选项 -->
          <div @click.stop="select('')"
               class="cursor-pointer whitespace-nowrap rounded-xl px-3 py-2.5 text-sm font-bold text-slate-600 hover:-translate-y-0.5 hover:bg-slate-100 hover:text-blue-600 hover:shadow-sm dark:text-slate-200 dark:hover:bg-slate-700 dark:hover:text-indigo-300"
               :class="{ 'bg-blue-50 text-blue-600 dark:bg-indigo-500/20 dark:text-indigo-300': modelValue === '' }">
            <i v-if="icon" class="fa-solid fa-layer-group mr-1.5 text-slate-400"></i>{{ placeholder }}
          </div>
          <!-- 选项列表 -->
          <div v-for="opt in options" :key="opt" @click.stop="select(opt)"
               class="cursor-pointer whitespace-nowrap rounded-xl px-3 py-2.5 text-sm font-bold text-slate-600 hover:-translate-y-0.5 hover:bg-slate-100 hover:text-blue-600 hover:shadow-sm dark:text-slate-200 dark:hover:bg-slate-700 dark:hover:text-indigo-300"
               :class="{ 'bg-blue-50 text-blue-600 dark:bg-indigo-500/20 dark:text-indigo-300': modelValue === opt }">
            <i v-if="icon" class="fa-solid mr-1.5" :class="icon(opt)"></i>{{ opt }}
          </div>
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
