<script setup>
defineProps({
  count: { type: Number, default: 0 },
  visible: { type: Boolean, default: false },
})

const emit = defineEmits(['export', 'clear'])
</script>

<template>
  <Transition
    enter-active-class="transition-transform duration-300 ease-out"
    enter-from-class="translate-y-12"
    enter-to-class="translate-y-0"
    leave-active-class="transition-transform duration-200 ease-in"
    leave-from-class="translate-y-0"
    leave-to-class="translate-y-12"
  >
    <div v-if="visible && count" class="fixed bottom-24 left-1/2 z-50 -translate-x-1/2 md:bottom-10">
      <div class="flex items-center gap-6 rounded-full border border-slate-200/60 bg-white/70 px-6 py-3 shadow-md backdrop-blur-xl dark:border-white/10 dark:bg-white/[0.03]">
        <div class="flex items-center gap-3 border-r border-slate-200/60 pr-6 dark:border-white/10">
          <div class="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 font-mono text-xs font-bold text-white shadow-sm dark:bg-indigo-500">
            {{ count }}
          </div>
          <span class="text-sm font-bold tracking-wider text-slate-700 dark:text-slate-200">已选中题目</span>
        </div>

        <div class="flex items-center gap-4">
          <button
            @click="emit('export')"
            class="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 text-sm font-bold text-white shadow-sm transition-all hover:bg-blue-700 hover:shadow-blue-500/20 active:scale-95 dark:bg-indigo-600 dark:hover:bg-indigo-500"
          >
            <i class="fa-solid fa-file-export text-sm"></i>
            生成复习卷
          </button>

          <button
            @click="emit('clear')"
            class="inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-slate-200/60 bg-white/60 px-4 text-sm font-bold text-slate-600 transition-all hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-400 dark:hover:border-rose-500/30 dark:hover:bg-rose-500/10 dark:hover:text-rose-400"
          >
            清除
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>
