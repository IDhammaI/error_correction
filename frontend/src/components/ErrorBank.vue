<script setup>
import { ref, reactive, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import * as api from '../api.js'
import { getQuestionSnippet, typesetMath as _typesetMath } from '../utils.js'
import QuestionDetailModal from './QuestionDetailModal.vue'
import CustomSelect from './CustomSelect.vue'
import CalendarPicker from './CalendarPicker.vue'

const props = defineProps({
  theme: { type: String, default: 'light' },
  visible: { type: Boolean, default: false },
})

const emit = defineEmits(['go-workspace', 'push-toast', 'open-image', 'start-chat'])

// ---- 筛选条件 ----
const filters = reactive({
  subject: '',
  knowledge_tag: '',
  question_type: '',
  keyword: '',
  start_date: '',
  end_date: '',
  review_status: '',
})
const page = ref(1)
const pageSize = ref(20)

// 复习状态图标映射
const reviewStatusIcon = (status) => {
  if (status === '待复习') return 'fa-clock text-orange-500'
  if (status === '复习中') return 'fa-spinner text-amber-500'
  return 'fa-circle-check text-emerald-500'
}

// ---- 数据 ----
const items = ref([])
const total = ref(0)
const totalPages = ref(0)
const loading = ref(false)
const subjects = ref([])
const questionTypes = ref([])
const tagNames = ref([])
const selectedIds = reactive(new Set())

const detailOpen = ref(false)
const detailQuestion = ref(null)

// ---- 知识点标签墙 ----
const TAG_BATCH_SIZE = 8
const tagBatchIndex = ref(0)
const tagBatchAnimating = ref(false)
const selectedTags = reactive(new Set())

const TAG_COLORS = [
  { bg: 'bg-[#f08a5d]', text: 'text-black' },
  { bg: 'bg-[#f9d74c]', text: 'text-black' },
  { bg: 'bg-[#c6e3b5]', text: 'text-black' },
  { bg: 'bg-[#a6c1ee]', text: 'text-black' },
  { bg: 'bg-[#f6f2ce]', text: 'text-black' },
  { bg: 'bg-[#ffb5a7]', text: 'text-black' },
  { bg: 'bg-[#e4c1f9]', text: 'text-black' },
  { bg: 'bg-[#8bc9e4]', text: 'text-black' },
  { bg: 'bg-[#ffc3a0]', text: 'text-black' },
  { bg: 'bg-[#a0e4cb]', text: 'text-black' },
  { bg: 'bg-[#dcd3ff]', text: 'text-black' },
  { bg: 'bg-[#ffafcc]', text: 'text-black' },
  { bg: 'bg-[#bde0fe]', text: 'text-black' },
  { bg: 'bg-[#f4a261]', text: 'text-black' },
]

const tagColor = (idx) => TAG_COLORS[idx % TAG_COLORS.length]

const currentTagBatch = computed(() => {
  const start = tagBatchIndex.value * TAG_BATCH_SIZE
  return tagNames.value.slice(start, start + TAG_BATCH_SIZE)
})

const hasMoreTagBatches = computed(() => tagNames.value.length > TAG_BATCH_SIZE)

const refreshTagBatch = () => {
  const totalBatches = Math.ceil(tagNames.value.length / TAG_BATCH_SIZE)
  if (totalBatches <= 1) return
  tagBatchAnimating.value = false
  tagBatchIndex.value = (tagBatchIndex.value + 1) % totalBatches
  requestAnimationFrame(() => { tagBatchAnimating.value = true })
}

const toggleTagSelect = (tag) => {
  if (selectedTags.has(tag)) {
    selectedTags.delete(tag)
  } else {
    selectedTags.add(tag)
  }
  // 多选标签同步到筛选（取第一个选中的标签给下拉框）
  const arr = Array.from(selectedTags)
  filters.knowledge_tag = arr.length === 1 ? arr[0] : arr.length > 1 ? arr.join(',') : ''
}

const clearTagSelection = () => {
  selectedTags.clear()
  filters.knowledge_tag = ''
}

// 下拉框单选 → 同步到标签墙
watch(() => filters.knowledge_tag, (val) => {
  // 如果是标签墙触发的多选逗号值，不要反向覆盖
  if (val && !val.includes(',')) {
    selectedTags.clear()
    selectedTags.add(val)
  } else if (!val) {
    selectedTags.clear()
  }
})

const totalText = computed(() => `共收录 ${total.value} 道题目`)

// ---- 查询 ----
let debounceTimer = null
const doQuery = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filters.subject) params.subject = filters.subject
    if (filters.knowledge_tag) params.knowledge_tag = filters.knowledge_tag
    if (filters.question_type) params.question_type = filters.question_type
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.start_date) params.start_date = filters.start_date
    if (filters.end_date) params.end_date = filters.end_date
    if (filters.review_status) params.review_status = filters.review_status

    const data = await api.fetchErrorBank(params)
    items.value = data.items || []
    total.value = data.total || 0
    totalPages.value = data.total_pages || 0
  } catch (e) {
    emit('push-toast', 'error', e instanceof Error ? e.message : String(e))
  } finally {
    loading.value = false
    typesetMath()
  }
}

