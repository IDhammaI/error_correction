<script setup>
defineProps({
  count: { type: Number, default: 4 },
})
</script>

<template>
  <div class="space-y-4">
    <div
      v-for="i in count" :key="i"
      class="rounded-2xl border border-slate-200/60 bg-white/70 p-6 backdrop-blur-xl dark:border-white/10 dark:bg-white/[0.03]"
    >
      <div class="flex items-start gap-4 animate-pulse">
        <!-- 复选框占位 -->
        <div class="mt-1 h-5 w-5 shrink-0 rounded-lg bg-slate-200 dark:bg-slate-700"></div>

        <div class="min-w-0 flex-1 space-y-4">
          <!-- 标签行 -->
          <div class="flex items-center gap-2">
            <div class="h-6 w-16 rounded-full bg-slate-200 dark:bg-slate-700"></div>
            <div class="h-6 w-12 rounded-full bg-slate-200 dark:bg-slate-700"></div>
            <div class="h-6 w-20 rounded-full bg-slate-200 dark:bg-slate-700"></div>
            <div class="ml-auto h-6 w-14 rounded-full bg-slate-200 dark:bg-slate-700"></div>
          </div>

          <!-- 内容行 -->
          <div class="space-y-2">
            <div class="h-4 w-full rounded-lg bg-slate-200 dark:bg-slate-700"></div>
            <div class="h-4 w-3/4 rounded-lg bg-slate-200 dark:bg-slate-700"></div>
          </div>

          <!-- 底部状态 -->
          <div class="flex items-center gap-2">
            <div class="h-6 w-20 rounded-full bg-slate-200 dark:bg-slate-700"></div>
            <div class="h-6 w-16 rounded-full bg-slate-200 dark:bg-slate-700"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
