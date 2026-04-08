<script setup>
import { ArrowUp } from 'lucide-vue-next'

const props = defineProps({
  visible: Boolean,
})

const emit = defineEmits(['click'])
</script>

<template>
  <!-- 回到顶部按钮 -->
  <button
    id="back-to-top"
    class="fixed bottom-8 right-8 z-50 flex h-10 w-10 items-center justify-center rounded-full border border-slate-200/60 bg-white/80 text-slate-500 shadow-md transition-[opacity,transform,box-shadow] duration-300 hover:text-blue-600 hover:border-blue-300/60 hover:shadow-[0_0_16px_4px_rgba(59,130,246,0.35)] dark:border-white/10 dark:bg-white/5 dark:text-slate-400 dark:hover:text-indigo-400 dark:hover:border-indigo-500/40 dark:hover:shadow-[0_0_16px_4px_rgba(99,102,241,0.5)]"
    :style="{ opacity: visible ? '1' : '0', transform: visible ? 'translateY(0)' : 'translateY(12px)', pointerEvents: visible ? 'auto' : 'none' }"
    aria-label="回到顶部"
    @click="emit('click')"
  >
    <ArrowUp class="h-4 w-4" />
  </button>
</template>
