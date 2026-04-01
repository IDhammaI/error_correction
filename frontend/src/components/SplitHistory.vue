<script setup>
import { ref, watch, nextTick } from 'vue'
import * as api from '../api.js'
import { isHtml, sanitizeHtml, typesetMath as _typesetMath } from '../utils.js'

const props = defineProps({
  theme: { type: String, default: 'light' },
  visible: { type: Boolean, default: false },
})

const emit = defineEmits(['push-toast', 'open-image', 'load-record', 'go-workspace'])

// ---- 列表数据 ----
const records = ref([])
const loading = ref(false)
const detailLoading = ref(false)

// ---- 详情面板 ----
const activeRecord = ref(null)
const activeQuestions = ref([])
const selectedIds = ref(new Set())

const loadRecords = async () => {
  loading.value = true
  try {
    records.value = await api.fetchSplitRecords(20)
  } catch (e) {
    emit('push-toast', 'error', '加载分割历史失败: ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    loading.value = false
  }
}

const openDetail = async (record) => {
  if (activeRecord.value?.id === record.id) {
    closeDetail()
    return
  }
  detailLoading.value = true
  activeRecord.value = record
  activeQuestions.value = []
  selectedIds.value = new Set()
  try {
    const detail = await api.fetchSplitRecordDetail(record.id)
    // 兼容旧历史记录（无 uid）：按索引补齐
    const qs = detail.questions || []
    qs.forEach((q, i) => { if (q.uid == null) q.uid = `hist_${i}` })
    activeQuestions.value = qs
  } catch (e) {
    emit('push-toast', 'error', '加载记录详情失败')
    activeRecord.value = null
  } finally {
    detailLoading.value = false
  }
  await nextTick()
  const el = document.querySelector('.split-history-questions')
  if (el) await _typesetMath(el)
}

const closeDetail = () => {
  activeRecord.value = null
  activeQuestions.value = []
  selectedIds.value = new Set()
}

const toggleSelect = (qid) => {
  const s = new Set(selectedIds.value)
  if (s.has(qid)) s.delete(qid)
  else s.add(qid)
  selectedIds.value = s
}

const selectAllQuestions = () => {
  selectedIds.value = new Set(activeQuestions.value.map(q => q.uid))
}

const deselectAllQuestions = () => {
  selectedIds.value = new Set()
}

const loadToWorkspace = () => {
  if (!activeQuestions.value.length) return
  const qs = selectedIds.value.size > 0
    ? activeQuestions.value.filter(q => selectedIds.value.has(q.uid))
    : activeQuestions.value
  emit('load-record', qs, activeRecord.value)
}

// ---- 格式化 ----
const formatDate = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now - d
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr} 小时前`
  const diffDay = Math.floor(diffHr / 24)
  if (diffDay < 7) return `${diffDay} 天前`
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hr = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return y === now.getFullYear() ? `${m}-${day} ${hr}:${min}` : `${y}-${m}-${day}`
}

const formatFullDate = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
}

const providerLabel = (p) => {
  const map = { deepseek: 'DeepSeek', ernie: '文心一言', openai: 'OpenAI' }
  return map[p] || p || '未知'
}

const providerColor = (p) => {
  if (p === 'deepseek') return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300'
  if (p === 'ernie') return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300'
  return 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
}

const questionTypeIcon = (t) => {
  if (t === '选择题') return 'fa-list-check'
  if (t === '填空题') return 'fa-pen-to-square'
  if (t === '判断题') return 'fa-circle-check'
  if (t === '解答题' || t === '计算题') return 'fa-calculator'
  return 'fa-question'
}

const questionTypeBadge = (t) => {
  if (t === '选择题') return 'bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300'
  if (t === '填空题') return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300'
  if (t === '判断题') return 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300'
  return 'bg-slate-100 text-slate-600 dark:bg-slate-500/15 dark:text-slate-300'
}

// ---- 初始化 ----
watch(() => props.visible, (v) => {
  if (v) loadRecords()
}, { immediate: true })

defineExpose({ refresh: loadRecords })
</script>

<template>
  <div v-show="visible" class="flex h-full flex-col overflow-hidden">
    <!-- 背景光晕 -->
    <div class="pointer-events-none absolute inset-0 z-0 overflow-hidden">
      <div class="animate-blob absolute -top-[15%] right-[-5%] h-[45vw] w-[45vw] rounded-full bg-violet-300/[0.10] mix-blend-multiply blur-[120px] dark:bg-violet-600/15 dark:mix-blend-screen"></div>
      <div class="animate-blob animation-delay-4000 absolute -bottom-[10%] left-[-8%] h-[40vw] w-[40vw] rounded-full bg-blue-200/[0.12] mix-blend-multiply blur-[100px] dark:bg-blue-500/10 dark:mix-blend-screen"></div>
    </div>

    <div class="container relative z-10 mx-auto flex h-full max-w-6xl flex-col px-4 py-4 sm:px-8 sm:py-6">
      <!-- 页头 -->
      <div class="mb-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between shrink-0">
        <div class="flex items-center gap-4">
          <button
            @click="emit('go-workspace')"
            class="group flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200/60 bg-white/60 text-slate-500 backdrop-blur-md transition-all hover:border-blue-500/50 hover:bg-white hover:text-blue-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-400 dark:hover:border-indigo-500/50 dark:hover:text-indigo-300"
          >
            <i class="fa-solid fa-arrow-left-long transition-transform group-hover:-translate-x-1"></i>
          </button>
          <div>
            <div class="mb-1 flex items-center gap-2">
              <span class="inline-flex items-center rounded-full bg-violet-100 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-violet-700 dark:bg-violet-500/20 dark:text-violet-300">
                History
              </span>
              <span class="h-1 w-1 rounded-full bg-slate-300 dark:bg-slate-600"></span>
              <span class="text-[9px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">最近 20 条</span>
            </div>
            <h2 class="text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl dark:text-white">分割历史</h2>
          </div>
        </div>
        <button
          @click="loadRecords"
          :disabled="loading"
          class="inline-flex items-center gap-2 rounded-xl border border-slate-200/60 bg-white/60 px-4 py-2.5 text-sm font-bold text-slate-600 backdrop-blur-md transition-all hover:border-violet-500/40 hover:bg-white hover:text-violet-600 disabled:opacity-50 dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:hover:border-violet-500/40 dark:hover:text-violet-300"
        >
          <i class="fa-solid fa-arrows-rotate text-sm" :class="{ 'animate-spin': loading }"></i>
          刷新
        </button>
      </div>

      <!-- 主体 -->
      <div class="flex-1 overflow-y-auto pr-1 custom-scrollbar">

        <!-- 加载状态 -->
        <div v-if="loading && !records.length" class="flex flex-col items-center justify-center py-20">
          <div class="mb-4 h-10 w-10 animate-spin rounded-full border-[3px] border-slate-200 border-t-violet-500 dark:border-slate-700 dark:border-t-violet-400"></div>
          <span class="text-sm font-semibold text-slate-400 dark:text-slate-500">加载中...</span>
        </div>

        <!-- 空状态 -->
        <div v-else-if="!loading && !records.length" class="flex flex-col items-center justify-center py-20">
          <div class="mb-4 flex h-20 w-20 items-center justify-center rounded-3xl bg-slate-100 dark:bg-white/5">
            <i class="fa-solid fa-clock-rotate-left text-3xl text-slate-300 dark:text-slate-600"></i>
          </div>
          <p class="text-base font-bold text-slate-400 dark:text-slate-500">暂无分割记录</p>
          <p class="mt-1 text-xs text-slate-400 dark:text-slate-600">完成题目分割后，记录将自动保存在这里</p>
        </div>

        <!-- 记录列表 -->
        <div v-else class="space-y-3">
          <div
            v-for="(r, idx) in records"
            :key="r.id"
            class="group cursor-pointer rounded-2xl border transition-all duration-300"
            :class="activeRecord?.id === r.id
              ? 'border-violet-400/60 bg-violet-50/50 shadow-lg shadow-violet-500/10 dark:border-violet-500/40 dark:bg-violet-500/[0.06] dark:shadow-violet-500/5'
              : 'border-slate-200/60 bg-white/70 hover:border-violet-300/50 hover:bg-white/90 hover:shadow-md dark:border-white/[0.06] dark:bg-white/[0.03] dark:hover:border-violet-500/20 dark:hover:bg-white/[0.05]'"
            @click="openDetail(r)"
          >
            <!-- 记录卡片头 -->
            <div class="flex items-center gap-4 px-5 py-4">
              <!-- 序号圆 -->
              <div
                class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-sm font-black transition-colors"
                :class="activeRecord?.id === r.id
                  ? 'bg-violet-500 text-white shadow-md shadow-violet-500/30'
                  : 'bg-slate-100 text-slate-500 group-hover:bg-violet-100 group-hover:text-violet-600 dark:bg-white/[0.06] dark:text-slate-400 dark:group-hover:bg-violet-500/20 dark:group-hover:text-violet-300'"
              >
                {{ records.length - idx }}
              </div>

              <!-- 主信息 -->
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2 mb-1">
                  <span class="truncate text-sm font-bold text-slate-800 dark:text-white">
                    {{ r.subject || '未识别科目' }}
                  </span>
                  <span class="rounded-full px-2 py-0.5 text-[10px] font-bold" :class="providerColor(r.model_provider)">
                    {{ providerLabel(r.model_provider) }}
                  </span>
                </div>
                <div class="flex items-center gap-3 text-xs text-slate-400 dark:text-slate-500">
                  <span class="inline-flex items-center gap-1">
                    <i class="fa-regular fa-file text-[10px]"></i>
                    {{ (r.file_names || []).length }} 个文件
                  </span>
                  <span class="h-3 w-px bg-slate-200 dark:bg-white/10"></span>
                  <span class="inline-flex items-center gap-1" :title="formatFullDate(r.created_at)">
                    <i class="fa-regular fa-clock text-[10px]"></i>
                    {{ formatDate(r.created_at) }}
                  </span>
                </div>
              </div>

              <!-- 题目数 + 展开箭头 -->
              <div class="flex items-center gap-3 shrink-0">
                <div class="text-right">
                  <div class="text-xl font-black tabular-nums text-slate-800 dark:text-white">{{ r.question_count }}</div>
                  <div class="text-[10px] font-bold text-slate-400 dark:text-slate-500">道题目</div>
                </div>
                <i
                  class="fa-solid fa-chevron-down text-xs text-slate-300 transition-transform duration-300 dark:text-slate-600"
                  :class="{ '-rotate-180': activeRecord?.id === r.id }"
                ></i>
              </div>
            </div>

            <!-- 文件名列表 -->
            <div v-if="r.file_names?.length" class="flex flex-wrap gap-1.5 px-5 pb-3">
              <span
                v-for="fname in r.file_names"
                :key="fname"
                class="inline-flex items-center gap-1 rounded-lg bg-slate-100/80 px-2 py-0.5 text-[11px] font-semibold text-slate-500 dark:bg-white/[0.04] dark:text-slate-400"
              >
                <i class="fa-solid text-[9px]" :class="fname.toLowerCase().endsWith('.pdf') ? 'fa-file-pdf text-rose-400' : 'fa-file-image text-blue-400'"></i>
                {{ fname }}
              </span>
            </div>

            <!-- 展开详情面板 -->
            <Transition
              enter-active-class="transition-all duration-400 ease-out"
              enter-from-class="max-h-0 opacity-0"
              enter-to-class="max-h-[2000px] opacity-100"
              leave-active-class="transition-all duration-300 ease-in"
              leave-from-class="max-h-[2000px] opacity-100"
              leave-to-class="max-h-0 opacity-0"
            >
              <div v-if="activeRecord?.id === r.id" class="overflow-hidden border-t border-slate-200/40 dark:border-white/5">
                <!-- 加载中 -->
                <div v-if="detailLoading" class="flex items-center justify-center py-10">
                  <div class="h-7 w-7 animate-spin rounded-full border-[3px] border-slate-200 border-t-violet-500 dark:border-slate-700 dark:border-t-violet-400"></div>
                </div>

                <!-- 题目列表 -->
                <div v-else class="split-history-questions px-5 py-4">
                  <!-- 工具栏 -->
                  <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
                    <div class="flex items-center gap-2">
                      <button
                        @click.stop="selectAllQuestions"
                        class="rounded-lg border border-slate-200/60 bg-white/60 px-3 py-1.5 text-xs font-bold text-slate-600 transition-all hover:bg-white dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:hover:bg-white/10"
                      >全选</button>
                      <button
                        v-if="selectedIds.size > 0"
                        @click.stop="deselectAllQuestions"
                        class="rounded-lg border border-slate-200/60 bg-white/60 px-3 py-1.5 text-xs font-bold text-slate-500 transition-all hover:bg-white dark:border-white/10 dark:bg-white/5 dark:text-slate-400 dark:hover:bg-white/10"
                      >取消选择</button>
                      <span v-if="selectedIds.size > 0" class="ml-1 text-xs font-semibold text-violet-600 dark:text-violet-400">
                        已选 {{ selectedIds.size }} / {{ activeQuestions.length }}
                      </span>
                    </div>
                    <button
                      @click.stop="loadToWorkspace"
                      class="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2 text-xs font-bold text-white shadow-sm transition-all hover:bg-violet-700 hover:shadow-md dark:bg-violet-500 dark:hover:bg-violet-600"
                    >
                      <i class="fa-solid fa-arrow-right-to-bracket"></i>
                      {{ selectedIds.size > 0 ? `加载选中 (${selectedIds.size})` : '全部加载到工作台' }}
                    </button>
                  </div>

                  <!-- 题目网格 -->
                  <div class="grid grid-cols-1 gap-2.5 lg:grid-cols-2">
                    <div
                      v-for="q in activeQuestions"
                      :key="q.uid"
                      @click.stop="toggleSelect(q.uid)"
                      class="cursor-pointer rounded-xl border p-3.5 transition-all duration-200"
                      :class="selectedIds.has(q.uid)
                        ? 'border-violet-400/60 bg-violet-50/60 ring-1 ring-violet-400/30 dark:border-violet-500/40 dark:bg-violet-500/[0.08] dark:ring-violet-500/20'
                        : 'border-slate-200/50 bg-white/50 hover:border-violet-300/40 hover:bg-white/80 dark:border-white/[0.05] dark:bg-white/[0.02] dark:hover:border-violet-500/20'"
                    >
                      <div class="mb-2 flex items-center gap-2">
                        <!-- 选中指示 -->
                        <div
                          class="flex h-5 w-5 shrink-0 items-center justify-center rounded-md border text-[10px] transition-colors"
                          :class="selectedIds.has(q.uid)
                            ? 'border-violet-500 bg-violet-500 text-white dark:border-violet-400 dark:bg-violet-500'
                            : 'border-slate-300 dark:border-white/15'"
                        >
                          <i v-if="selectedIds.has(q.uid)" class="fa-solid fa-check"></i>
                        </div>
                        <span class="text-xs font-black text-slate-700 dark:text-slate-200">
                          {{ q.question_id || '?' }}
                        </span>
                        <span v-if="q.question_type" class="rounded-md px-1.5 py-0.5 text-[10px] font-bold" :class="questionTypeBadge(q.question_type)">
                          <i class="fa-solid mr-0.5 text-[8px]" :class="questionTypeIcon(q.question_type)"></i>
                          {{ q.question_type }}
                        </span>
                        <span v-if="q.has_formula" class="rounded-md bg-purple-100/80 px-1.5 py-0.5 text-[10px] font-bold text-purple-600 dark:bg-purple-500/15 dark:text-purple-300">
                          <i class="fa-solid fa-square-root-variable text-[8px]"></i>
                        </span>
                        <span v-if="q.has_image" class="rounded-md bg-cyan-100/80 px-1.5 py-0.5 text-[10px] font-bold text-cyan-600 dark:bg-cyan-500/15 dark:text-cyan-300">
                          <i class="fa-solid fa-image text-[8px]"></i>
                        </span>
                      </div>
                      <!-- 题目内容 -->
                      <div class="line-clamp-2 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
                        <template v-if="(q.content_blocks || q.content_json)?.length">
                          <template v-for="(b, i) in (q.content_blocks || q.content_json)" :key="i">
                            <span v-if="b.block_type === 'text'" v-html="isHtml(b.content) ? sanitizeHtml(b.content) : b.content"></span>
                          </template>
                        </template>
                        <span v-else class="italic text-slate-400 dark:text-slate-500">（无文本内容）</span>
                      </div>
                      <!-- 知识点标签 -->
                      <div v-if="q.knowledge_tags?.length" class="mt-2 flex flex-wrap gap-1">
                        <span
                          v-for="tag in q.knowledge_tags.slice(0, 3)"
                          :key="tag"
                          class="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-500 dark:bg-white/[0.05] dark:text-slate-400"
                        >{{ tag }}</span>
                        <span v-if="q.knowledge_tags.length > 3" class="text-[10px] text-slate-400 dark:text-slate-500">+{{ q.knowledge_tags.length - 3 }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- 空题目提示 -->
                  <div v-if="!activeQuestions.length && !detailLoading" class="py-8 text-center text-sm text-slate-400 dark:text-slate-500">
                    此记录无题目数据
                  </div>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
