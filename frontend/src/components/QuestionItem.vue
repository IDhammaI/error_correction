<script setup>
import { getQuestionSnippet } from '../utils.js'

const props = defineProps({
  question: { type: Object, required: true },
  selected: { type: Boolean, default: false },
  selectable: { type: Boolean, default: false },
  showStatus: { type: Boolean, default: false },
  maxTags: { type: Number, default: 0 },
})

const emit = defineEmits(['click', 'toggle-select'])

const summary = () => getQuestionSnippet(props.question)

const tags = () => {
  const all = props.question.knowledge_tags || []
  return props.maxTags ? all.slice(0, props.maxTags) : all
}

const statusClass = (status) => {
  if (status === '已掌握') return 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400 border border-emerald-200/50 dark:border-emerald-500/30'
  if (status === '复习中') return 'bg-indigo-500/10 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-400 border border-indigo-200/50 dark:border-indigo-500/30'
  return 'bg-slate-500/10 text-slate-600 dark:bg-slate-500/20 dark:text-slate-400 border border-slate-200/50 dark:border-slate-500/30'
}

const statusIcon = (status) => {
  if (status === '已掌握') return 'fa-circle-check'
  if (status === '复习中') return 'fa-spinner'
  return 'fa-clock'
}
</script>

<template>
  <div
    @click="selectable ? emit('toggle-select', question.id) : emit('click', question)"
    class="group cursor-pointer rounded-2xl border border-slate-200/60 bg-white/70 p-6 shadow-sm backdrop-blur-xl transition-all hover:shadow-md dark:border-white/10 dark:bg-white/[0.03]"
    :class="{ 'ring-2 ring-indigo-500/50 border-indigo-300 dark:border-indigo-500/40': selected }"
  >
    <div class="flex items-start gap-4">
      <!-- 选择复选框 -->
      <div v-if="selectable" class="flex shrink-0 items-center pt-1" @click.stop="emit('toggle-select', question.id)">
        <div class="flex h-5 w-5 items-center justify-center rounded-lg border-2 transition-all"
          :class="selected ? 'border-indigo-500 bg-indigo-500 text-white' : 'border-slate-300 dark:border-slate-600'">
          <i v-if="selected" class="fa-solid fa-check text-xs"></i>
        </div>
      </div>

      <div class="min-w-0 flex-1">
        <!-- 标签行 -->
        <div class="mb-2 flex flex-wrap items-center gap-2">
          <span v-if="question.subject" class="rounded-full bg-blue-50 px-2 py-1 text-xs font-bold text-blue-600 dark:bg-blue-500/10 dark:text-blue-300">{{ question.subject }}</span>
          <span class="rounded-full bg-slate-100 px-2 py-1 text-xs font-bold uppercase tracking-widest text-slate-500 dark:bg-white/5 dark:text-slate-400">{{ question.question_type }}</span>
          <span v-for="tag in tags()" :key="tag" class="rounded-full border border-indigo-500/20 bg-indigo-500/5 px-2 py-1 text-xs font-bold text-indigo-600 dark:text-indigo-300">{{ tag }}</span>
          <!-- 复习状态 -->
          <span v-if="showStatus" class="ml-auto flex items-center gap-1 rounded-full px-2 py-1 text-xs font-bold" :class="statusClass(question.review_status)">
            <i class="fa-solid" :class="statusIcon(question.review_status)"></i>
            {{ question.review_status || '待复习' }}
          </span>
          <span v-else class="ml-auto text-xs font-bold text-slate-400">{{ question.created_at ? new Date(question.created_at).toLocaleDateString() : '' }}</span>
        </div>

        <!-- 摘要 -->
        <p class="line-clamp-2 text-sm font-bold leading-relaxed text-slate-700 group-hover:text-slate-900 dark:text-slate-300 dark:group-hover:text-white">{{ summary() }}</p>

        <!-- 底部信息（答案/笔记状态） -->
        <div class="mt-2 flex flex-wrap items-center gap-2 text-xs" @click.stop>
          <span v-if="question.answer" class="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-1 font-bold text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400">
            <i class="fa-solid fa-circle-check"></i>有答案
          </span>
          <span v-if="question.user_answer" class="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-1 font-bold text-blue-600 dark:bg-blue-500/10 dark:text-blue-400">
            <i class="fa-solid fa-pen-to-square"></i>已记笔记
          </span>
          <span v-if="showStatus" class="ml-auto text-xs font-bold text-slate-400">{{ question.created_at ? new Date(question.created_at).toLocaleDateString() : '' }}</span>
        </div>

        <!-- 扩展插槽（内联编辑等） -->
        <slot name="extra" :question="question" />
      </div>

      <!-- 右侧操作区插槽 -->
      <div v-if="$slots.actions" class="flex shrink-0 gap-2" @click.stop>
        <slot name="actions" :question="question" />
      </div>
    </div>
  </div>
</template>
