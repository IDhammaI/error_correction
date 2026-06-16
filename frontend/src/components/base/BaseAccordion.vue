<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number, Array], default: '' },
  items: { type: Array, default: () => [] },
  multiple: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'change'])
const internalValue = ref(props.modelValue)

watch(() => props.modelValue, value => {
  internalValue.value = value
})

const openValues = computed(() => {
  if (props.multiple) return Array.isArray(internalValue.value) ? internalValue.value : []
  return internalValue.value ? [internalValue.value] : []
})

function toggle(value) {
  let next
  if (props.multiple) {
    const set = new Set(openValues.value)
    if (set.has(value)) set.delete(value)
    else set.add(value)
    next = [...set]
  } else {
    next = openValues.value.includes(value) ? '' : value
  }
  internalValue.value = next
  emit('update:modelValue', next)
  emit('change', next)
}
</script>

<template>
  <div class="overflow-hidden rounded-xl border border-slate-200 bg-white/70 dark:border-white/[0.08] dark:bg-white/[0.025]">
    <div v-for="item in items" :key="item.value" class="border-b border-slate-200/70 last:border-b-0 dark:border-white/[0.06]">
      <button
        type="button"
        class="flex min-h-12 w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm font-semibold text-slate-800 transition-colors hover:bg-slate-50 dark:text-[#f7f8f8] dark:hover:bg-white/[0.04]"
        @click="toggle(item.value)"
      >
        <span class="min-w-0 truncate">{{ item.label }}</span>
        <i class="fa-solid fa-chevron-down shrink-0 text-[10px] text-slate-400 transition-transform" :class="openValues.includes(item.value) ? 'rotate-180' : ''"></i>
      </button>
      <Transition
        enter-active-class="transition duration-150 ease-out"
        enter-from-class="-translate-y-1 opacity-0"
        enter-to-class="translate-y-0 opacity-100"
        leave-active-class="transition duration-100 ease-in"
        leave-from-class="translate-y-0 opacity-100"
        leave-to-class="-translate-y-1 opacity-0"
      >
        <div v-if="openValues.includes(item.value)" class="px-4 pb-4 text-sm leading-6 text-slate-500 dark:text-[#8a8f98]">
          <slot name="item" :item="item">
            {{ item.content }}
          </slot>
        </div>
      </Transition>
    </div>
  </div>
</template>
