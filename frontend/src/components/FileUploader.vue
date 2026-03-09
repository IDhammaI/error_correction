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
  <div>
    <!-- File chips (已上传/排队中的文件) -->
    <div v-if="pendingFiles.length" class="mb-6">
      <div class="flex flex-wrap items-center gap-3">
        <div
          v-for="item in pendingFiles"
          :key="item.key"
          class="file-chip inline-flex items-center gap-2.5 rounded-xl border border-slate-200/60 bg-white/60 backdrop-blur-md px-3 py-2 text-sm shadow-sm transition-all dark:border-slate-700/60 dark:bg-slate-800/60"
          :class="(uploadBusy || uploadReady) && 'file-chip--progress'"
          :style="{ '--p': String(fileProgress[item.key] ?? 0) }"
          :data-file-key="item.key"
        >
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-700">
            <i
              class="fa-solid text-lg"
              :class="
                item.file.name.toLowerCase().endsWith('.pdf')
                  ? 'fa-file-pdf text-rose-500 dark:text-rose-400'
                  : 'fa-file-image text-blue-500 dark:text-blue-400'
              "
            ></i>
          </div>
          <div class="flex flex-col">
            <span class="max-w-[200px] truncate font-medium text-slate-800 dark:text-slate-200" :title="item.file.name">
              {{ item.file.name }}
            </span>
            <span class="text-[11px] font-semibold tracking-wide text-slate-500 dark:text-slate-400">
              {{
                waitingKeys.has(item.key) && uploadBusy && (fileProgress[item.key] ?? 0) === 0
                  ? '等待中...'
                  : `${Math.round(fileProgress[item.key] ?? 0)}%`
              }}
            </span>
          </div>
          <button
            type="button"
            class="ml-1 inline-flex h-7 w-7 flex-none items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-rose-100 hover:text-rose-600 focus:outline-none focus:ring-4 focus:ring-rose-100 dark:hover:bg-rose-900/30 dark:hover:text-rose-400 dark:focus:ring-rose-900/50"
            :disabled="splitting || splitCompleted"
            aria-label="移除文件"
            @click.stop="() => emit('remove-file', item.key)"
          >
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
      </div>
    </div>
  
    <!-- Drop zone (拖拽上传区域) -->
    <div
      class="group relative overflow-hidden rounded-2xl border-2 border-dashed px-6 py-12 text-center transition-all duration-300"
      :class="
        uploadHover
          ? 'border-blue-400 bg-blue-50/50 dark:border-blue-500 dark:bg-blue-900/20'
          : 'border-slate-300 bg-slate-50/50 hover:border-blue-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900/30 dark:hover:border-slate-600 dark:hover:bg-slate-900/50'
      "
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
      <!-- 背景光晕点缀 (仅 Hover 或拖拽时亮起) -->
      <div
        class="absolute inset-0 -z-10 bg-gradient-to-b from-blue-50/0 to-blue-100/30 opacity-0 transition-opacity duration-300 dark:from-blue-900/0 dark:to-blue-900/10"
        :class="uploadHover && 'opacity-100'"
      ></div>
  
      <div
        class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-sm ring-1 ring-slate-200 transition-transform duration-300 group-hover:scale-110 group-hover:shadow-md dark:bg-slate-800 dark:ring-slate-700"
      >
        <i
          class="fa-solid fa-cloud-arrow-up text-3xl transition-colors duration-300"
          :class="uploadHover ? 'text-blue-500' : 'text-slate-400 dark:text-slate-300 group-hover:text-blue-500'"
        ></i>
      </div>
      <div class="text-lg font-semibold text-slate-900 dark:text-slate-100">
        点击此处 <span class="text-blue-600 dark:text-blue-400">选择文件</span> 或将文件拖拽到这里
      </div>
      <div class="mt-2 text-sm text-slate-500 dark:text-slate-400">
        支持 PDF、PNG、JPG、WEBP 等格式，可批量上传（单文件最大 50MB）
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