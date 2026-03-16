<script setup>
defineProps({
  step: { type: Number, default: 1 },
})

const labels = ['上传文件', 'OCR解析', '分割题目', '预览导出']
const descs = ['选择 PDF 或图片', '结构化提取题干', 'AI 识别并拆分', '勾选题目并导出']
</script>

<template>
  <div class="px-2 sm:px-0">
    <ol class="relative flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between sm:gap-0">
      <li 
        v-for="n in 4" 
        :key="n" 
        class="group relative flex items-center gap-4 sm:flex-1 sm:flex-col sm:gap-2"
      >
        <!-- 桌面端连接线 (优化定位，避免穿过圆圈) -->
        <div 
          v-if="n < 4" 
          class="hidden sm:block absolute left-[calc(50%+1.25rem)] top-5 w-[calc(100%-2.5rem)] h-[2px] -translate-y-1/2"
          :class="n < step ? 'bg-slate-400 dark:bg-slate-600' : 'bg-slate-200 dark:bg-slate-800'"
        ></div>
        
        <!-- 移动端连接线 -->
        <div 
          v-if="n < 4" 
          class="sm:hidden absolute left-5 top-12 bottom-[-1.5rem] w-[2px] -translate-x-1/2"
          :class="n < step ? 'bg-slate-400 dark:bg-slate-600' : 'bg-slate-200 dark:bg-slate-800'"
        ></div>

        <!-- 步骤圆圈 (白/灰黑玻璃风格) -->
        <div 
          class="step-circle relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border backdrop-blur-sm"
          :class="
            n < step
              ? 'border-transparent bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/30'
              : n === step
                ? 'border-slate-200 bg-white text-blue-600 shadow-xl shadow-blue-500/10 dark:border-white/20 dark:bg-white/10 dark:text-indigo-400'
                : 'border-slate-200 bg-white text-slate-400 dark:border-white/5 dark:bg-white/5 dark:text-slate-600'
          "
        >
          <Transition name="scale" mode="out-in">
            <i v-if="n < step" :key="'check-'+n" class="fa-solid fa-check text-[10px] font-black"></i>
            <span v-else :key="'num-'+n" class="text-xs font-black tabular-nums">{{ n }}</span>
          </Transition>
          
          <!-- 当前步骤的光晕 -->
          <div v-if="n === step" class="absolute -inset-1 animate-pulse rounded-xl bg-blue-500/10 blur-md dark:bg-indigo-500/20"></div>
        </div>

        <!-- 文本描述 (字号微调) -->
        <div class="flex flex-col sm:items-center sm:text-center">
          <h3 
            class="text-[11px] font-black tracking-tight"
            :class="n <= step ? 'text-slate-900 dark:text-white' : 'text-slate-500 dark:text-slate-600'"
          >
            {{ labels[n - 1] }}
          </h3>
          <p class="mt-0.5 text-[9px] font-bold leading-relaxed text-slate-500 dark:text-slate-500 sm:max-w-[100px]">
            {{ descs[n - 1] }}
          </p>
        </div>
      </li>
    </ol>
  </div>
</template>

<style scoped>
.scale-enter-active,
.scale-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.scale-enter-from {
  opacity: 0;
  transform: scale(0.5);
}

.scale-leave-to {
  opacity: 0;
  transform: scale(1.5);
}
</style>