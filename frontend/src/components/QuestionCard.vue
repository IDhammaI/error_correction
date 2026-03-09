<script setup>
import { isHtml, sanitizeHtml, formatOption } from '../utils.js'

defineProps({
  question: { type: Object, required: true },
  selected: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle', 'open-image'])
</script>

<template>
  <div
    class="question-card group relative overflow-hidden rounded-2xl border bg-white/80 p-5 shadow-sm backdrop-blur-sm transition-all duration-500 hover:-translate-y-1 hover:shadow-lg dark:bg-[#0A0A0F]/60"
    :class="
      selected 
        ? 'border-blue-500/50 shadow-[0_0_20px_rgba(59,130,246,0.1)] dark:border-indigo-500/50 dark:shadow-[0_0_30px_rgba(99,102,241,0.15)]' 
        : 'border-slate-200/60 dark:border-white/10 hover:border-blue-300/50 dark:hover:border-white/20'
    "
    @click="emit('toggle', question.question_id)"
  >
    <!-- 卡片背景环境光晕 (悬浮或选中时显示) -->
    <div 
      class="absolute inset-0 -z-10 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 transition-opacity duration-500 dark:from-indigo-500/10 dark:to-fuchsia-500/5"
      :class="(selected || 'group-hover:opacity-100') && 'opacity-100'"
    ></div>

    <!-- 顶部状态栏 -->
    <div class="mb-4 flex flex-wrap items-center gap-3 border-b border-slate-100/80 pb-3 dark:border-white/5">
      <button
        type="button"
        class="inline-flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 bg-white text-xs text-slate-400 shadow-sm transition-colors hover:bg-slate-50 hover:text-slate-700 dark:border-white/10 dark:bg-slate-900 dark:text-slate-500 dark:hover:bg-slate-800 dark:hover:text-slate-300"
        data-drag-handle="1"
        aria-label="拖动排序"
        @click.stop
      >
        <i class="fa-solid fa-grip-vertical"></i>
      </button>

      <span class="text-lg font-extrabold tracking-tight text-slate-900 dark:text-white">
        <span class="mr-1 text-sm font-mono text-blue-500 dark:text-indigo-400">#</span>{{ question.question_id }}
      </span>

      <span class="rounded-md border border-slate-200/80 bg-slate-50 px-2.5 py-1 text-xs font-bold tracking-wide text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300">
        {{ question.question_type }}
      </span>

      <!-- 科技感知识点标签 -->
      <template v-if="question.knowledge_tags && question.knowledge_tags.length">
        <span
          v-for="tag in question.knowledge_tags"
          :key="`${question.question_id}-tag-${tag}`"
          class="flex items-center gap-1 rounded-md border border-blue-500/20 bg-blue-500/10 px-2.5 py-1 text-xs font-medium text-blue-700 dark:border-cyan-500/20 dark:bg-cyan-500/10 dark:text-cyan-400"
        >
          <i class="fa-solid fa-tag text-[10px]"></i> {{ tag }}
        </span>
      </template>

      <!-- 右侧复选框 -->
      <label class="ml-auto inline-flex cursor-pointer items-center gap-2 rounded-lg py-1 pl-3 pr-1 text-sm font-medium text-slate-600 transition-colors hover:text-blue-600 dark:text-slate-400 dark:hover:text-indigo-300" @click.stop="emit('toggle', question.question_id)">
        <span :class="selected ? 'text-blue-600 dark:text-indigo-400' : ''">选择导出</span>
        <div 
          class="flex h-5 w-5 items-center justify-center rounded border transition-all"
          :class="selected ? 'border-blue-500 bg-blue-500 dark:border-indigo-500 dark:bg-indigo-500' : 'border-slate-300 bg-white dark:border-slate-600 dark:bg-slate-900'"
        >
          <i v-show="selected" class="fa-solid fa-check text-xs text-white"></i>
        </div>
      </label>
    </div>

    <!-- 题目内容区 -->
    <div class="question-content font-medium">
      <template v-if="question.content_blocks && question.content_blocks.length">
        <template v-for="(b, i) in question.content_blocks">
          <div v-if="b.block_type === 'text' && isHtml(b.content)" :key="`${question.question_id}-${i}`" v-html="sanitizeHtml(b.content)" class="question-text my-3 leading-loose text-slate-800 dark:text-slate-200"></div>
          <p v-else-if="b.block_type === 'text'" :key="`${question.question_id}-t-${i}`" class="my-3 whitespace-pre-line leading-loose text-slate-800 dark:text-slate-200">{{ b.content }}</p>
          
          <img
            v-else-if="b.block_type === 'image' && b.content"
            :key="`${question.question_id}-img-${i}`"
            :src="b.content"
            class="my-4 max-w-full cursor-zoom-in rounded-xl border border-slate-200/60 shadow-sm transition-transform hover:scale-[1.02] dark:border-white/10 dark:opacity-90 dark:hover:opacity-100"
            @click.stop="() => emit('open-image', b.content)"
            alt="题目图片"
          />
          <p v-else-if="b.block_type === 'image'" :key="`${question.question_id}-ip-${i}`" class="my-3 inline-flex items-center gap-2 rounded-lg bg-amber-50 px-3 py-1.5 text-sm font-bold text-amber-600 dark:bg-amber-500/10 dark:text-amber-400">
            <i class="fa-regular fa-image"></i> 图片资源待处理
          </p>
          <p v-else :key="`${question.question_id}-o-${i}`" class="my-3 whitespace-pre-line leading-loose text-slate-800 dark:text-slate-200">{{ b.content }}</p>
        </template>
      </template>
      <p v-else class="text-sm italic text-slate-400 dark:text-slate-600">（内容为空，请检查解析结果）</p>

      <!-- 选项区 -->
      <div v-if="question.options && question.options.length" class="mt-5 grid gap-2 border-t border-slate-100/50 pt-4 dark:border-white/5">
        <div
          v-for="(opt, idx) in question.options"
          :key="`${question.question_id}-opt-${idx}`"
          class="rounded-xl border border-slate-100 bg-slate-50/50 px-4 py-2.5 text-sm text-slate-800 transition-colors hover:border-slate-200 hover:bg-slate-100 dark:border-white/5 dark:bg-white/5 dark:text-slate-200 dark:hover:border-white/10 dark:hover:bg-white/10"
        >
          {{ formatOption(opt) }}
        </div>
      </div>
    </div>
  </div>
</template>