<script setup>
import { ref } from 'vue'
import { isHtml, sanitizeHtml, formatOption } from '../utils.js'

const props = defineProps({
  question: { type: Object, required: true },
  selected: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle', 'open-image'])

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
  <div
    class="question-card group relative overflow-hidden rounded-[2rem] border bg-white p-6 transition-all duration-500 hover:shadow-[0_20px_40px_rgba(0,0,0,0.04)] dark:bg-slate-900/40"
    :class="
      selected
        ? 'border-blue-500/50 shadow-[0_0_30px_rgba(59,130,246,0.1)] dark:border-indigo-500/50 dark:shadow-[0_0_40px_rgba(99,102,241,0.2)]'
        : 'border-slate-100 dark:border-white/5 hover:border-blue-200 dark:hover:border-white/10'
    "
    @click="emit('toggle', question.question_id)"
  >
    <!-- 选中态背景 -->
    <div
      v-if="selected"
      class="absolute inset-0 -z-10 bg-gradient-to-br from-blue-500/[0.03] to-indigo-500/[0.03] dark:from-indigo-500/[0.05] dark:to-purple-500/[0.05]"
    ></div>

    <!-- 顶部状态栏 -->
    <div class="mb-6 flex flex-wrap items-center gap-3">
      <div
        class="flex h-8 w-8 cursor-grab items-center justify-center rounded-xl border border-slate-100 bg-slate-50 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 active:cursor-grabbing dark:border-white/5 dark:bg-slate-800 dark:text-slate-500"
        data-drag-handle="1"
        @click.stop
      >
        <i class="fa-solid fa-grip-vertical text-xs"></i>
      </div>

      <div class="flex items-center gap-2 rounded-xl border border-slate-100 bg-slate-50/50 px-3 py-1.5 dark:border-white/5 dark:bg-white/5">
        <span class="text-xs font-black text-blue-600 dark:text-indigo-400">#{{ question.question_id }}</span>
        <div class="h-3 w-px bg-slate-200 dark:bg-white/10"></div>
        <span class="text-[11px] font-bold text-slate-600 dark:text-slate-300">{{ question.question_type }}</span>
      </div>

      <!-- 知识点标签 -->
      <div v-if="question.knowledge_tags?.length" class="flex flex-wrap items-center gap-2">
        <span
          v-for="tag in question.knowledge_tags"
          :key="tag"
          class="rounded-lg bg-blue-50 px-2.5 py-1.5 text-[10px] font-black tracking-wider text-blue-600 dark:bg-indigo-500/10 dark:text-indigo-400"
        >
          {{ tag }}
        </span>
      </div>

      <!-- 右侧复选框 -->
      <div class="ml-auto flex items-center gap-3">
        <span class="text-[11px] font-black uppercase tracking-widest text-slate-400" :class="selected && 'text-blue-600 dark:text-indigo-400'">
          {{ selected ? '已选择' : '未选择' }}
        </span>
        <div
          class="flex h-6 w-6 items-center justify-center rounded-lg border-2 transition-all duration-300"
          :class="selected ? 'border-blue-500 bg-blue-500 shadow-lg shadow-blue-500/20 dark:border-indigo-500 dark:bg-indigo-500' : 'border-slate-200 bg-white dark:border-white/5 dark:bg-slate-800'"
        >
          <i v-if="selected" class="fa-solid fa-check text-[10px] text-white"></i>
        </div>
      </div>
    </div>

    <!-- 题目内容区 -->
    <div class="question-content relative pl-2 border-l-2 border-slate-50 dark:border-white/5">
      <template v-if="question.content_blocks?.length">
        <div v-for="(b, i) in question.content_blocks" :key="i">
          <div v-if="b.block_type === 'text'" class="my-4 text-base font-medium leading-relaxed text-slate-800 dark:text-slate-200" v-html="isHtml(b.content) ? sanitizeHtml(b.content) : b.content"></div>
          <img
            v-else-if="b.block_type === 'image' && b.content"
            :src="b.content"
            class="my-6 max-h-[400px] cursor-zoom-in rounded-2xl border border-slate-100 shadow-sm transition-transform hover:scale-[1.01] dark:border-white/5"
            @click.stop="() => emit('open-image', b.content)"
          />
        </div>
      </template>

      <!-- 选项 -->
      <div v-if="question.options?.length" class="mt-8 grid gap-3 sm:grid-cols-2">
        <div
          v-for="(opt, idx) in question.options"
          :key="idx"
          class="flex items-start gap-3 rounded-xl border border-slate-100 bg-slate-50/30 p-4 text-[13px] font-bold text-slate-700 transition-colors hover:bg-slate-50 dark:border-white/5 dark:bg-white/5 dark:text-slate-300 dark:hover:bg-white/10"
        >
          <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-white text-[10px] shadow-sm dark:bg-slate-800">{{ formatOption(opt)[0] }}</span>
          <span class="flex-1">{{ formatOption(opt).slice(2) }}</span>
        </div>
      </div>
    </div>

    <!-- 录入区 -->
    <div class="mt-8 grid gap-4 border-t border-slate-50 pt-8 dark:border-white/5 sm:grid-cols-2" @click.stop>
      <!-- 正确答案 -->
      <div class="group/box relative rounded-2xl border border-emerald-100 bg-emerald-50/30 p-4 transition-colors hover:bg-emerald-50/50 dark:border-emerald-500/10 dark:bg-emerald-500/5">
        <div class="mb-3 flex items-center justify-between">
          <span class="text-[10px] font-black uppercase tracking-widest text-emerald-600 dark:text-emerald-400">正确答案</span>
          <button @click="startEditAnswer" class="text-[10px] font-black text-emerald-600 underline-offset-4 hover:underline">
            {{ question.answer ? '编辑' : '录入' }}
          </button>
        </div>
        
        <div v-if="editingAnswer" class="space-y-3">
          <textarea
            v-model="answerDraft"
            rows="3"
            class="w-full rounded-xl border-none bg-white p-3 text-xs font-bold text-slate-800 shadow-sm focus:ring-2 focus:ring-emerald-500/20 dark:bg-slate-800 dark:text-white"
          ></textarea>
          <div class="flex justify-end gap-2">
            <button @click="cancelAnswer" class="text-[10px] font-black text-slate-400">取消</button>
            <button @click="saveAnswer" class="rounded-lg bg-emerald-600 px-3 py-1.5 text-[10px] font-black text-white shadow-lg shadow-emerald-600/20">完成</button>
          </div>
        </div>
        <div v-else class="text-[13px] font-bold leading-relaxed text-slate-700 dark:text-slate-300">
          {{ question.answer || '点击上方按钮录入参考答案...' }}
        </div>
      </div>

      <!-- 错因笔记 -->
      <div class="group/box relative rounded-2xl border border-blue-100 bg-blue-50/30 p-4 transition-colors hover:bg-blue-50/50 dark:border-indigo-500/10 dark:bg-indigo-500/5">
        <div class="mb-3 flex items-center justify-between">
          <span class="text-[10px] font-black uppercase tracking-widest text-blue-600 dark:text-indigo-400">我的笔记</span>
          <button @click="startEditUserAnswer" class="text-[10px] font-black text-blue-600 underline-offset-4 hover:underline dark:text-indigo-400">
            {{ question.user_answer ? '编辑' : '录入' }}
          </button>
        </div>
        
        <div v-if="editingUserAnswer" class="space-y-3">
          <textarea
            v-model="userAnswerDraft"
            rows="3"
            class="w-full rounded-xl border-none bg-white p-3 text-xs font-bold text-slate-800 shadow-sm focus:ring-2 focus:ring-blue-500/20 dark:bg-slate-800 dark:text-white"
          ></textarea>
          <div class="flex justify-end gap-2">
            <button @click="cancelUserAnswer" class="text-[10px] font-black text-slate-400">取消</button>
            <button @click="saveUserAnswer" class="rounded-lg bg-blue-600 px-3 py-1.5 text-[10px] font-black text-white shadow-lg shadow-blue-600/20 dark:bg-indigo-500">完成</button>
          </div>
        </div>
        <div v-else class="text-[13px] font-bold leading-relaxed text-slate-700 dark:text-slate-300">
          {{ question.user_answer || '记录你的错因或学习笔记...' }}
        </div>
      </div>
    </div>
  </div>
</template>
