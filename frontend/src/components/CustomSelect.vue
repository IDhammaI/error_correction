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
    <label v-if="label" class="mb-1.5 block text-xs font-medium text-[#62666d]">{{ label }}</label>
    <button
      type="button"
      @click.stop="toggle"
      class="flex h-9 w-full items-center justify-between rounded-md border border-white/[0.08] bg-white/[0.02] px-3 text-left text-sm font-medium transition-colors hover:border-white/[0.12]"
      :class="[
        open ? 'border-white/[0.15]' : '',
        modelValue ? 'text-[#d0d6e0]' : 'text-[#62666d]',
      ]"
    >
      <span class="truncate">{{ modelValue || placeholder }}</span>
      <i class="fa-solid fa-chevron-down ml-2 text-[10px] text-[#62666d] transition-transform duration-200" :class="open ? 'rotate-180' : ''"></i>
    </button>
    <Transition name="dropdown">
      <div v-if="open" class="absolute left-0 top-full z-50 mt-1 min-w-full w-max rounded-lg bg-[#1c1c20] py-1 shadow-lg shadow-black/40">
        <div class="no-scrollbar max-h-56 overflow-y-auto">
          <button
            type="button"
            @click.stop="select('')"
            class="dropdown-item"
            :class="modelValue === '' ? 'text-[#f7f8f8]' : ''"
          >
            <span>{{ placeholder }}</span>
            <i v-if="modelValue === ''" class="fa-solid fa-check ml-auto text-[10px] text-[rgb(129,115,223)]"></i>
          </button>
          <button
            v-for="opt in options" :key="opt"
            type="button"
            @click.stop="select(opt)"
            class="dropdown-item"
            :class="modelValue === opt ? 'text-[#f7f8f8]' : ''"
          >
            <span>{{ opt }}</span>
            <i v-if="modelValue === opt" class="fa-solid fa-check ml-auto text-[10px] text-[rgb(129,115,223)]"></i>
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
