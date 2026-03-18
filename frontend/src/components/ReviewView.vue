<script setup>
import { ref, reactive, watch, nextTick, onBeforeUnmount, computed } from 'vue'
import * as api from '../api.js'
import { getQuestionSnippet, typesetMath as _typesetMath } from '../utils.js'
import QuestionDetailModal from './QuestionDetailModal.vue'
import AiAnalysisModal from './AiAnalysisModal.vue'
import CustomSelect from './CustomSelect.vue'
import PageHeader from './PageHeader.vue'

const answerEditId = ref(null)
const answerEditField = ref('')
const answerEditDraft = ref('')
const answerEditSaving = ref(false)

const props = defineProps({
  theme: { type: String, default: 'light' },
  visible: { type: Boolean, default: false },
})

const emit = defineEmits(['go-workspace', 'push-toast', 'open-image', 'start-chat'])

// ---- 学科筛选 ----
const selectedSubject = ref('')
const subjects = ref([])

// ---- 待复习题目列表 ----
const reviewItems = ref([])
const reviewTotal = ref(0)
const reviewLoading = ref(false)

// ---- 详情弹窗 ----
const detailOpen = ref(false)
const detailQuestion = ref(null)

// ---- AI 分析 ----
const selectMode = ref(false)
const selectedIds = reactive(new Set())
const aiModalOpen = ref(false)
const aiAnalysisResult = ref(null)
const aiAnalyzing = ref(false)

// ---- 数据加载 ----
const loadSubjects = async () => {
  try {
    const data = await api.fetchDashboardStats()
    subjects.value = data?.subjects || []
  } catch (_) {}
}

const loadReviewItems = async () => {
  reviewLoading.value = true
  try {
    const params = { review_status: '待复习', page: 1, page_size: 20 }
    if (selectedSubject.value) params.subject = selectedSubject.value
    const data = await api.fetchErrorBank(params)
    reviewItems.value = data.items || []
    reviewTotal.value = data.total || 0
  } catch (e) {
    emit('push-toast', 'error', '加载待复习题目失败')
  } finally {
    reviewLoading.value = false
    typesetMath()
  }
}

const loadAll = () => { loadSubjects(); loadReviewItems() }

watch(selectedSubject, () => { loadReviewItems() })

// ---- 题目操作 ----
const getSummary = (q) => getQuestionSnippet(q)

const typesetMath = async () => {
  await nextTick()
  await _typesetMath()
}

const openDetail = (q) => { detailQuestion.value = q; detailOpen.value = true }
const closeDetail = () => { detailOpen.value = false; detailQuestion.value = null }

const quickMarkStatus = async (q, status) => {
  try {
    const data = await api.updateReviewStatus(q.id, status)
    q.review_status = data.review_status
    emit('push-toast', 'success', `已标记为「${status}」`)
    if (status !== '待复习') {
      reviewItems.value = reviewItems.value.filter(x => x.id !== q.id)
      reviewTotal.value = Math.max(0, reviewTotal.value - 1)
    }
  } catch (e) {
    emit('push-toast', 'error', '更新状态失败')
  }
}

const onDeleted = (id) => {
  reviewItems.value = reviewItems.value.filter(q => q.id !== id)
  reviewTotal.value = Math.max(0, reviewTotal.value - 1)
  closeDetail()
}

const onAnswerSaved = (id, answer, updatedAt) => {
  const q = reviewItems.value.find(x => x.id === id)
  if (q) { q.user_answer = answer; q.updated_at = updatedAt }
}

const startInlineEdit = (q, field) => {
  answerEditId.value = q.id
  answerEditField.value = field
  answerEditDraft.value = q[field] || ''
}
const cancelInlineEdit = () => { answerEditId.value = null }
const saveInlineEdit = async () => {
  if (answerEditSaving.value) return
  const q = reviewItems.value.find(x => x.id === answerEditId.value)
  if (!q) return
  answerEditSaving.value = true
  try {
    if (answerEditField.value === 'answer') {
      await api.saveQuestionAnswer(q.id, answerEditDraft.value)
      q.answer = answerEditDraft.value
    } else {
      await api.saveAnswer(q.id, answerEditDraft.value)
      q.user_answer = answerEditDraft.value
    }
    answerEditId.value = null
    emit('push-toast', 'success', '已保存')
  } catch (e) {
    emit('push-toast', 'error', '保存失败')
  } finally {
    answerEditSaving.value = false
  }
}

