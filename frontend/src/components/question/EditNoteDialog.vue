<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { typesetMath, isHtml, sanitizeHtml } from '@/utils.js'

const props = defineProps({
  open: { type: Boolean, default: false },
  field: { type: String, default: 'answer' },
  question: { type: Object, default: null },
  value: { type: String, default: '' },
  valueAnswer: { type: String, default: '' },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'save'])

const draft = ref('')
const draftAnswer = ref('')
const questionContentRef = ref(null)
const previewMode = ref(false)
const htmlError = ref('')

// 简单的 HTML 结构验证
const validateHtml = (html) => {
  if (!html) return ''
  const stack = []
  const tags = html.match(/<\/?([a-zA-Z0-9]+)[^>]*>/g) || []
  const voidTags = ['img', 'br', 'hr', 'input', 'meta', 'link']

  for (const tagStr of tags) {
    const isClosing = tagStr.startsWith('</')
    const tagNameMatch = tagStr.match(/<\/?([a-zA-Z0-9]+)/)
    if (!tagNameMatch) continue
    const tagName = tagNameMatch[1].toLowerCase()

    if (voidTags.includes(tagName)) continue

    if (!isClosing) {
      stack.push(tagName)
    } else {
      if (stack.length === 0) return `错误: 多余的闭合标签 </${tagName}>`
      const last = stack.pop()
      if (last !== tagName) return `错误: 标签不匹配，期望 </${last}>，实际找到 </${tagName}>`
    }
  }
  if (stack.length > 0) return `错误: 缺少闭合标签 </${stack[stack.length - 1]}>`
  return ''
}

const onDraftChange = () => {
  if (props.field === 'question') {
    htmlError.value = validateHtml(draft.value)
    if (previewMode.value) {
      nextTick(() => typesetMath(questionContentRef.value))
    }
  }
}

watch(() => props.open, async (v) => {
  if (v) {
    draft.value = props.value || ''
    draftAnswer.value = props.valueAnswer || ''
    htmlError.value = validateHtml(draft.value)
    if (props.field === 'question') {
      previewMode.value = true // 默认显示预览
      await nextTick()
      typesetMath(questionContentRef.value)
    }
  }
})

const onSave = () => {
  if (htmlError.value) {
    alert(htmlError.value)
    return
  }
  if (props.field === 'question') {
    emit('save', { content: draft.value, answer: draftAnswer.value })
  } else {
    emit('save', draft.value)
  }
}

