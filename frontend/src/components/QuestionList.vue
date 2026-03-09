<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import QuestionCard from './QuestionCard.vue'

const props = defineProps({
  questions: { type: Array, default: () => [] },
  selectedIds: { type: Object, default: () => new Set() },
})

const emit = defineEmits(['toggle-select', 'select-all', 'deselect-all', 'open-image', 'reorder'])

const questionListEl = ref(null)
const questionsBoxEl = ref(null)
let sortable = null

const selectedCountLabel = computed(() => `已选 ${props.selectedIds.size} 项`)

const initSortable = async () => {
  await nextTick()
  const el = questionListEl.value
  if (!el) return
  const Sortable = window.Sortable
  if (!Sortable) return
  if (sortable) sortable.destroy()
  sortable = Sortable.create(el, {
    animation: 250,
    easing: "cubic-bezier(0.2, 0, 0, 1)",
    handle: '[data-drag-handle="1"]',
    ghostClass: 'opacity-50',
    onEnd: (evt) => {
      const { oldIndex, newIndex } = evt
      if (oldIndex == null || newIndex == null || oldIndex === newIndex) return
      emit('reorder', oldIndex, newIndex)
    },
  })
}

watch(() => props.questions, (val) => {
  if (val && val.length) initSortable()
}, { flush: 'post' })

defineExpose({ initSortable, questionsBoxEl })
</script>

<template>
  <div ref="questionsBoxEl" class="mt-10 relative">
    <div v-if="questions.length" class="relative overflow-hidden rounded-3xl border border-slate-200/60 bg-white/40 p-5 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-[#05050A]/60 sm:p-8">
      
      <!-- 容器背景光点缀 -->
      <div class="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-blue-500/10 blur-[80px] dark:bg-indigo-500/10"></div>
      
      <div class="relative z-10 flex flex-col gap-4 border-b border-slate-200/60 pb-5 sm:flex-row sm:items-end sm:justify-between dark:border-white/10">
        <div>
          <h3 class="flex items-center gap-2 text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            <i class="fa-solid fa-layer-group text-blue-500 dark:text-indigo-400"></i>
            题目数据核对
          </h3>
          <p class="mt-1.5 text-sm font-medium text-slate-500 dark:text-slate-400">拖拽可排序，点击选择最终需要导出的错题</p>
        </div>
        
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex rounded-xl border border-slate-200 bg-white/60 p-1 shadow-sm backdrop-blur-md dark:border-white/10 dark:bg-slate-900/60">
            <button 
              type="button" 
              class="flex items-center gap-2 rounded-lg px-4 py-1.5 text-sm font-bold text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white" 
              @click="emit('select-all')"
            >
              <i class="fa-solid fa-check-double text-blue-500 dark:text-indigo-400"></i>
              全选
            </button>
            <div class="my-1 w-px bg-slate-200 dark:bg-white/10"></div>
            <button 
              type="button" 
              class="flex items-center gap-2 rounded-lg px-4 py-1.5 text-sm font-bold text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white" 
              @click="emit('deselect-all')"
            >
              <i class="fa-solid fa-rotate-left"></i>
              取消
            </button>
          </div>
          
          <span class="inline-flex items-center gap-1.5 rounded-xl border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-bold text-blue-700 dark:border-indigo-500/30 dark:bg-indigo-500/10 dark:text-indigo-300">
            <i class="fa-solid fa-calculator text-[10px]"></i>
            {{ selectedCountLabel }}
          </span>
        </div>
      </div>

      <!-- 题目列表 -->
      <div ref="questionListEl" class="relative z-10 mt-6 grid gap-5" id="questionList">
        <QuestionCard
          v-for="q in questions"
          :key="q.question_id"
          :question="q"
          :selected="selectedIds.has(q.question_id)"
          @toggle="(id) => emit('toggle-select', id)"
          @open-image="(src) => emit('open-image', src)"
        />
      </div>
    </div>
  </div>
</template>