<script setup>
import { computed } from 'vue'
import { useOverlay } from '@/composables/useOverlay.js'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  placement: { type: String, default: 'right' },
  widthClass: { type: String, default: 'w-full max-w-md' },
  closeOnBackdrop: { type: Boolean, default: true },
})

const emit = defineEmits(['close'])
const close = () => emit('close')
const { overlayRef, overlayStyle, backdropStyle } = useOverlay(
  computed(() => props.open),
  { onClose: close },
)

const panelClass = computed(() => {
  if (props.placement === 'left') return `left-0 top-0 h-full ${props.widthClass}`
  if (props.placement === 'bottom') return 'bottom-0 left-0 w-full max-h-[85vh]'
  return `right-0 top-0 h-full ${props.widthClass}`
})

const enterFrom = computed(() => {
  if (props.placement === 'left') return '-translate-x-full'
  if (props.placement === 'bottom') return 'translate-y-full'
  return 'translate-x-full'
})

function closeFromBackdrop() {
  if (props.closeOnBackdrop) emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition enter-active-class="transition-opacity duration-200" enter-from-class="opacity-0" leave-active-class="transition-opacity duration-150" leave-to-class="opacity-0">
      <div v-if="open" class="fixed inset-0 bg-black/40 backdrop-blur-sm" :style="backdropStyle" @click="closeFromBackdrop"></div>
    </Transition>

    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-to-class="translate-x-0 translate-y-0"
      :enter-from-class="enterFrom"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="translate-x-0 translate-y-0"
      :leave-to-class="enterFrom"
    >
      <aside
        v-if="open"
        ref="overlayRef"
        tabindex="-1"
        class="fixed flex flex-col overflow-hidden border-slate-200 bg-white shadow-2xl dark:border-white/[0.08] dark:bg-[#17171a]"
        :class="[panelClass, placement === 'bottom' ? 'rounded-t-2xl border-t' : placement === 'left' ? 'border-r' : 'border-l']"
        :style="overlayStyle"
      >
        <header class="flex shrink-0 items-start justify-between gap-4 border-b border-slate-200/70 px-5 py-4 dark:border-white/[0.06]">
          <div class="min-w-0">
            <h2 v-if="title" class="text-base font-bold text-slate-900 dark:text-[#f7f8f8]">{{ title }}</h2>
            <p v-if="description" class="mt-1 text-sm leading-5 text-slate-500 dark:text-[#8a8f98]">{{ description }}</p>
          </div>
          <button type="button" class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-white/[0.06] dark:hover:text-[#d0d6e0]" @click="emit('close')">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </header>

        <div class="min-h-0 flex-1 overflow-y-auto custom-scrollbar p-5">
          <slot />
        </div>

        <footer v-if="$slots.footer" class="shrink-0 border-t border-slate-200/70 px-5 py-3 dark:border-white/[0.06]">
          <slot name="footer" />
        </footer>
      </aside>
    </Transition>
  </Teleport>
</template>
