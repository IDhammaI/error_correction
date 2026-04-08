<script setup>
/**
 * OcrPreview.vue
 * OCR 结果预览 — 左侧原图 + 右侧识别文本
 */
defineProps({
  pages: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['confirm', 'retry'])
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- 加载中 -->
    <div v-if="loading" class="flex-1 flex flex-col items-center justify-center gap-4">
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-white/10 border-t-[rgb(129,115,223)]"></div>
      <p class="text-sm text-[#8a8f98]">正在执行 OCR 识别...</p>
    </div>

    <!-- 无数据 -->
    <div v-else-if="!pages.length" class="flex-1 flex items-center justify-center">
      <p class="text-sm text-[#62666d]">暂无 OCR 数据</p>
    </div>

    <!-- 预览 -->
    <template v-else>
      <!-- 统计 -->
      <div class="flex items-center justify-between mb-4">
        <span class="text-xs text-[#8a8f98]">共 {{ pages.length }} 页</span>
        <div class="flex items-center gap-2">
          <button @click="emit('retry')" class="inline-flex items-center gap-1.5 rounded-md border border-white/[0.08] bg-white/[0.02] px-3 py-1.5 text-xs font-medium text-[#d0d6e0] hover:bg-white/[0.05] transition-colors">
            <i class="fa-solid fa-arrows-rotate text-[10px]"></i> 重新识别
          </button>
          <button @click="emit('confirm')" class="inline-flex items-center gap-1.5 rounded-md brand-btn px-3 py-1.5 text-xs font-medium text-white">
            <i class="fa-solid fa-check text-[10px]"></i> 确认并分割
          </button>
        </div>
      </div>

      <!-- 页面列表 -->
      <div class="flex-1 overflow-y-auto custom-scrollbar space-y-4">
        <div
          v-for="page in pages"
          :key="page.page_index"
          class="flex gap-4 rounded-lg border border-white/[0.06] bg-white/[0.02] p-4"
        >
          <!-- 左侧：原图 -->
          <div class="w-1/2 shrink-0">
            <div class="mb-2 flex items-center gap-2">
              <span class="text-xs font-medium text-[#8a8f98]">第 {{ page.page_index + 1 }} 页</span>
              <span class="text-xs text-[#62666d]">{{ page.block_count }} 个文本块</span>
            </div>
            <div v-if="page.image_url" class="rounded-md border border-white/[0.06] overflow-hidden bg-white/[0.02]">
              <img :src="page.image_url" class="w-full object-contain max-h-[500px]" alt="原图" />
            </div>
            <div v-else class="flex h-48 items-center justify-center rounded-md border border-dashed border-white/[0.08] text-xs text-[#62666d]">
              图片不可用
            </div>
          </div>

          <!-- 右侧：OCR 文本 -->
          <div class="w-1/2">
            <div class="mb-2 text-xs font-medium text-[#8a8f98]">OCR 识别结果</div>
            <div class="rounded-md border border-white/[0.06] bg-white/[0.01] p-3 text-sm text-[#d0d6e0] leading-relaxed whitespace-pre-wrap max-h-[500px] overflow-y-auto custom-scrollbar">
              {{ page.text || '（无文本内容）' }}
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
