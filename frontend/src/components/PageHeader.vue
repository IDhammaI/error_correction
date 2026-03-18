<script setup>
/**
 * PageHeader.vue
 * 统一的页面顶部组件，支持徽章、标题、副标题以及右侧操作区插槽。
 * 采用了现代化的磨砂感设计和优雅的入场动画。
 */
defineProps({
  badge: { type: String, default: '' },
  badgeIcon: { type: String, default: '' },
  badgeColor: { type: String, default: 'indigo' }, // 支持 indigo, blue, emerald, amber, rose, slate
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  subtitleIcon: { type: String, default: '' },
})

// 颜色映射，确保 Tailwind JIT 能识别并生成对应的样式
const colorMap = {
  indigo: 'border-indigo-200 bg-indigo-50 text-indigo-600 dark:border-indigo-500/30 dark:bg-indigo-500/10 dark:text-indigo-300 shadow-indigo-500/10',
  blue: 'border-blue-200 bg-blue-50 text-blue-600 dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-300 shadow-blue-500/10',
  emerald: 'border-emerald-200 bg-emerald-50 text-emerald-600 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300 shadow-emerald-500/10',
  amber: 'border-amber-200 bg-amber-50 text-amber-600 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300 shadow-amber-500/10',
  rose: 'border-rose-200 bg-rose-50 text-rose-600 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300 shadow-rose-500/10',
  slate: 'border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-500/30 dark:bg-slate-500/10 dark:text-slate-300 shadow-slate-500/10',
}
</script>

<template>
  <header class="page-header relative z-30 mb-8 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
    <div class="flex flex-col items-start space-y-2">
      <!-- 顶部徽章 -->
      <div
        v-if="badge"
        class="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-black uppercase tracking-widest shadow-sm"
        :class="colorMap[badgeColor] || colorMap.indigo"
      >
        <i v-if="badgeIcon" :class="badgeIcon" class="animate-pulse"></i>
        <span>{{ badge }}</span>
      </div>

      <div class="space-y-1">
        <!-- 标题：大而有力的排版，增强视觉重心 -->
        <h2 class="text-3xl font-black tracking-tight text-slate-900 sm:text-4xl dark:text-white">
          {{ title }}
        </h2>

        <!-- 副标题：柔和的辅助信息 -->
        <p v-if="subtitle" class="flex items-center gap-2 text-sm font-bold text-slate-500 dark:text-slate-400">
          <i v-if="subtitleIcon" :class="subtitleIcon" class="opacity-60"></i>
          <span>{{ subtitle }}</span>
        </p>
      </div>
    </div>

    <!-- 右侧操作区：通过 extra 插槽注入按钮、搜索框或筛选器 -->
    <div v-if="$slots.extra" class="flex shrink-0 items-center gap-4">
      <slot name="extra"></slot>
    </div>
  </header>
</template>
