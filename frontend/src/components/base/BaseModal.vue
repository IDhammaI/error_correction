<script setup>
import { computed } from 'vue'
import { useOverlay } from '@/composables/useOverlay.js'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, required: true },
  icon: { type: String, default: '' },
  iconClass: { type: String, default: 'text-blue-600 dark:text-blue-400' },
  iconBg: { type: String, default: 'bg-blue-50 dark:bg-blue-500/10' },
  maxWidth: { type: String, default: 'max-w-md' },
  bodyClass: { type: String, default: 'px-6 py-5' },
  blurBackdrop: { type: Boolean, default: true },
  sidebarOffset: { type: Number, default: null },
})

const emit = defineEmits(['close'])

const close = () => emit('close')
const { overlayRef, overlayStyle, backdropStyle: overlayBackdropStyle } = useOverlay(
  computed(() => props.open),
  { onClose: close },
)

const backdropStyle = computed(() => ({
  '--dialog-backdrop-blur': props.blurBackdrop ? '8px' : '0px',
  ...overlayBackdropStyle.value,
}))
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog-overlay" appear>
      <div
        v-if="open"
        class="dialog-backdrop fixed inset-0 z-[100] bg-black/40 transition-all duration-300"
        :style="backdropStyle"
        @click="emit('close')"
      ></div>
    </Transition>

    <Transition name="dialog-content" appear>
      <div
        v-if="open"
        class="fixed inset-0 flex items-center justify-center p-4 transition-all duration-300"
        :style="overlayStyle"
        @click.self="emit('close')"
      >
        <div
          ref="overlayRef"
          tabindex="-1"
          class="relative w-full rounded-xl border border-slate-200/60 bg-white shadow-2xl dark:border-[#2f3336] dark:bg-[#1b1b1d]"
          :class="maxWidth"
        >
          <slot name="header" :close="close">
            <div class="flex items-center justify-between border-b border-slate-200/60 px-6 pt-5 pb-4 dark:border-[#2f3336]">
              <div class="flex items-center gap-3">
                <div v-if="$slots.icon || icon" class="flex h-9 w-9 items-center justify-center rounded-lg" :class="iconBg">
                  <slot name="icon">
                    <i class="fa-solid text-base" :class="[icon, iconClass]"></i>
                  </slot>
                </div>
                <h3 class="text-lg font-bold text-slate-900 dark:text-[#f7f8f8]">
                  {{ title }}
                </h3>
              </div>
              <button
                @click="emit('close')"
                class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/[0.04] dark:text-[#8a8f98] dark:hover:text-[#d0d6e0]"
              >
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>
          </slot>

          <div :class="bodyClass">
            <slot />
          </div>

          <div v-if="$slots.footer" class="flex min-h-16 items-center justify-end gap-2 rounded-b-xl border-t border-slate-200/60 px-6 py-3 dark:border-[#2f3336]">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-backdrop {
  backdrop-filter: blur(var(--dialog-backdrop-blur, 8px));
  -webkit-backdrop-filter: blur(var(--dialog-backdrop-blur, 8px));
}

.dialog-overlay-enter-active,
.dialog-overlay-leave-active {
  transition:
    opacity 0.22s ease,
    backdrop-filter 0.22s ease,
    -webkit-backdrop-filter 0.22s ease;
}

.dialog-overlay-enter-from,
.dialog-overlay-leave-to {
  opacity: 0;
  backdrop-filter: blur(var(--dialog-backdrop-blur, 8px));
  -webkit-backdrop-filter: blur(var(--dialog-backdrop-blur, 8px));
}

.dialog-content-enter-active,
.dialog-content-leave-active {
  transition: opacity 0.22s ease, transform 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

.dialog-content-enter-from,
.dialog-content-leave-to {
  opacity: 0;
  transform: scale(0.96) translateY(8px);
}
</style>
