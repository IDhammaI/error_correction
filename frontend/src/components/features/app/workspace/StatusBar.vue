<script setup>
/**
 * 工作台顶部状态栏。
 *
 * 汇总引擎连接状态和模型可用状态。
 */
import BaseStatusPill from '@/components/base/BaseStatusPill.vue'

defineProps({
  statusLoading: { type: Boolean, default: true },
  statusError: { type: String, default: '' },
  statusPills: { type: Array, default: () => [] },
})
</script>

<template>
  <div class="relative z-20 flex shrink-0 flex-wrap items-center gap-4 text-sm">
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

    <div v-if="!statusError" class="flex flex-wrap items-center gap-2.5">
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
</template>