const debouncedQuery = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => { page.value = 1; doQuery() }, 300)
}

watch(() => [filters.subject, filters.knowledge_tag, filters.question_type, filters.start_date, filters.end_date, filters.review_status], debouncedQuery)
watch(() => filters.keyword, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => { page.value = 1; doQuery() }, 500)
})

const resetFilters = () => {
  Object.keys(filters).forEach(k => filters[k] = '')
  selectedTags.clear()
  page.value = 1
  doQuery()
}

const goPage = (p) => {
  if (p < 1 || p > totalPages.value) return
  page.value = p
  doQuery()
}

const toggleSelect = (id) => { selectedIds.has(id) ? selectedIds.delete(id) : selectedIds.add(id) }
const clearSelection = () => { selectedIds.clear() }

const doExport = async () => {
  if (!selectedIds.size) return
  try {
    const data = await api.exportFromDb(Array.from(selectedIds))
    emit('push-toast', 'success', '错题本导出成功')
    let filename = 'wrongbook.md'
    if (data.output_path) {
      const parts = String(data.output_path).split(/[/\\]/)
      const last = parts[parts.length - 1]; if (last) filename = last
    }
    const a = document.createElement('a')
    a.href = `/download/${encodeURIComponent(filename)}?t=${Date.now()}`
    a.download = filename
    document.body.appendChild(a); a.click(); a.remove()
  } catch (e) {
    emit('push-toast', 'error', '导出失败: ' + (e instanceof Error ? e.message : String(e)))
  }
}

const openDetail = (q) => { detailQuestion.value = q; detailOpen.value = true }
const closeDetail = () => { detailOpen.value = false; detailQuestion.value = null }

const onDeleted = (id) => {
  items.value = items.value.filter(q => q.id !== id)
  total.value = Math.max(0, total.value - 1)
  selectedIds.delete(id)
  closeDetail()
}

const onAnswerSaved = (id, answer, updatedAt) => {
  const q = items.value.find(x => x.id === id)
  if (q) { q.user_answer = answer; q.updated_at = updatedAt }
}

const onReviewStatusChanged = (id, status, updatedAt) => {
  const q = items.value.find(x => x.id === id)
  if (q) { q.review_status = status; q.updated_at = updatedAt }
}

const getSummary = (q) => getQuestionSnippet(q)

const typesetMath = async () => {
  await nextTick()
  await _typesetMath()
}

