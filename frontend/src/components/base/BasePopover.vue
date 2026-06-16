<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  placement: { type: String, default: 'bottom' },
  align: { type: String, default: 'left' },
  widthClass: { type: String, default: 'w-80' },
  panelClass: {
    type: String,
    default: 'rounded-xl border border-slate-200 bg-white p-4 shadow-xl shadow-black/10 dark:border-white/[0.08] dark:bg-[#1b1b1f] dark:shadow-black/40',
  },
})

const emit = defineEmits(['update:modelValue', 'open', 'close'])
const rootRef = ref(null)

function setOpen(value) {
  if (value === props.modelValue) return
  emit('update:modelValue', value)
  emit(value ? 'open' : 'close')
}

function syncClickOutside(event) {
  if (rootRef.value && !rootRef.value.contains(event.target)) {
    setOpen(false)
  }
}

onMounted(() => document.addEventListener('click', syncClickOutside))
onUnmounted(() => document.removeEventListener('click', syncClickOutside))
</script>

<template>
  <div ref="rootRef" class="relative inline-block">
    <div @click.stop="setOpen(!modelValue)">
      <slot name="trigger" :open="modelValue" />
    </div>
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="translate-y-1 opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-1 opacity-0"
    >
      <div
        v-if="modelValue"
        class="absolute z-[70] mt-2"
        :class="[
          widthClass,
          panelClass,
          placement === 'top' ? 'bottom-full mb-2 mt-0' : 'top-full',
          align === 'right' ? 'right-0' : align === 'center' ? 'left-1/2 -translate-x-1/2' : 'left-0',
        ]"
        @click.stop
      >
        <slot :close="() => setOpen(false)" />
      </div>
    </Transition>
  </div>
</template>
