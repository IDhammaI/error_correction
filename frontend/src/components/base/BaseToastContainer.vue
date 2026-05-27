<script setup>
/**
 * BaseToastContainer.vue
 * Linear-like global toast stack.
 */
defineProps({
  toasts: { type: Array, default: () => [] },
  sidebarOffset: { type: Number, default: 0 },
})

const emit = defineEmits(['dismiss'])

const iconClassMap = {
  success: 'fa-circle-check text-emerald-400',
  error: 'fa-circle-xmark text-rose-400',
  warning: 'fa-triangle-exclamation text-amber-400',
  info: 'fa-circle-info accent-text',
}

const fallbackTitleMap = {
  success: 'Success',
  error: 'Error',
  warning: 'Warning',
  info: 'Information',
}

const titleOf = (toast) => toast.title || toast.message || fallbackTitleMap[toast.type] || 'Notice'

const onLeave = (el) => {
  const { left, top, width, height } = el.getBoundingClientRect()
  el.style.left = `${left}px`
  el.style.top = `${top}px`
  el.style.width = `${width}px`
  el.style.height = `${height}px`
  el.style.position = 'absolute'
}
</script>

<template>
  <div
    class="pointer-events-none fixed bottom-5 right-5 z-[200] flex w-[calc(100vw-2.5rem)] max-w-[26.5rem] flex-col items-stretch gap-2"
    :style="{ '--sidebar-offset': `${sidebarOffset}px` }"
  >
    <TransitionGroup
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="translate-y-3 scale-[0.98] opacity-0"
      enter-to-class="translate-y-0 scale-100 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="translate-y-0 scale-100 opacity-100"
      leave-to-class="translate-y-2 scale-[0.98] opacity-0"
      move-class="transition duration-200 ease-out"
      @leave="onLeave"
    >
      <div
        v-for="toast in toasts"
        :key="toast.id"
        role="status"
        class="pointer-events-auto flex gap-3 rounded-xl border border-white/[0.09] bg-[#202022]/95 px-3.5 py-3 text-[#f7f8f8] shadow-[0_18px_50px_rgba(0,0,0,0.38)] ring-1 ring-black/20 backdrop-blur-xl"
      >
        <div class="flex h-5 w-5 shrink-0 items-center justify-center pt-0.5">
          <i
            class="fa-solid text-[15px]"
            :class="iconClassMap[toast.type] || iconClassMap.info"
          ></i>
        </div>

        <div class="flex min-w-0 flex-1 flex-col gap-1.5">
          <div class="flex min-w-0 items-start justify-between gap-3">
            <p class="line-clamp-2 min-w-0 text-sm font-semibold leading-5 text-[#f7f8f8]">
              {{ titleOf(toast) }}
            </p>
            <button
              type="button"
              class="-mr-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-[#8a8f98] transition-colors hover:bg-white/[0.06] hover:text-[#f7f8f8]"
              title="关闭"
              @click="emit('dismiss', toast.id)"
            >
              <i class="fa-solid fa-xmark text-xs"></i>
            </button>
          </div>

          <p
            v-if="toast.description"
            class="line-clamp-2 text-[13px] leading-5 text-[#a8adb7]"
          >
            {{ toast.description }}
          </p>

          <a
            v-if="toast.action?.href"
            :href="toast.action.href"
            class="mt-1 inline-flex w-fit text-sm font-medium accent-text transition-colors hover:text-[rgb(var(--accent-hover-rgb))]"
          >
            {{ toast.action.label || '查看' }}
          </a>
          <button
            v-else-if="toast.action?.label"
            type="button"
            class="mt-1 inline-flex w-fit text-sm font-medium accent-text transition-colors hover:text-[rgb(var(--accent-hover-rgb))]"
            @click="toast.action.onClick?.(); emit('dismiss', toast.id)"
          >
            {{ toast.action.label }}
          </button>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>