const pageButtons = computed(() => {
  const tp = totalPages.value; const cp = page.value
  if (tp <= 7) return Array.from({ length: tp }, (_, i) => i + 1)
  const pages = [1]
  let start = Math.max(2, cp - 1); let end = Math.min(tp - 1, cp + 1)
  if (start > 2) pages.push('...')
  for (let i = start; i <= end; i++) pages.push(i)
  if (end < tp - 1) pages.push('...')
  pages.push(tp)
  return pages
})

const refreshTags = async () => {
  tagNames.value = await api.fetchTagNames(filters.subject || undefined)
  tagBatchIndex.value = 0
}

const loadFilters = async () => {
  try {
    const [s, qt] = await Promise.all([
      api.fetchSubjects(),
      api.fetchQuestionTypes(),
    ])
    subjects.value = s
    questionTypes.value = qt
    await refreshTags()
    nextTick(() => { tagBatchAnimating.value = true })
  } catch (e) {
    emit('push-toast', 'error', '加载筛选项失败')
  }
}

const reloadTags = async () => {
  try {
    await refreshTags()
    // 清除已选中但不再属于当前学科的标签
    const valid = new Set(tagNames.value)
    for (const t of Array.from(selectedTags)) {
      if (!valid.has(t)) selectedTags.delete(t)
    }
    filters.knowledge_tag = Array.from(selectedTags).join(',')
  } catch (e) { /* 静默失败，loadFilters 已加载过 */ }
}

watch(() => filters.subject, () => { reloadTags() })

watch(() => props.visible, (v) => { if (v) { loadFilters(); doQuery() } })

defineExpose({ refresh: doQuery })

onBeforeUnmount(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
})
</script>