const onReviewStatusChanged = (id, status, updatedAt) => {
  const q = reviewItems.value.find(x => x.id === id)
  if (q) { q.review_status = status; q.updated_at = updatedAt }
  if (status !== '待复习') {
    reviewItems.value = reviewItems.value.filter(x => x.id !== id)
    reviewTotal.value = Math.max(0, reviewTotal.value - 1)
  }
}

// ---- AI 分析 ----
const toggleSelectMode = () => {
  selectMode.value = !selectMode.value
  if (!selectMode.value) selectedIds.clear()
}

const toggleSelect = (id) => {
  if (selectedIds.has(id)) selectedIds.delete(id)
  else selectedIds.add(id)
}

const selectAllReview = () => {
  for (const q of reviewItems.value) selectedIds.add(q.id)
}

const startAiAnalysis = async () => {
  if (!selectedIds.size) {
    emit('push-toast', 'error', '请先选择要分析的题目')
    return
  }
  aiAnalyzing.value = true
  aiModalOpen.value = true
  aiAnalysisResult.value = null
  try {
    const data = await api.requestAiAnalysis(Array.from(selectedIds))
    aiAnalysisResult.value = data.analysis
  } catch (e) {
    emit('push-toast', 'error', 'AI 分析失败: ' + (e instanceof Error ? e.message : String(e)))
    aiModalOpen.value = false
  } finally {
    aiAnalyzing.value = false
  }
}

const closeAiModal = () => {
  aiModalOpen.value = false
  aiAnalysisResult.value = null
}

// ---- 生命周期 ----
watch(() => props.visible, (v) => {
  if (v) loadAll()
})
</script>

