<script setup>
import { ref, watch, nextTick } from 'vue'
import { getQuestionSnippet, typesetMath } from '../utils.js'

const props = defineProps({
  question: { type: Object, required: true },
  selected: { type: Boolean, default: false },
  selectable: { type: Boolean, default: false },
  showStatus: { type: Boolean, default: false },
  maxTags: { type: Number, default: 0 },
})

const emit = defineEmits(['click', 'toggle-select'])

const optionsEl = ref(null)

const summary = () => getQuestionSnippet(props.question)

watch(() => props.question.options_json, async (val) => {
  if (val?.length && optionsEl.value) {
    await nextTick()
    typesetMath(optionsEl.value)
  }
}, { immediate: true, flush: 'post' })

const tags = () => {
  const all = props.question.knowledge_tags || []
  return props.maxTags ? all.slice(0, props.maxTags) : all
}

const statusClass = (status) => {
  if (status === '已掌握') return 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400 border border-emerald-200/50 dark:border-emerald-500/30'
  if (status === '复习中') return 'bg-amber-500/10 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400 border border-amber-200/50 dark:border-amber-500/30'
  return 'bg-rose-500/10 text-rose-600 dark:bg-rose-500/20 dark:text-rose-400 border border-rose-200/50 dark:border-rose-500/30'
}

const statusColor = (status) => {
  if (status === '已掌握') return 'text-emerald-500 dark:text-emerald-400'
  if (status === '复习中') return 'text-amber-500 dark:text-amber-400'
  return 'text-rose-500 dark:text-rose-400'
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
          <!-- 复习状态图标 -->
          <i v-if="showStatus" class="fa-solid text-sm" :class="[statusIcon(question.review_status), statusColor(question.review_status)]"></i>
          <span class="rounded-full bg-slate-100 px-2 py-1 text-xs font-bold uppercase tracking-widest text-slate-500 dark:bg-white/5 dark:text-slate-400">{{ question.question_type }}</span>
          <span v-if="question.subject" class="rounded-full bg-blue-50 px-2 py-1 text-xs font-bold text-blue-600 dark:bg-blue-500/10 dark:text-blue-300">{{ question.subject }}</span>
          <span v-for="tag in tags()" :key="tag" class="rounded-full border border-indigo-500/20 bg-indigo-500/5 px-2 py-1 text-xs font-bold text-indigo-600 dark:text-indigo-300">{{ tag }}</span>
        </div>

        <!-- 摘要 -->
        <p class="line-clamp-2 text-sm font-bold leading-relaxed text-slate-700 group-hover:text-slate-900 dark:text-slate-300 dark:group-hover:text-white">{{ summary() }}</p>

        <!-- 题目图片 -->
        <div v-if="question.content_json?.some(b => b.block_type === 'image' && b.content)" class="mt-3 flex flex-wrap gap-2">
          <img
            v-for="(b, i) in question.content_json.filter(b => b.block_type === 'image' && b.content)"
            :key="i"
            :src="b.content"
            class="max-h-32 rounded-xl border border-slate-100 object-contain dark:border-white/5"
            @click.stop
          />
        </div>

        <!-- 选择题选项 -->
        <div v-if="question.options_json?.length" ref="optionsEl" class="mt-3 grid grid-cols-2 gap-1.5">
          <div
            v-for="(opt, idx) in question.options_json"
            :key="idx"
            class="flex items-start gap-2 rounded-lg border border-slate-100 bg-slate-50/50 px-3 py-1.5 text-xs font-bold text-slate-600 dark:border-white/5 dark:bg-white/[0.02] dark:text-slate-400"
          >
            <span class="shrink-0 text-slate-400 dark:text-slate-500">{{ String.fromCharCode(65 + idx) }}.</span>
            <span class="line-clamp-1">{{ String(opt).replace(/^[A-Da-d][.、．]\s*/, '') }}</span>
          </div>
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
