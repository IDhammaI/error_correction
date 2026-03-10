<script setup>
defineProps({
  step: { type: Number, default: 1 },
})

const labels = ['上传文件', 'OCR解析', '分割题目', '预览导出']
const descs = ['选择 PDF 或图片', '结构化提取题干', 'AI 识别并拆分', '勾选题目并导出']
</script>

<template>
  <div class="mb-10 px-2 sm:px-0">
    <ol class="relative flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between sm:gap-0">
      <li 
        v-for="n in 4" 
        :key="n" 
        class="relative flex items-center gap-4 sm:flex-1 sm:flex-col sm:gap-3"
      >
        <!-- 桌面端连接线 -->
        <div 
          v-if="n < 4" 
          class="hidden sm:block absolute left-[50%] top-6 w-full h-[2px] -translate-y-1/2 transition-colors duration-500 ease-in-out"
          :class="n < step ? 'bg-blue-600 dark:bg-blue-500' : 'bg-slate-200 dark:bg-slate-700'"
        ></div>
        
        <!-- 移动端连接线 -->
        <div 
          v-if="n < 4" 
          class="sm:hidden absolute left-6 top-14 bottom-[-1.5rem] w-[2px] -translate-x-1/2 transition-colors duration-500 ease-in-out"
          :class="n < step ? 'bg-blue-600 dark:bg-blue-500' : 'bg-slate-200 dark:bg-slate-700'"
        ></div>

        <!-- 步骤圆圈 -->
        <div 
          class="step-circle relative z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-[3px] ring-4 ring-white transition-all duration-300 dark:ring-slate-900"
          :class="
            n < step 
              ? 'border-blue-600 bg-blue-600 text-white dark:border-blue-500 dark:bg-blue-500 shadow-md shadow-blue-500/30' 
              : n === step 
                ? 'border-blue-600 bg-white text-blue-600 dark:border-blue-500 dark:bg-slate-900 dark:text-blue-400 shadow-md shadow-blue-500/20' 
                : 'border-slate-200 bg-slate-50 text-slate-400 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-500'
          "
        >
          <i v-if="n < step" class="fa-solid fa-check font-bold"></i>
          <span v-else class="text-sm font-bold tabular-nums">{{ n }}</span>
        </div>

        <!-- 文本描述 -->
        <div class="flex flex-col sm:items-center sm:text-center">
          <h3 
            class="text-base font-bold transition-colors duration-300"
            :class="n <= step ? 'text-slate-900 dark:text-slate-100' : 'text-slate-500 dark:text-slate-400'"
          >
            {{ labels[n - 1] }}
          </h3>
          <p class="mt-0.5 text-xs font-medium text-slate-500 dark:text-slate-400 sm:max-w-[120px]">
            {{ descs[n - 1] }}
          </p>
        </div>
      </li>
    </ol>
  </div>
</template>