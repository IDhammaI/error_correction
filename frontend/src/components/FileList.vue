<script setup>
defineProps({
  pendingFiles: { type: Array, default: () => [] },
  fileProgress: { type: Object, default: () => ({}) },
  waitingKeys: { type: Object, default: () => new Set() },
  uploadBusy: { type: Boolean, default: false },
  uploadReady: { type: Boolean, default: false },
  splitting: { type: Boolean, default: false },
  splitCompleted: { type: Boolean, default: false },
})
const emit = defineEmits(['remove-file'])
</script>

<template>
  <Transition
    enter-active-class="transition-all duration-500 ease-out"
    enter-from-class="opacity-0 -translate-y-4 max-h-0"
    enter-to-class="opacity-100 translate-y-0 max-h-40"
    leave-active-class="transition-all duration-300 ease-in"
    leave-from-class="opacity-100 translate-y-0 max-h-40"
    leave-to-class="opacity-0 -translate-y-4 max-h-0"
  >
    <div v-if="pendingFiles.length" class="relative z-20 w-full overflow-hidden shrink-0">
      <div class="flex flex-wrap items-center gap-3">
        <div
          v-for="item in pendingFiles"
          :key="item.key"
          class="file-chip relative flex items-center gap-3 overflow-hidden rounded-xl border border-slate-900/10 bg-slate-900/[0.04] p-2.5 shadow-sm backdrop-blur-sm dark:border-white/5 dark:bg-white/5"
          :class="(uploadBusy || uploadReady) && 'file-chip--progress'"
        >
          <!-- 进度条背景 -->
          <div 
            class="absolute inset-0 -z-10 bg-blue-500/10 transition-[width] duration-500 ease-out dark:bg-indigo-500/20"
            :style="{ width: `${fileProgress[item.key] ?? 0}%` }"
          ></div>

          <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-slate-900/5 bg-white/50 shadow-sm dark:bg-white/10">
            <i
              class="fa-solid text-base"
              :class="
                item.file.name.toLowerCase().endsWith('.pdf')
                  ? 'fa-file-pdf text-rose-500'
                  : 'fa-file-image text-blue-500'
              "
            ></i>
          </div>
          <div class="flex flex-col min-w-0 pr-6 text-left">
            <span class="truncate text-xs font-bold text-slate-800 dark:text-slate-200" :title="item.file.name">
              {{ item.file.name }}
            </span>
            <div class="flex items-center gap-2">
              <span class="text-[9px] font-black uppercase tracking-wider text-slate-400">
                {{ waitingKeys.has(item.key) && uploadBusy ? '等待' : `${Math.round(fileProgress[item.key] ?? 0)}%` }}
              </span>
            </div>
          </div>
          
          <button
            type="button"
            class="absolute right-1 top-1 flex h-5 w-5 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-rose-50 hover:text-rose-500 dark:hover:bg-rose-500/10"
            :disabled="splitting || splitCompleted"
            @click.stop="() => emit('remove-file', item.key)"
          >
            <i class="fa-solid fa-xmark text-[10px]"></i>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>