<template>
  <div class="relative h-full overflow-y-auto custom-scrollbar">
    <div class="container relative z-10 mx-auto max-w-6xl px-4 py-8 sm:px-8">
      <!-- 页面标题：强化科技质感 -->
      <div class="mb-10 flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div class="mb-2 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-bold text-blue-600 dark:border-indigo-500/30 dark:bg-indigo-500/10 dark:text-indigo-300">
            <i class="fa-solid fa-vault animate-pulse"></i> 智能存档中心
          </div>
          <h2 class="text-3xl font-black tracking-tight text-slate-900 sm:text-4xl dark:text-white">
            错题知识图谱
          </h2>
          <p class="mt-2 flex items-center gap-2 text-sm font-bold text-slate-600 dark:text-slate-400">
            <i class="fa-solid fa-chart-line text-blue-500"></i> {{ totalText }} · 记录每一次认知的突破
          </p>
        </div>
        <button @click="emit('go-workspace')" class="btn-primary group h-12 px-8 shadow-xl shadow-blue-500/20">
          <i class="fa-solid fa-plus-circle transition-transform group-hover:rotate-90"></i>
          录入新题目
        </button>
      </div>

      <!-- 搜索控制台：玻璃态工具栏 -->
      <div class="relative z-20 mb-8 space-y-5 rounded-3xl border border-slate-200/60 bg-white/40 p-5 shadow-sm backdrop-blur-2xl dark:border-white/10 dark:bg-[#0A0A0F]/60 sm:p-6">
        <!-- 第一行：关键词 + 三个下拉 -->
        <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <!-- 关键词 -->
          <div>
            <label class="mb-2 block text-[11px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-500">内容检索</label>
            <div class="relative group">
              <i class="fa-solid fa-magnifying-glass absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-500 transition-colors"></i>
              <input v-model="filters.keyword" type="text" placeholder="搜索题目关键词..." class="h-11 w-full rounded-xl border border-slate-200/60 bg-white/50 pl-11 pr-4 text-sm font-bold shadow-sm backdrop-blur-sm outline-none hover:-translate-y-0.5 hover:border-blue-400/50 hover:bg-white/70 hover:shadow-md focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 dark:border-white/10 dark:bg-white/5 dark:text-white dark:hover:border-indigo-500/30 dark:hover:bg-white/10 dark:focus:border-indigo-500/50" />
            </div>
          </div>

          <CustomSelect v-model="filters.subject" :options="subjects" label="学科" placeholder="全部学科" />
          <CustomSelect v-model="filters.knowledge_tag" :options="tagNames" label="知识点标签" placeholder="全部知识点" />
          <CustomSelect v-model="filters.question_type" :options="questionTypes" label="题型" placeholder="全部题型" />
        </div>

        <!-- 第二行：复习状态 + 日期范围 + 重置 -->
        <div class="flex flex-wrap items-end gap-5">
          <CustomSelect v-model="filters.review_status" :options="['待复习', '复习中', '已掌握']" label="复习状态" placeholder="全部状态" :icon="reviewStatusIcon" width-class="w-40 shrink-0" />

          <!-- 时间跨度 -->
          <div class="min-w-0 flex-1">
            <label class="mb-2 block text-[11px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-500">时间跨度</label>
            <div class="flex items-center gap-3">
              <CalendarPicker v-model="filters.start_date" label="开始日期" align="left" />
              <span class="shrink-0 text-slate-400 dark:text-slate-600 font-black">—</span>
              <CalendarPicker v-model="filters.end_date" label="结束日期" align="right" />
            </div>
          </div>
          
          <button @click="resetFilters" class="btn-secondary h-11 shrink-0 px-5 shadow-sm hover:-translate-y-0.5 hover:shadow-md" title="重置筛选">
            <i class="fa-solid fa-arrow-rotate-right"></i>
          </button>
        </div>
      </div>

      <!-- 知识点标签墙 Bento Grid -->
      <div v-if="tagNames.length" class="mb-8 rounded-3xl border border-slate-200/60 bg-white/40 p-5 shadow-sm backdrop-blur-2xl dark:border-white/10 dark:bg-[#0A0A0F]/60 sm:p-6">
        <div class="mb-4 flex items-end justify-between">
          <div>
            <h3 class="flex items-center gap-2 text-sm font-black text-slate-800 dark:text-slate-300">
              <i class="fa-solid fa-cubes text-indigo-500"></i> 知识点快速检索
            </h3>
            <p class="mt-1 text-[11px] text-slate-500 dark:text-slate-500">点击标签筛选对应错题，支持多选</p>
          </div>
          <button v-if="hasMoreTagBatches" @click="refreshTagBatch"
            class="group flex items-center gap-1.5 rounded-full border border-slate-200/60 bg-white/60 px-3 py-1.5 text-xs font-bold text-slate-600 shadow-sm hover:border-blue-300 hover:bg-blue-50 hover:text-blue-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-400 dark:hover:border-indigo-500/30 dark:hover:text-indigo-400">
            <svg class="h-3.5 w-3.5 transition-transform duration-500 group-hover:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            换一批
          </button>
        </div>
        <div class="flex flex-wrap gap-2.5" :class="{ 'tag-batch-active': tagBatchAnimating }">
          <button v-for="(tag, idx) in currentTagBatch" :key="tag"
            @click="toggleTagSelect(tag)"
            class="bento-tag relative overflow-hidden rounded-2xl px-4 py-2.5 text-sm font-bold hover:scale-[0.97] hover:brightness-105 active:scale-95"
            :class="[
              tagColor(tagBatchIndex * TAG_BATCH_SIZE + idx).bg,
              tagColor(tagBatchIndex * TAG_BATCH_SIZE + idx).text,
              selectedTags.has(tag) ? 'ring-2 ring-blue-500 ring-offset-2 dark:ring-indigo-400 dark:ring-offset-slate-900 shadow-lg' : 'shadow-sm'
            ]"
            :style="{ animationDelay: (idx * 0.05) + 's' }">
            <span class="relative z-10 flex items-center gap-1.5">
              <i v-if="selectedTags.has(tag)" class="fa-solid fa-check text-[10px]"></i>
              {{ tag }}
            </span>
            <div class="absolute inset-0 bg-black/5 opacity-0 transition-opacity hover:opacity-100"></div>
          </button>
        </div>
        <div v-if="selectedTags.size" class="mt-3 flex items-center gap-2">
          <span class="text-[11px] font-bold text-slate-400 dark:text-slate-500">已选 {{ selectedTags.size }} 个标签</span>
          <button @click="clearTagSelection" class="text-[11px] font-bold text-blue-500 hover:text-blue-700 dark:text-indigo-400 dark:hover:text-indigo-300">清除全部</button>
        </div>
      </div>

      <!-- 复习状态说明卡片 -->
      <div class="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div class="flex items-start gap-3 rounded-2xl border border-orange-300 bg-orange-50 p-4 dark:border-orange-500/20 dark:bg-orange-500/10">
          <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-orange-100 dark:bg-orange-500/20">
            <i class="fa-solid fa-clock text-orange-500"></i>
          </div>
          <div>
            <div class="text-sm font-black text-orange-700 dark:text-orange-300">待复习</div>
            <p class="mt-0.5 text-xs font-semibold leading-relaxed text-orange-600 dark:text-orange-300/80">新录入的错题，等待首次复习巩固</p>
          </div>
        </div>
        <div class="flex items-start gap-3 rounded-2xl border border-amber-300 bg-amber-50 p-4 dark:border-amber-500/20 dark:bg-amber-500/10">
          <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber-100 dark:bg-amber-500/20">
            <i class="fa-solid fa-spinner text-amber-500"></i>
          </div>
          <div>
            <div class="text-sm font-black text-amber-700 dark:text-amber-300">复习中</div>
            <p class="mt-0.5 text-xs font-semibold leading-relaxed text-amber-600 dark:text-amber-300/80">正在反复练习中，还需要继续加强</p>
          </div>
        </div>
        <div class="flex items-start gap-3 rounded-2xl border border-emerald-300 bg-emerald-50 p-4 dark:border-emerald-500/20 dark:bg-emerald-500/10">
          <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-100 dark:bg-emerald-500/20">
            <i class="fa-solid fa-circle-check text-emerald-500"></i>
          </div>
          <div>
            <div class="text-sm font-black text-emerald-700 dark:text-emerald-300">已掌握</div>
            <p class="mt-0.5 text-xs font-semibold leading-relaxed text-emerald-600 dark:text-emerald-300/80">已完全理解并能独立解答，无需再复习</p>
          </div>
        </div>
      </div>

      <!-- 列表区：使用精美的卡片网格 -->
      <div v-if="loading" class="flex flex-col items-center justify-center py-40">
        <div class="relative h-16 w-16">
          <div class="absolute inset-0 animate-spin rounded-full border-4 border-blue-500/20 border-t-blue-500"></div>
          <i class="fa-solid fa-cube absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-xl text-blue-500"></i>
        </div>
        <p class="mt-6 font-mono text-xs font-black uppercase tracking-[0.3em] text-slate-400">正在加载题库...</p>
      </div>

      <div v-else-if="!items.length" class="flex flex-col items-center justify-center rounded-[2.5rem] border-2 border-dashed border-slate-200 bg-slate-50/50 py-32 dark:border-white/5 dark:bg-white/5">
        <div class="mb-8 flex h-24 w-24 items-center justify-center rounded-3xl bg-white shadow-xl dark:bg-slate-900">
          <i class="fa-solid fa-box-open text-4xl text-slate-300 dark:text-slate-700"></i>
        </div>
        <p class="text-xl font-black text-slate-900 dark:text-white">暂无匹配记录</p>
        <p class="mt-2 text-sm font-medium text-slate-500">调整筛选条件，或者开始新的录入</p>
      </div>

      <div v-else class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div
          v-for="q in items"
          :key="q.id"
          @click="openDetail(q)"
          class="group relative cursor-pointer overflow-hidden rounded-[2rem] border bg-white/80 p-6 shadow-sm backdrop-blur-md hover:-translate-y-1.5 hover:shadow-2xl dark:bg-[#0A0A0F]/60"
          :class="selectedIds.has(q.id) ? 'border-blue-500 ring-1 ring-blue-500/50 shadow-blue-500/10' : 'border-slate-200/60 dark:border-white/10 hover:border-blue-400/40'"
        >
          <!-- 学科状态条 -->
          <div class="absolute left-0 top-0 h-full w-1.5 opacity-80"
            :class="q.subject === '数学' ? 'bg-blue-500' : q.subject === '物理' ? 'bg-indigo-600' : 'bg-emerald-500'">
          </div>

          <div class="flex items-start gap-5">
            <!-- 勾选框：科技感微动效 -->
            <button class="mt-1 shrink-0" @click.stop="toggleSelect(q.id)">
              <div class="flex h-6 w-6 items-center justify-center rounded-lg border-2"
                :class="selectedIds.has(q.id) ? 'border-blue-500 bg-blue-500 text-white rotate-12 scale-110 shadow-lg shadow-blue-500/40' : 'border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-900'">
                <i v-show="selectedIds.has(q.id)" class="fa-solid fa-check text-[11px] font-black"></i>
              </div>
            </button>

            <div class="min-w-0 flex-1">
              <!-- 顶部标签云 -->
              <div class="mb-4 flex flex-wrap items-center gap-2">
                <span class="rounded-lg bg-slate-100 px-2.5 py-1 text-[10px] font-black uppercase tracking-widest text-slate-500 dark:bg-white/5 dark:text-slate-400">
                  {{ q.question_type }}
                </span>
                <span v-for="tag in (q.knowledge_tags || [])" :key="tag" class="inline-flex items-center gap-1.5 rounded-lg border border-blue-500/20 bg-blue-500/5 px-2.5 py-1 text-[10px] font-black text-blue-600 dark:text-blue-300">
                  <span class="h-1 w-1 rounded-full bg-blue-500"></span> {{ tag }}
                </span>
                <span class="ml-auto flex items-center gap-1 rounded-lg px-2.5 py-1 text-[10px] font-black uppercase tracking-wider"
                  :class="q.review_status === '已掌握' ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400' : q.review_status === '复习中' ? 'bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-400' : 'bg-orange-50 text-orange-600 dark:bg-orange-500/10 dark:text-orange-400'">
                  <i class="fa-solid" :class="q.review_status === '已掌握' ? 'fa-circle-check' : q.review_status === '复习中' ? 'fa-spinner' : 'fa-clock'"></i>
                  {{ q.review_status || '待复习' }}
                </span>
              </div>
              
              <!-- 题目摘要 -->
              <p class="line-clamp-3 text-sm font-bold leading-relaxed text-slate-700 group-hover:text-slate-900 dark:text-slate-300 dark:group-hover:text-white">
                {{ getSummary(q) }}
              </p>

              <!-- 底部元数据 -->
              <div class="mt-6 flex items-center justify-between border-t border-slate-50 pt-4 text-[10px] font-black uppercase tracking-widest text-slate-400 dark:border-white/5">
                <div class="flex items-center gap-3">
                  <span class="font-mono">编号 #{{ q.id }}</span>
                  <span v-if="q.answer" class="flex items-center gap-1 rounded-md bg-emerald-50 px-1.5 py-0.5 font-bold normal-case tracking-normal text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400">
                    <i class="fa-solid fa-circle-check"></i>答案
                  </span>
                  <span v-if="q.user_answer" class="flex items-center gap-1 rounded-md bg-blue-50 px-1.5 py-0.5 font-bold normal-case tracking-normal text-blue-600 dark:bg-blue-500/10 dark:text-blue-400">
                    <i class="fa-solid fa-pen-to-square"></i>笔记
                  </span>
                </div>
                <span class="flex items-center gap-1.5"><i class="fa-regular fa-calendar-alt text-blue-500"></i> {{ q.created_at ? new Date(q.created_at).toLocaleDateString() : '未知' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页控制：浮动微拟物风格 -->
      <div v-if="totalPages > 1" class="mt-16 flex items-center justify-center gap-2">
        <button @click="goPage(page - 1)" :disabled="page <= 1" class="btn-secondary h-11 w-11 p-0 disabled:opacity-30">
          <i class="fa-solid fa-chevron-left"></i>
        </button>
        <div class="flex items-center gap-1.5 rounded-2xl bg-white/50 p-1.5 shadow-sm dark:bg-white/5">
          <template v-for="(p, i) in pageButtons" :key="i">
            <span v-if="p === '...'" class="flex w-8 justify-center font-bold text-slate-400">...</span>
            <button v-else @click="goPage(p)" 
              class="h-9 min-w-[36px] rounded-xl text-xs font-black"
              :class="p === page ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30' : 'text-slate-500 hover:bg-white dark:hover:bg-white/10'">
              {{ p }}
            </button>
          </template>
        </div>
        <button @click="goPage(page + 1)" :disabled="page >= totalPages" class="btn-secondary h-11 w-11 p-0 disabled:opacity-30">
          <i class="fa-solid fa-chevron-right"></i>
        </button>
      </div>
    </div>

    <!-- 底部悬浮操作胶囊：导出专用 -->
    <Transition enter-active-class="transition duration-500 ease-out" enter-from-class="translate-y-20 opacity-0" enter-to-class="translate-y-0 opacity-100" leave-active-class="transition duration-300 ease-in" leave-from-class="translate-y-0 opacity-100" leave-to-class="translate-y-20 opacity-0">
      <div v-if="selectedIds.size" class="fixed bottom-24 left-1/2 z-50 -translate-x-1/2 md:bottom-10">
        <div class="flex items-center gap-6 rounded-full border border-white/20 bg-slate-900/90 px-8 py-4 shadow-[0_20px_50px_rgba(0,0,0,0.3)] backdrop-blur-2xl dark:bg-slate-800/80">
          <div class="flex items-center gap-3 border-r border-white/10 pr-6">
            <div class="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500 font-mono text-xs font-black text-white outline outline-4 outline-blue-500/20">
              {{ selectedIds.size }}
            </div>
            <span class="text-sm font-black tracking-widest text-white uppercase">已选中</span>
          </div>
          <div class="flex items-center gap-4">
            <button @click="doExport" class="btn-primary h-10 px-6 text-xs font-black shadow-lg shadow-blue-500/40">
              <i class="fa-solid fa-file-export mr-2"></i> 生成复习卷
            </button>
            <button @click="clearSelection" class="text-xs font-black tracking-widest text-slate-400 hover:text-white transition-colors">
              清除
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <QuestionDetailModal
      :open="detailOpen"
      :question="detailQuestion"
      @close="closeDetail"
      @open-image="(src) => emit('open-image', src)"
      @deleted="onDeleted"
      @answer-saved="onAnswerSaved"
      @review-status-changed="onReviewStatusChanged"
      @push-toast="(type, msg) => emit('push-toast', type, msg)"
      @start-chat="(q) => emit('start-chat', q)"
    />
  </div>
</template>

<style scoped>
/* 列表入场动画 */
.container {
  animation: vaultEntry 0.8s cubic-bezier(0.2, 0, 0, 1) both;
}
@keyframes vaultEntry {
  from { opacity: 0; transform: scale(0.98) translateY(20px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

/* 知识点标签墙动画 */
@keyframes tagPopIn {
  0% { opacity: 0; transform: scale(0.85) translateY(8px); }
  100% { opacity: 1; transform: scale(1) translateY(0); }
}
.tag-batch-active .bento-tag {
  opacity: 0;
  animation: tagPopIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>