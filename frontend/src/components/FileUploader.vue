<script setup>
import { ref } from 'vue'

const props = defineProps({
  pendingFiles: { type: Array, default: () => [] },
  fileProgress: { type: Object, default: () => ({}) },
  waitingKeys: { type: Object, default: () => new Set() },
  uploadBusy: { type: Boolean, default: false },
  uploadReady: { type: Boolean, default: false },
  splitting: { type: Boolean, default: false },
  splitCompleted: { type: Boolean, default: false },
  expand: { type: Boolean, default: false },
})

const emit = defineEmits(['upload', 'remove-file'])

const fileInputEl = ref(null)
const uploadHover = ref(false)

const onFileInput = (e) => {
  emit('upload', e.target.files)
  e.target.value = ''
}

const onDrop = (e) => {
  e.preventDefault()
  uploadHover.value = false
  emit('upload', e.dataTransfer.files)
}
</script>

<template>
  <div :class="{ 'flex flex-col flex-1': expand }">
    <!-- Drop zone (拖拽上传区域) -->
    <div
      class="group relative flex flex-col items-center justify-center overflow-hidden rounded-[2rem] border backdrop-blur-md"
      :class="[
        uploadHover
          ? 'border-blue-500/50 bg-slate-900/10 shadow-2xl shadow-blue-500/20 dark:border-indigo-500/50 dark:bg-white/10'
          : 'border-slate-900/10 bg-slate-900/[0.05] shadow-[0_8px_30px_rgba(0,0,0,0.06)] hover:border-blue-200 hover:bg-slate-900/10 dark:border-white/5 dark:bg-white/5 dark:shadow-none dark:hover:border-indigo-500/20 dark:hover:bg-white/10',
        expand ? 'flex-1 py-12 min-h-[280px]' : 'py-10'
      ]"
      @dragenter.prevent="uploadHover = true"
      @dragover.prevent="uploadHover = true"
      @dragleave.prevent="uploadHover = false"
      @drop="onDrop"
      @click="() => fileInputEl?.click()"
      @keydown.enter.prevent="() => fileInputEl?.click()"
      @keydown.space.prevent="() => fileInputEl?.click()"
      role="button"
      tabindex="0"
    >
      <!-- 动态装饰 -->
      <div class="pointer-events-none absolute inset-0 -z-10">
        <div class="absolute -left-10 -top-10 h-24 w-24 rounded-full bg-blue-500/5 blur-2xl transition-opacity group-hover:opacity-100"></div>
        <div class="absolute -right-10 -bottom-10 h-24 w-24 rounded-full bg-indigo-500/5 blur-2xl transition-opacity group-hover:opacity-100"></div>
      </div>

      <!-- Center content (主上传引导) -->
      <div class="flex flex-1 flex-col items-center justify-center">
        <div class="relative mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border border-slate-900/10 bg-slate-900/5 shadow-xl shadow-slate-200/50 backdrop-blur-md transition-transform duration-500 group-hover:scale-110 dark:border-white/10 dark:bg-white/5 dark:shadow-none">
          <i class="fa-solid fa-cloud-arrow-up text-2xl text-blue-600 dark:text-indigo-400"></i>
        </div>

        <div class="max-w-xs">
          <h4 class="text-sm font-black tracking-tight text-slate-900 dark:text-white">
            点击 <span class="text-blue-600 dark:text-indigo-400">选择文件</span> 或拖拽至此
          </h4>
          <div class="mt-4 flex flex-wrap justify-center gap-1.5">
            <span v-for="fmt in ['PDF', 'PNG', 'JPG']" :key="fmt" class="rounded-lg border border-slate-900/10 bg-slate-900/5 px-3 py-1 text-[9px] font-black tracking-wider text-slate-500 shadow-sm backdrop-blur-sm dark:border-white/5 dark:bg-white/5 dark:text-slate-400">
              {{ fmt }}
            </span>
          </div>
        </div>
      </div>

      <input
        ref="fileInputEl"
        type="file"
        class="hidden"
        accept=".pdf,.png,.jpg,.jpeg,.bmp,.tiff,.webp"
        multiple
        @change="onFileInput"
      />
    </div>
  </div>
</template>