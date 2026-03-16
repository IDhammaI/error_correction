<script setup>
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import QuestionCard from './QuestionCard.vue'
import { typesetMath } from '../utils.js'

const props = defineProps({
  questions: { type: Array, default: () => [] },
  selectedIds: { type: Object, default: () => new Set() },
})

const emit = defineEmits(['toggle-select', 'select-all', 'deselect-all', 'open-image', 'reorder'])

const questionListEl = ref(null)
const questionsBoxEl = ref(null)
let sortable = null

const selectedCountLabel = computed(() => `已选 ${props.selectedIds.size} 项`)

const triggerTypeset = async () => {
  await nextTick()
  if (questionsBoxEl.value) {
    await typesetMath(questionsBoxEl.value)
  }
}

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
  if (val && val.length) {
    initSortable()
    triggerTypeset()
  }
}, { flush: 'post', deep: true })

onMounted(() => {
  if (props.questions.length) {
    initSortable()
    triggerTypeset()
  }
})

defineExpose({ initSortable, questionsBoxEl, triggerTypeset })
</script>

<template>
  <div v-if="questions.length" ref="questionsBoxEl" class="mt-8 relative z-10">
    <div class="flex flex-col gap-4 border-b border-slate-100/80 pb-6 sm:flex-row sm:items-end sm:justify-between dark:border-white/5">
        <div>
          <div class="mb-1 flex items-center gap-2">
            <div class="flex h-5 w-5 items-center justify-center rounded-lg bg-blue-100 text-blue-600 dark:bg-indigo-500/20 dark:text-indigo-400">
              <i class="fa-solid fa-layer-group text-[9px]"></i>
            </div>
            <span class="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">解析结果</span>
          </div>
          <h3 class="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
            题目数据核对
          </h3>
          <p class="mt-1 text-[11px] font-bold text-slate-500 dark:text-slate-400">
            拖拽调整排序，点击卡片选择导出
          </p>
        </div>
        
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center gap-1 rounded-xl border border-slate-100 bg-white/50 p-1 shadow-sm backdrop-blur-md dark:border-white/5 dark:bg-slate-800/50">
            <button 
              type="button" 
              class="flex items-center gap-2 rounded-lg px-4 py-1.5 text-[10px] font-black text-slate-600 hover:bg-white hover:text-blue-600 hover:shadow-sm dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-indigo-300" 
              @click="emit('select-all')"
            >
              全选
            </button>
            <button 
              type="button" 
              class="flex items-center gap-2 rounded-lg px-4 py-1.5 text-[10px] font-black text-slate-600 hover:bg-white hover:text-rose-500 hover:shadow-sm dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-rose-400" 
              @click="emit('deselect-all')"
            >
              清空
            </button>
          </div>
          
          <div class="flex h-9 items-center gap-2 rounded-xl bg-slate-900 px-4 text-[10px] font-black text-white shadow-xl shadow-slate-900/20 dark:bg-white dark:text-slate-900 dark:shadow-none">
            <i class="fa-solid fa-square-check text-blue-400"></i>
            <span class="tracking-widest">{{ selectedCountLabel }}</span>
          </div>
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
</template>