const config = () => {
  if (props.field === 'answer') {
    return {
      title: '正确答案',
      icon: 'fa-circle-check',
      iconBg: 'bg-emerald-50 dark:bg-emerald-500/10',
      iconCls: 'text-emerald-600 dark:text-emerald-400',
      btnCls: 'bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-600',
    }
  }
  if (props.field === 'question') {
    return {
      title: '编辑题目',
      icon: 'fa-pen-to-square',
      iconBg: 'bg-indigo-50 dark:bg-indigo-500/10',
      iconCls: 'text-indigo-600 dark:text-indigo-400',
      btnCls: 'bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600',
    }
  }
  return {
    title: '我的笔记',
    icon: 'fa-pen-to-square',
    iconBg: 'bg-blue-50 dark:bg-blue-500/10',
    iconCls: 'text-blue-600 dark:text-blue-400',
    btnCls: 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600',
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog-overlay" appear>
      <div v-if="open" class="dialog-backdrop fixed inset-0 z-[100] bg-black/40 md:left-64" @click="emit('close')">
      </div>
    </Transition>

    <Transition name="dialog-content" appear>
      <div v-if="open" class="fixed inset-0 z-[101] flex items-center justify-center p-4 md:left-64"
        @click.self="emit('close')">
        <div
          class="relative w-full rounded-2xl border border-slate-200/60 bg-white shadow-2xl dark:border-white/10 dark:bg-[#0f0f17]"
          :class="field === 'question' ? 'max-w-2xl' : 'max-w-xl'">
          <div class="flex items-center justify-between border-b border-slate-100 px-6 py-4 dark:border-white/5">
            <div class="flex items-center gap-3">
              <div class="flex h-9 w-9 items-center justify-center rounded-xl" :class="config().iconBg">
                <i class="fa-solid text-base" :class="[config().icon, config().iconCls]"></i>
              </div>
              <h3 class="text-base font-bold text-slate-800 dark:text-slate-200">{{ config().title }}</h3>
            </div>
            <button @click="emit('close')"
              class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-slate-300">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>

          <div v-if="field === 'question'" class="max-h-[72vh] overflow-y-auto px-6 py-4 space-y-4">
            <div>
              <div class="flex items-center justify-between mb-2">
                <p class="text-xs font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500">题目内容</p>
                <div class="flex items-center gap-3 rounded-lg bg-slate-100 p-1 dark:bg-white/5">
                  <button @click="previewMode = false"
                    :class="!previewMode ? 'bg-white text-indigo-600 shadow-sm dark:bg-indigo-500/20 dark:text-indigo-300' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'"
                    class="rounded-md px-3 py-1 text-[10px] font-black uppercase tracking-wider transition-all">编辑</button>
                  <button @click="previewMode = true; onDraftChange()"
                    :class="previewMode ? 'bg-white text-indigo-600 shadow-sm dark:bg-indigo-500/20 dark:text-indigo-300' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'"
                    class="rounded-md px-3 py-1 text-[10px] font-black uppercase tracking-wider transition-all">预览</button>
                </div>
              </div>

              <!-- 编辑区 -->
              <div v-show="!previewMode">
                <textarea v-model="draft" @input="onDraftChange" rows="6"
                  class="w-full resize-none rounded-xl border border-slate-200/60 bg-slate-50/60 px-4 py-3 text-sm font-mono leading-relaxed text-slate-700 outline-none transition-all focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200/60 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-200 dark:focus:border-white/20 dark:focus:ring-white/5"
                  placeholder="输入题目内容，支持富文本 HTML 标签..."></textarea>
                <p v-if="htmlError" class="mt-2 text-xs font-medium text-rose-500 flex items-center gap-1"><i
                    class="fa-solid fa-triangle-exclamation"></i> {{ htmlError }}</p>
              </div>

              <!-- 预览区 -->
              <div v-show="previewMode" ref="questionContentRef"
                class="rounded-xl border border-slate-200/60 bg-slate-50/60 p-4 dark:border-white/10 dark:bg-white/[0.03] min-h-[100px] html-preview-content">
                <div v-if="isHtml(draft)" v-html="sanitizeHtml(draft)"
                  class="text-sm font-bold leading-relaxed text-slate-700 dark:text-slate-200 overflow-x-auto w-full">
                </div>
                <p v-else
                  class="text-sm font-bold leading-relaxed text-slate-700 dark:text-slate-200 whitespace-pre-wrap">{{
                    draft }}</p>

                <div v-if="question?.content_json?.some(b => b.block_type === 'image' && b.content)"
                  class="mt-3 flex flex-wrap gap-2">
                  <img v-for="(b, i) in question.content_json.filter(b => b.block_type === 'image' && b.content)"
                    :key="i" :src="b.content"
                    class="max-h-40 rounded-xl border border-slate-100 object-contain dark:border-white/5" />
                </div>
                <div v-if="question?.options_json?.length" class="mt-3 grid grid-cols-2 gap-1.5">
                  <div v-for="(opt, idx) in question.options_json" :key="idx"
                    class="flex items-start gap-2 rounded-lg border border-slate-100 bg-slate-50/50 px-3 py-1.5 text-xs font-bold text-slate-600 dark:border-white/5 dark:bg-white/[0.02] dark:text-slate-400">
                    <span class="shrink-0 text-slate-400">{{ String.fromCharCode(65 + idx) }}.</span>
                    <span>{{ String(opt).replace(/^[A-Da-d][.、．]\s*/, '') }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div>
              <p class="mb-2 text-xs font-bold uppercase tracking-widest text-emerald-600 dark:text-emerald-400">正确答案
              </p>
              <textarea v-model="draftAnswer" rows="5"
                class="w-full resize-none rounded-xl border border-slate-200/60 bg-slate-50/60 px-4 py-3 text-sm font-medium leading-relaxed text-slate-700 outline-none transition-all focus:border-slate-300 focus:ring-2 focus:ring-slate-200/60 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-200 dark:focus:border-white/20 dark:focus:ring-white/5"
                placeholder="输入正确答案..."></textarea>
            </div>
          </div>

          <div v-else class="px-6 py-4">
            <textarea v-model="draft" rows="7"
              class="w-full resize-none rounded-xl border border-slate-200/60 bg-slate-50/60 px-4 py-3 text-sm font-medium leading-relaxed text-slate-700 outline-none transition-all focus:border-slate-300 focus:ring-2 focus:ring-slate-200/60 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-200 dark:focus:border-white/20 dark:focus:ring-white/5"
              :placeholder="field === 'answer' ? '输入正确答案...' : '记录你的笔记...'"></textarea>
          </div>

          <div class="flex justify-end gap-2 border-t border-slate-100 px-6 py-4 dark:border-white/5">
            <button @click="emit('close')"
              class="inline-flex h-10 items-center justify-center rounded-xl px-4 text-sm font-bold text-slate-500 transition-all hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300">
              取消
            </button>
            <button @click="onSave" :disabled="saving"
              class="inline-flex h-10 items-center justify-center gap-2 rounded-xl px-6 text-sm font-bold text-white transition-all disabled:cursor-not-allowed disabled:opacity-50"
              :class="config().btnCls">
              <i v-if="saving" class="fa-solid fa-spinner animate-spin"></i>
              {{ saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-backdrop {
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.dialog-overlay-enter-active,
.dialog-overlay-leave-active {
  transition:
    opacity 0.22s ease,
    backdrop-filter 0.22s ease,
    -webkit-backdrop-filter 0.22s ease;
}

.dialog-overlay-enter-from,
.dialog-overlay-leave-to {
  opacity: 0;
  backdrop-filter: blur(0px);
  -webkit-backdrop-filter: blur(0px);
}

.dialog-content-enter-active,
.dialog-content-leave-active {
  transition: opacity 0.22s ease, transform 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

.dialog-content-enter-from,
.dialog-content-leave-to {
  opacity: 0;
  transform: scale(0.96) translateY(8px);
}

.html-preview-content :deep(table) {
  @apply my-4 w-full rounded-xl border border-slate-200 bg-white/50 text-sm overflow-hidden;
  display: block;
  overflow-x: auto;
  white-space: nowrap;
}

.html-preview-content :deep(th) {
  @apply bg-slate-100 p-3 text-left font-black dark:bg-white/5;
}

.html-preview-content :deep(td) {
  @apply border-t border-slate-100 p-3 dark:border-white/5;
}

.html-preview-content :deep(ul) {
  @apply list-disc pl-5 my-2;
}

.html-preview-content :deep(ol) {
  @apply list-decimal pl-5 my-2;
}

.html-preview-content :deep(img) {
  @apply max-w-full rounded-lg border border-slate-200 dark:border-white/10;
}

.html-preview-content :deep(a) {
  @apply text-blue-600 hover:underline dark:text-blue-400;
}
</style>
