<script setup>
/**
 * BasePopconfirm.vue
 * 轻量二次确认浮层，用于替代 window.confirm。
 */
import { ref } from 'vue'

const props = defineProps({
  title: { type: String, default: '确认操作？' },
  description: { type: String, default: '' },
  confirmText: { type: String, default: '确认' },
  cancelText: { type: String, default: '取消' },
  danger: { type: Boolean, default: false },
})

const emit = defineEmits(['confirm', 'cancel'])
const open = ref(false)

const confirm = () => {
  open.value = false
  emit('confirm')
}

const cancel = () => {
  open.value = false
  emit('cancel')
}
</script>

<template>
  <span class="relative inline-flex" @click.stop>
    <span @click="open = !open">
      <slot />
    </span>
    <Transition name="pop">
      <div
        v-if="open"
        class="absolute right-0 top-full z-[80] mt-2 w-64 rounded-xl border border-gray-200 bg-white p-3 shadow-xl shadow-black/10 dark:border-white/[0.08] dark:bg-[#1d1e22] dark:shadow-black/40"
      >
        <p class="text-sm font-bold text-gray-900 dark:text-[#f7f8f8]">{{ title }}</p>
        <p v-if="description" class="mt-1 text-xs leading-5 text-gray-500 dark:text-[#8a8f98]">{{ description }}</p>
        <div class="mt-3 flex justify-end gap-2">
          <button class="h-8 rounded-lg px-3 text-xs font-bold text-gray-500 transition-colors hover:bg-gray-100 dark:text-[#8a8f98] dark:hover:bg-white/[0.06]" @click="cancel">
            {{ cancelText }}
          </button>
          <button
            class="h-8 rounded-lg px-3 text-xs font-bold text-white transition-colors"
            :class="danger ? 'bg-rose-500 hover:bg-rose-400' : 'accent-bg hover:opacity-90'"
            @click="confirm"
          >
            {{ confirmText }}
          </button>
        </div>
      </div>
    </Transition>
  </span>
</template>

<style scoped>
.pop-enter-active,
.pop-leave-active {
  transition: opacity 0.14s ease, transform 0.14s ease;
}
.pop-enter-from,
.pop-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}
</style>
