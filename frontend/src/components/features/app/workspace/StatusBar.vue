<script setup>
/**
 * 工作台顶部状态栏。
 *
 * 汇总引擎连接状态；宽屏展开显示，窄屏收起为一个状态按钮。
 */
import { computed } from 'vue'
import BaseStatusPill from '@/components/base/BaseStatusPill.vue'

const props = defineProps({
  statusLoading: { type: Boolean, default: true },
  statusError: { type: String, default: '' },
  statusPills: { type: Array, default: () => [] },
})

const hasLoading = computed(() => props.statusLoading || props.statusPills.some((p) => p.loading))
const hasFailed = computed(() => props.statusPills.some((p) => !p.ok && !p.isPlaceholder && !p.loading))

const summaryToneClass = computed(() => {
  if (props.statusError || hasFailed.value) return 'border-rose-500/20 bg-rose-500/10 text-rose-500 dark:text-rose-400'
  if (hasLoading.value) return 'border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-400'
  return 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
})

const summaryIconClass = computed(() => {
  if (props.statusError || hasFailed.value) return 'fa-circle-exclamation'
  if (hasLoading.value) return 'fa-spinner animate-spin'
  return 'fa-check'
})
</script>

<template>
  <div class="engine-status relative z-20 shrink-0 text-sm">
    <div class="engine-status-inline flex flex-wrap items-center gap-4">
      <div class="flex items-center gap-2.5">
        <span class="text-xs font-medium uppercase tracking-[0.15em] text-gray-500 transition-colors dark:text-[#62666d]">
          引擎状态
        </span>
      </div>

      <div class="h-4 w-px bg-gray-300 transition-colors dark:bg-white/[0.08]"></div>

      <span
        v-if="statusError"
        class="inline-flex items-center gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-1.5 text-xs font-medium text-rose-500 transition-colors dark:text-rose-400"
      >
        <i class="fa-solid fa-circle-exclamation animate-pulse"></i>
        {{ statusError }}
      </span>

      <div v-else class="flex flex-wrap items-center gap-2.5">
        <BaseStatusPill
          v-for="p in statusPills"
          :key="p.key"
          :label="p.label"
          :loading="p.loading"
          :ok="p.ok"
          :placeholder="p.isPlaceholder"
        />
      </div>
    </div>

    <div class="engine-status-compact group relative">
      <button
        type="button"
        class="inline-flex h-8 w-9 items-center justify-center rounded-lg border transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[rgb(var(--accent-rgb)/0.35)]"
        :class="summaryToneClass"
        aria-label="引擎状态"
      >
        <i class="fa-solid text-[11px]" :class="summaryIconClass"></i>
      </button>

      <div
        class="engine-status-popover pointer-events-none absolute right-0 top-full z-[80] mt-2 min-w-[220px] rounded-lg border border-gray-200 bg-white/95 p-2 opacity-0 shadow-xl shadow-black/10 backdrop-blur-xl transition-[opacity,transform] duration-150 group-hover:pointer-events-auto group-hover:translate-y-0 group-hover:opacity-100 group-focus-within:pointer-events-auto group-focus-within:translate-y-0 group-focus-within:opacity-100 dark:border-white/[0.08] dark:bg-[#17171d]/95 dark:shadow-black/30"
      >
        <div class="mb-2 px-1 text-xs font-medium uppercase tracking-[0.15em] text-gray-500 dark:text-[#62666d]">
          引擎状态
        </div>
        <span
          v-if="statusError"
          class="inline-flex items-center gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-1.5 text-xs font-medium text-rose-500 transition-colors dark:text-rose-400"
        >
          <i class="fa-solid fa-circle-exclamation animate-pulse"></i>
          {{ statusError }}
        </span>
        <div v-else class="flex flex-col gap-2">
          <BaseStatusPill
            v-for="p in statusPills"
            :key="p.key"
            :label="p.label"
            :loading="p.loading"
            :ok="p.ok"
            :placeholder="p.isPlaceholder"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.engine-status-compact {
  display: none;
}

.engine-status-popover {
  transform: translateY(-4px);
}

@media (max-width: 1280px) {
  .engine-status-inline {
    display: none;
  }

  .engine-status-compact {
    display: block;
  }
}
</style>
