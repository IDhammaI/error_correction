<script setup>
import { ref } from 'vue'

const props = defineProps({
  text: { type: String, default: '' },
  label: { type: String, default: '复制' },
  copiedLabel: { type: String, default: '已复制' },
})

const emit = defineEmits(['copy', 'error'])
const copied = ref(false)

async function copy() {
  try {
    await navigator.clipboard.writeText(props.text)
    copied.value = true
    emit('copy', props.text)
    window.setTimeout(() => {
      copied.value = false
    }, 1200)
  } catch (error) {
    emit('error', error)
  }
}
</script>

<template>
  <button
    type="button"
    class="inline-flex h-8 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 text-xs font-bold text-slate-600 transition-colors hover:bg-slate-50 dark:border-white/[0.08] dark:bg-white/[0.04] dark:text-[#d0d6e0] dark:hover:bg-white/[0.07]"
    @click="copy"
  >
    <i class="fa-solid text-[10px]" :class="copied ? 'fa-check text-emerald-500' : 'fa-copy'"></i>
    {{ copied ? copiedLabel : label }}
  </button>
</template>