<template>
  <div class="relative h-full overflow-y-auto custom-scrollbar">
    <div class="container relative z-10 mx-auto max-w-6xl px-4 py-8 sm:px-8">
      <!-- 页面标题 -->
      <div class="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <PageHeader
          badge="复习中心"
          badge-icon="fa-solid fa-clock"
          badge-color="orange"
          title="待复习题目"
          subtitle="及时复习，巩固薄弱知识点"
          subtitle-icon="fa-solid fa-rotate text-orange-500"
        />
        <div class="flex items-center gap-3">
          <CustomSelect v-if="subjects.length" v-model="selectedSubject" :options="subjects" placeholder="全部学科" width-class="min-w-[140px]" />
          <button @click="emit('go-workspace')" class="btn-primary group h-11 px-8 shadow-xl shadow-blue-500/20">
            <i class="fa-solid fa-plus-circle transition-transform group-hover:rotate-90"></i> 录入新题目
          </button>
        </div>
      </div>

      <!-- 操作栏 -->
      <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h3 class="flex items-center gap-2 text-lg font-black text-slate-900 dark:text-white">
          <i class="fa-solid fa-list-check text-indigo-500"></i> 题目列表
          <span v-if="reviewTotal" class="ml-2 rounded-full bg-orange-100 px-2.5 py-0.5 text-xs font-bold text-orange-600 dark:bg-orange-500/10 dark:text-orange-400">{{ reviewTotal }}</span>
        </h3>
        <div v-if="reviewItems.length" class="flex items-center gap-2">
          <button @click="toggleSelectMode"
            class="rounded-lg border px-3 py-1.5 text-xs font-bold"
            :class="selectMode ? 'border-blue-500 bg-blue-50 text-blue-600 dark:border-blue-400/30 dark:bg-blue-500/10 dark:text-blue-400' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:bg-white/5 dark:text-slate-400'">
            <i class="fa-solid mr-1" :class="selectMode ? 'fa-xmark' : 'fa-list-check'"></i>
            {{ selectMode ? '取消选择' : '选择题目' }}
          </button>
          <template v-if="selectMode">
            <button @click="selectAllReview" class="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
              全选
            </button>
            <button @click="startAiAnalysis" :disabled="!selectedIds.size || aiAnalyzing"
              class="rounded-lg bg-gradient-to-r from-indigo-500 to-blue-600 px-4 py-1.5 text-xs font-bold text-white shadow-md shadow-indigo-500/20 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed">
              <i class="fa-solid fa-wand-magic-sparkles mr-1" :class="{ 'animate-spin': aiAnalyzing }"></i>
              AI 错题分析 <span v-if="selectedIds.size">({{ selectedIds.size }})</span>
            </button>
          </template>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="reviewLoading" class="flex justify-center py-16">
        <div class="h-12 w-12 animate-spin rounded-full border-4 border-blue-500/20 border-t-blue-500"></div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!reviewItems.length" class="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50/50 py-20 dark:border-white/5 dark:bg-white/5">
        <i class="fa-solid fa-circle-check mb-4 text-4xl text-emerald-400"></i>
        <p class="text-lg font-black text-slate-900 dark:text-white">全部搞定了</p>
        <p class="mt-1 text-sm text-slate-500">没有待复习的题目，继续保持</p>
      </div>

      <!-- 题目列表 -->
      <div v-else class="space-y-4">
        <div v-for="q in reviewItems" :key="q.id"
          @click="selectMode ? toggleSelect(q.id) : openDetail(q)"
          class="group cursor-pointer rounded-2xl border border-slate-200/60 bg-white/80 p-5 shadow-sm backdrop-blur-md hover:-translate-y-0.5 hover:shadow-lg dark:border-white/10 dark:bg-white/[0.03]"
          :class="{ 'ring-2 ring-indigo-500/50 border-indigo-300 dark:border-indigo-500/40': selectMode && selectedIds.has(q.id) }">
          <div class="flex items-start gap-4">
            <div v-if="selectMode" class="flex shrink-0 items-center pt-1" @click.stop="toggleSelect(q.id)">
              <div class="flex h-5 w-5 items-center justify-center rounded-md border-2"
                :class="selectedIds.has(q.id) ? 'border-indigo-500 bg-indigo-500 text-white' : 'border-slate-300 dark:border-slate-600'">
                <i v-if="selectedIds.has(q.id)" class="fa-solid fa-check text-[10px]"></i>
              </div>
            </div>
            <div class="min-w-0 flex-1">
              <div class="mb-3 flex flex-wrap items-center gap-2">
                <span v-if="q.subject" class="rounded-lg bg-blue-50 px-2.5 py-1 text-[10px] font-black text-blue-600 dark:bg-blue-500/10 dark:text-blue-300">{{ q.subject }}</span>
                <span class="rounded-lg bg-slate-100 px-2.5 py-1 text-[10px] font-black uppercase tracking-widest text-slate-500 dark:bg-white/5 dark:text-slate-400">{{ q.question_type }}</span>
                <span v-for="tag in (q.knowledge_tags || []).slice(0, 3)" :key="tag" class="rounded-lg border border-indigo-500/20 bg-indigo-500/5 px-2 py-0.5 text-[10px] font-bold text-indigo-600 dark:text-indigo-300">{{ tag }}</span>
                <span class="ml-auto text-[10px] font-bold text-slate-400">{{ q.created_at ? new Date(q.created_at).toLocaleDateString() : '' }}</span>
              </div>
              <p class="line-clamp-2 text-sm font-bold leading-relaxed text-slate-700 group-hover:text-slate-900 dark:text-slate-300 dark:group-hover:text-white">{{ getSummary(q) }}</p>

              <div class="mt-3 flex flex-wrap items-center gap-2 text-[10px]" @click.stop>
                <span v-if="q.answer" class="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-0.5 font-bold text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400">
                  <i class="fa-solid fa-circle-check"></i>已录入答案
                </span>
                <button v-else @click="startInlineEdit(q, 'answer')" class="inline-flex items-center gap-1 rounded-md border border-dashed border-emerald-300 px-2 py-0.5 font-bold text-emerald-500 hover:bg-emerald-50 dark:border-emerald-500/30 dark:hover:bg-emerald-500/10">
                  <i class="fa-solid fa-plus"></i>录入答案
                </button>
                <span v-if="q.user_answer" class="inline-flex items-center gap-1 rounded-md bg-blue-50 px-2 py-0.5 font-bold text-blue-600 dark:bg-blue-500/10 dark:text-blue-400">
                  <i class="fa-solid fa-pen-to-square"></i>已记笔记
                </span>
                <button v-else @click="startInlineEdit(q, 'user_answer')" class="inline-flex items-center gap-1 rounded-md border border-dashed border-blue-300 px-2 py-0.5 font-bold text-blue-500 hover:bg-blue-50 dark:border-blue-500/30 dark:hover:bg-blue-500/10">
                  <i class="fa-solid fa-plus"></i>记笔记
                </button>
              </div>

              <div v-if="answerEditId === q.id" class="mt-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-white/10 dark:bg-slate-800" @click.stop>
                <div class="mb-2 text-[10px] font-black uppercase tracking-widest" :class="answerEditField === 'answer' ? 'text-emerald-600 dark:text-emerald-400' : 'text-blue-600 dark:text-blue-400'">
                  {{ answerEditField === 'answer' ? '正确答案' : '我的笔记' }}
                </div>
                <textarea v-model="answerEditDraft" rows="3" :placeholder="answerEditField === 'answer' ? '输入正确答案/解析…' : '记录错因或心得…'"
                  class="w-full resize-none rounded-lg border border-slate-200/80 bg-slate-50 px-3 py-2 font-mono text-xs text-slate-800 placeholder-slate-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-white/10 dark:bg-slate-900 dark:text-slate-200"></textarea>
                <div class="mt-2 flex justify-end gap-2">
                  <button @click="cancelInlineEdit" class="rounded-lg px-3 py-1 text-[10px] font-bold text-slate-500 hover:text-slate-700 dark:text-slate-400">取消</button>
                  <button @click="saveInlineEdit" :disabled="answerEditSaving"
                    class="rounded-lg px-3 py-1 text-[10px] font-bold text-white disabled:opacity-50"
                    :class="answerEditField === 'answer' ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-blue-500 hover:bg-blue-600'">
                    {{ answerEditSaving ? '保存中…' : '保存' }}
                  </button>
                </div>
              </div>
            </div>
            <div class="flex shrink-0 gap-2" @click.stop>
              <div class="group/tip relative">
                <button @click="quickMarkStatus(q, '复习中')" class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-1.5 text-[10px] font-black text-amber-600 hover:bg-amber-100 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-400">
                  <i class="fa-solid fa-spinner mr-1"></i>复习中
                </button>
                <span class="pointer-events-none absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-600/90 px-2 py-0.5 text-[10px] font-semibold text-white opacity-0 shadow-sm backdrop-blur-sm transition-opacity group-hover/tip:opacity-100 dark:bg-slate-700/90">
                  标记为复习中
                  <span class="absolute -bottom-1 left-1/2 -translate-x-1/2 border-[3px] border-transparent border-t-slate-600/90 dark:border-t-slate-700/90"></span>
                </span>
              </div>
              <div class="group/tip relative">
                <button @click="quickMarkStatus(q, '已掌握')" class="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-[10px] font-black text-emerald-600 hover:bg-emerald-100 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-400">
                  <i class="fa-solid fa-circle-check mr-1"></i>已掌握
                </button>
                <span class="pointer-events-none absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-600/90 px-2 py-0.5 text-[10px] font-semibold text-white opacity-0 shadow-sm backdrop-blur-sm transition-opacity group-hover/tip:opacity-100 dark:bg-slate-700/90">
                  标记为已掌握
                  <span class="absolute -bottom-1 left-1/2 -translate-x-1/2 border-[3px] border-transparent border-t-slate-600/90 dark:border-t-slate-700/90"></span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
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

    <!-- AI 分析弹窗 -->
    <AiAnalysisModal
      :open="aiModalOpen"
      :loading="aiAnalyzing"
      :analysis="aiAnalysisResult"
      @close="closeAiModal"
    />
  </div>
</template>

<style scoped>
.container {
  animation: reviewEntry 0.8s cubic-bezier(0.2, 0, 0, 1) both;
}
@keyframes reviewEntry {
  from { opacity: 0; transform: scale(0.98) translateY(20px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
</style>
