<script setup>
/**
 * BaseStatusPill.vue
 * 通用状态徽标，用统一视觉表达加载中、正常、异常、占位等状态。
 */
defineProps({
  label: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  ok: { type: Boolean, default: false },
  placeholder: { type: Boolean, default: false },
})

/**
 * 根据状态选择徽标颜色和图标。
 */
const getToneClass = ({ loading, ok, placeholder }) => {
  if (loading) return 'border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-400'
  if (placeholder) return 'border-gray-200 bg-gray-100 text-gray-500 dark:border-white/[0.05] dark:bg-white/[0.03] dark:text-[#62666d]'
  if (ok) return 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
  return 'border-rose-500/20 bg-rose-500/10 text-rose-500 dark:text-rose-400'
}

const getIconClass = ({ loading, ok, placeholder }) => {
  if (loading) return 'fa-spinner animate-spin'
  if (placeholder) return 'fa-hourglass-start'
  if (ok) return 'fa-check'
  return 'fa-xmark'
}

const getIconKey = ({ loading, ok, placeholder }) => {
  if (loading) return 'loading'
  if (placeholder) return 'placeholder'
  if (ok) return 'ok'
  return 'error'
}
</script>

<template>
  <span
    class="inline-flex items-center gap-2 rounded-lg !border-none px-3 py-1.5 text-xs font-medium transition-colors"
    :class="getToneClass({ loading, ok, placeholder })"
  >
    <span class="relative h-2.5 w-2.5 shrink-0">
      <Transition name="icon-pop">
        <i
          :key="getIconKey({ loading, ok, placeholder })"
          class="fa-solid absolute inset-0 flex items-center justify-center text-[10px]"
          :class="getIconClass({ loading, ok, placeholder })"
        ></i>
      </Transition>
    </span>
    {{ label }}
  </span>
</template>

<style scoped>
.icon-pop-enter-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.icon-pop-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.icon-pop-enter-from {
  opacity: 0;
  transform: scale(0.3) rotate(-180deg);
}

.icon-pop-leave-to {
  opacity: 0;
  transform: scale(0.3) rotate(180deg);
}
</style>
