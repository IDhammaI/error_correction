<script setup>
/**
 * QuestionCard.vue
 * 题目卡片（错题库列表项）
 */
import { ref, computed } from 'vue'
import BaseCard from '@/components/base/BaseCard.vue'
import { isHtml, sanitizeHtml, formatOption } from '@/utils.js'

const props = defineProps({
  question: { type: Object, required: true },
  selected: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle', 'open-image'])

// 兜底：image_refs 中有但 content_blocks 中未嵌入的图片
const extraImages = computed(() => {
  const refs = props.question.image_refs || []
  if (!refs.length) return []
  const blocks = props.question.content_blocks || []
  // 排除 image block 中已嵌入的
  const embedded = new Set(
    blocks.filter(b => b.block_type === 'image' && b.content).map(b => b.content)
  )
  // 排除 HTML 文本中已通过 <img> 引用的（如表格内嵌图片）
  const htmlContent = blocks.filter(b => b.block_type === 'text').map(b => b.content || '').join(' ')
  return refs.filter(r => {
    if (embedded.has(r)) return false
    // 提取文件名部分匹配，因为 HTML 中可能用 imgs/ 而 refs 用 /images/
    const filename = r.split('/').pop()
    if (filename && htmlContent.includes(filename)) return false
    return true
  })
})

// 图片与选项配对：优先使用 Agent 输出的 option_images，降级到按数量匹配
const optionImages = computed(() => {
  const opts = props.question.options || []
  if (!opts.length) return null
  // 优先使用 Agent 直接输出的 option_images
  const agentImages = props.question.option_images
  if (agentImages?.length === opts.length) return agentImages
  // 降级：extraImages 数量匹配时按索引配对
  if (extraImages.value.length >= opts.length) return extraImages.value
  return null
})

// 本地答案编辑状态（工作台内存保存，入库时随 question 对象一同传递）
const editingAnswer = ref(false)
const editingUserAnswer = ref(false)
const answerDraft = ref('')
const userAnswerDraft = ref('')

const startEditAnswer = () => {
  answerDraft.value = props.question.answer || ''
  editingAnswer.value = true
}
const saveAnswer = () => {
  props.question.answer = answerDraft.value.trim() || undefined
  editingAnswer.value = false
}
const cancelAnswer = () => { editingAnswer.value = false }

const startEditUserAnswer = () => {
  userAnswerDraft.value = props.question.user_answer || ''
  editingUserAnswer.value = true
}
const saveUserAnswer = () => {
  props.question.user_answer = userAnswerDraft.value.trim() || undefined
  editingUserAnswer.value = false
}
const cancelUserAnswer = () => { editingUserAnswer.value = false }
</script>

<template>
  <BaseCard class="question-card group relative overflow-hidden transition-shadow hover:shadow-md cursor-pointer"
    padding="p-6" rounded="rounded-2xl" :class="selected
      ? 'accent-border shadow-[rgb(var(--accent-rgb)/0.1)] dark:shadow-[rgb(var(--accent-rgb)/0.2)]'
      : 'hover:border-[rgb(var(--accent-rgb)/0.4)] dark:hover:!border-white/15'
      " @click="emit('toggle', question.uid)">
    <!-- 选中态背景 -->
    <div v-if="selected"
      class="absolute inset-0 -z-10 bg-gradient-to-br from-[rgb(var(--accent-rgb)/0.03)] to-[rgb(var(--accent-strong-rgb)/0.03)] dark:from-[rgb(var(--accent-rgb)/0.05)] dark:to-[rgb(var(--accent-strong-rgb)/0.05)]">
    </div>

    <!-- 大题标签 -->
    <div v-if="question.section_title"
      class="mb-4 flex items-center gap-2 border-l-2 border-[rgb(var(--accent-rgb)/0.6)] pl-3 dark:border-[rgb(var(--accent-rgb)/0.5)]">
      <i class="fa-solid fa-layer-group text-xs accent-text"></i>
      <span class="text-xs font-bold tracking-wide text-gray-500 dark:text-gray-400">{{ question.section_title }}</span>
    </div>

    <!-- 顶部状态栏 -->
    <div class="mb-6 flex items-start gap-4">
      <!-- 题型与标签 -->
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-xs font-bold tracking-widest text-gray-400 dark:text-gray-500">AI 识别标签</span>
        <span
          class="rounded-full bg-gray-100 px-3 py-1 text-xs font-bold uppercase tracking-widest text-gray-500 dark:bg-white/5 dark:text-gray-400">
          {{ question.question_type }}
        </span>
        <span v-for="tag in question.knowledge_tags" :key="tag"
          class="rounded-full accent-bg-soft px-3 py-1 text-xs font-bold accent-text">
          {{ tag }}
        </span>
      </div>

      <!-- 右侧复选框 -->
      <div class="ml-auto flex items-center gap-4">
        <span class="text-xs font-bold uppercase tracking-widest text-gray-400"
          :class="selected && 'accent-text'">
          {{ selected ? '已选择' : '未选择' }}
        </span>
        <div class="flex h-5 w-5 items-center justify-center rounded-lg border-2 transition-all"
          :class="selected ? 'accent-border accent-bg text-white shadow-sm' : 'border-gray-200 bg-white dark:border-white/5 dark:bg-[#15151e]'">
          <i v-if="selected" class="fa-solid fa-check text-[10px]"></i>
        </div>
      </div>
    </div>

    <!-- 题目内容区 -->
    <div class="question-content relative">
      <template v-if="question.content_blocks?.length">
        <div v-for="(b, i) in question.content_blocks" :key="i">
          <div v-if="b.block_type === 'text' && isHtml(b.content)"
            class="my-4 text-base font-medium leading-relaxed text-gray-800 dark:text-[#d0d6e0]"
            v-html="sanitizeHtml(b.content)"></div>
          <p v-else-if="b.block_type === 'text'"
            class="my-4 text-base font-medium leading-relaxed text-gray-800 dark:text-[#d0d6e0] whitespace-pre-wrap">{{
              b.content }}</p>
          <img v-else-if="b.block_type === 'image' && b.content" :src="b.content"
            class="my-6 max-h-[400px] cursor-zoom-in rounded-2xl border border-gray-100 dark:border-white/5 shadow-sm transition-transform hover:scale-[1.01]"
            @click.stop="() => emit('open-image', b.content)" />
        </div>
      </template>

      <!-- 兜底渲染：无选项配对时独立展示 -->
      <div v-if="extraImages.length && !optionImages" class="my-4 flex flex-wrap gap-2">
        <img v-for="(src, i) in extraImages" :key="'extra-' + i" :src="src"
          class="max-h-[200px] cursor-zoom-in rounded-2xl border border-gray-100 dark:border-white/5 object-contain shadow-sm transition-transform hover:scale-[1.01]"
          @click.stop="() => emit('open-image', src)" />
      </div>

      <!-- 选项 -->
      <div v-if="question.options?.length" class="mt-8 grid gap-3 sm:grid-cols-2">
        <div v-for="(opt, idx) in question.options" :key="idx"
          class="flex items-center gap-3 rounded-xl border border-gray-100 bg-gray-50/50 p-4 text-[13px] font-bold text-gray-700 hover:bg-gray-100/80 dark:border-white/5 dark:bg-white/5 dark:text-[#d0d6e0] dark:hover:bg-white/10 transition-colors">
          <span
            class="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-white text-[10px] shadow-sm dark:bg-[#15151e]">{{
              formatOption(opt)[0] }}</span>
          <span class="flex-1">{{ formatOption(opt).slice(2) }}</span>
          <img v-if="optionImages?.[idx]" :src="optionImages[idx]"
            class="max-h-[100px] max-w-[160px] shrink-0 cursor-zoom-in rounded-lg border border-gray-100 object-contain dark:border-white/5"
            @click.stop="() => emit('open-image', optionImages[idx])" />
        </div>
      </div>
    </div>

  </BaseCard>
</template>

<style scoped>
.question-content :deep(table) {
  @apply my-4 w-full rounded-xl border border-slate-200 bg-white/50 text-sm overflow-hidden dark:bg-white/[0.02] dark:border-white/10;
  display: block;
  overflow-x: auto;
  white-space: nowrap;
}
.question-content :deep(th) {
  @apply bg-slate-100 p-3 text-left font-black dark:bg-white/5 dark:text-slate-300;
}
.question-content :deep(td) {
  @apply border-t border-slate-100 p-3 dark:border-white/10 dark:text-slate-300;
}

.question-content :deep(ul) {
  @apply list-disc pl-5 my-2;
}

.question-content :deep(ol) {
  @apply list-decimal pl-5 my-2;
}

.question-content :deep(a) {
  @apply text-blue-600 hover:underline dark:text-blue-400;
}

.question-content :deep(img) {
  @apply inline-block max-h-[200px] object-contain rounded-lg border border-slate-200 dark:border-white/10;
}
</style>
