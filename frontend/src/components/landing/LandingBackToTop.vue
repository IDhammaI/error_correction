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
    class="fixed bottom-8 right-8 z-50 flex h-10 w-10 items-center justify-center rounded-full brand-btn text-[#8a8f98] transition-[opacity,transform] duration-300 hover:text-[#f7f8f8]"
    :style="{ opacity: visible ? '1' : '0', transform: visible ? 'translateY(0)' : 'translateY(12px)', pointerEvents: visible ? 'auto' : 'none' }"
    aria-label="回到顶部"
    @click="emit('click')"
  >
    <ArrowUp class="h-4 w-4" />
  </button>
</template>
