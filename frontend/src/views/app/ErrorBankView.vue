<script setup>
/**
 * ErrorBankView.vue
 * 错题库工作台：左侧题目列表 + 中间题目详情 + 右侧学习分析。
 *
 * 第一版只使用现有后端能力：错题查询、筛选、统计、复习状态和 AI 分析占位接口。
 */
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import {
  typesetMath as _typesetMath,
} from '@/utils/index.js'
import { useSelectableList } from '@/composables/useSelectableList.js'
import { useErrorBankActions } from '@/composables/useErrorBankActions.js'
import { useErrorBankQuery } from '@/composables/useErrorBankQuery.js'
import { useErrorBankStats } from '@/composables/useErrorBankStats.js'
import ContentPanel from '@/components/features/app/layout/ContentPanel.vue'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseStat from '@/components/base/BaseStat.vue'
import ErrorLearningAside from '@/components/features/app/error-bank/ErrorLearningAside.vue'
import ErrorQuestionFinderAside from '@/components/features/app/error-bank/ErrorQuestionFinderAside.vue'
import ErrorQuestionRecommendAside from '@/components/features/app/error-bank/ErrorQuestionRecommendAside.vue'
import ErrorQuestionDetailPanel from '@/components/features/app/error-bank/ErrorQuestionDetailPanel.vue'
import ErrorQuestionListPanel from '@/components/features/app/error-bank/ErrorQuestionListPanel.vue'
import EditNoteDialog from '@/components/features/app/question/EditNoteDialog.vue'
import QuestionDetailModal from '@/components/features/app/question/QuestionDetailModal.vue'
import SelectionPanel from '@/components/features/app/workspace/SelectionPanel.vue'
import { useToast } from '@/composables/useToast.js'
import { useImageModal } from '@/composables/useImageModal.js'
import { useWorkspaceNav } from '@/composables/useWorkspaceNav.js'
import { useChatSession } from '@/composables/useChatSession.js'
import { useProjects } from '@/composables/useProjects.js'

defineProps({
  embedded: { type: Boolean, default: false },
})

const { pushToast } = useToast()
const { openModal } = useImageModal()
const { currentView } = useWorkspaceNav()
const { openChat } = useChatSession()
const { activeQuestionProjectId, questionProjects, loadProjects } = useProjects()
const hasQuestionProject = computed(() => questionProjects.value.length > 0)

const activeTab = ref('analysis')
const workbenchView = ref('list')
const statsCollapsed = ref(false)
const showRecommend = ref(false)

const { selectMode, selectedIds, toggleSelectMode, toggleSelect, clearSelection } = useSelectableList()

const detailTabs = [
  { value: 'analysis', label: 'AI 解析', icon: 'fa-wand-magic-sparkles' },
  { value: 'answer', label: '答案解析', icon: 'fa-circle-check' },
  { value: 'note', label: '作答记录', icon: 'fa-camera' },
]

const rootEl = ref(null)
const typesetMath = async () => {
  await nextTick()
  await _typesetMath(rootEl.value || undefined)
}

const {
  filters,
  page,
  pageSize,
  items,
  total,
  grandTotal,
  totalPages,
  loading,
  subjects,
  questionTypes,
  tagNames,
  selectedTags,
  activeQuestionId,
  activeQuestion,
  contentBlocks,
  optionList,
  knowledgeTags,
  reviewStatusOptions,
  doQuery,
  loadFilters,
  refreshTags,
  debouncedQuery,
  resetFilters,
  goPage,
  dispose: disposeQuery,
} = useErrorBankQuery({ activeQuestionProjectId, pushToast, typesetMath })

const { statsCards, loadStats } = useErrorBankStats({ activeQuestionProjectId, grandTotal, total })

const {
  dialogOpen,
  dialogField,
  dialogQuestion,
  dialogSaving,
  detailOpen,
  detailQuestion,
  aiLoading,
  aiSummary,
  openDetail,
  openEditDialog,
  onDialogSave,
  quickMarkStatus,
  doDelete,
  doExport,
  requestAnalysis,
  startPractice,
  clearAiAnalysis,
} = useErrorBankActions({
  items,
  total,
  grandTotal,
  activeQuestionId,
  selectedIds,
  activeQuestion,
  activeTab,
  workbenchView,
  pushToast,
  typesetMath,
  loadStats,
})

const errorPatternRows = computed(() => {
  const tags = knowledgeTags.value.slice(0, 4)
  if (!tags.length) {
    return [
      { label: '基础概念不稳', percent: 48, color: 'bg-orange-400' },
      { label: '计算过程失误', percent: 32, color: 'bg-blue-400' },
      { label: '审题信息遗漏', percent: 20, color: 'bg-emerald-400' },
    ]
  }
  return tags.map((tag, idx) => ({
    label: tag,
    percent: Math.max(12, 48 - idx * 10),
    color: ['bg-orange-400', 'bg-blue-400', 'bg-emerald-400', 'bg-violet-400'][idx] || 'bg-slate-400',
  }))
})

/**
 * 选择题目后同步详情和分析区域。
 */
const selectQuestion = async (q) => {
  if (!q) return
  activeQuestionId.value = q.id
  activeTab.value = 'analysis'
  clearAiAnalysis()
  await nextTick()
  await typesetMath()
}

const handleQuestionClick = async (q) => {
  if (selectMode.value) toggleSelect(q.id)
  else {
    workbenchView.value = 'detail'
    await selectQuestion(q)
  }
}

const handleFinderSelect = async (q) => {
  workbenchView.value = 'detail'
  await selectQuestion(q)
}

const toggleRecommendPanel = () => {
  showRecommend.value = !showRecommend.value
}

const handleRecommendSelect = async (q) => {
  workbenchView.value = 'detail'
  await selectQuestion(q)
}

watch(() => [filters.subject, filters.knowledge_tag, filters.question_type, filters.review_status], () => debouncedQuery())
watch(() => filters.keyword, () => debouncedQuery(500))
watch(() => filters.subject, async () => {
  filters.knowledge_tag = ''
  selectedTags.clear()
  try { await refreshTags() } catch (_) { }
})
watch(activeQuestionProjectId, async () => {
  workbenchView.value = 'list'
  resetFilters()
  await Promise.all([loadFilters(), loadStats()])
})
watch(activeQuestion, async () => {
  await typesetMath()
}, { flush: 'post' })

onMounted(async () => {
  await Promise.all([loadFilters(), loadStats(), doQuery()])
})

onBeforeUnmount(() => {
  disposeQuery()
})

const onDetailDeleted = () => {
  doQuery()
  loadProjects()
}

defineExpose({
  refresh: doQuery,
  toggleSelectMode,
})
</script>

<template>
  <div ref="rootEl" class="contents">
  <component
    :is="embedded ? 'div' : ContentPanel"
    :title="embedded ? undefined : '错题库'"
    :class="embedded ? 'flex h-full min-h-0 flex-col overflow-hidden p-4' : ''"
  >
    <template v-if="!embedded" #toolbar>
      <BaseButton size="sm" variant="primary" @click="currentView = 'workspace'">
        <i class="fa-solid fa-plus"></i>
        录入题目
      </BaseButton>
    </template>

    <div class="flex h-full min-h-0 flex-col gap-3 overflow-hidden">
      <!-- 顶部统计卡片 -->
      <div>
        <button
          @click="statsCollapsed = !statsCollapsed"
          class="mb-2 flex items-center gap-1.5 text-xs font-medium text-slate-400 transition-colors hover:text-slate-600 dark:hover:text-slate-300"
        >
          <i class="fa-solid text-[10px] transition-transform duration-200" :class="statsCollapsed ? 'fa-chevron-right' : 'fa-chevron-down'"></i>
          {{ statsCollapsed ? '展开统计' : '收起统计' }}
        </button>
        <Transition name="collapse">
          <div v-show="!statsCollapsed" class="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
            <BaseStat
              v-for="card in statsCards"
              :key="card.label"
              :label="card.label"
              :value="card.value"
              :suffix="card.suffix"
              :hint="card.hint"
              :icon="card.icon"
              :tone="card.tone"
            />
          </div>
        </Transition>
      </div>

      <!-- 主体：列表/详情主从切换 + 右侧学习分析 -->
      <div class="grid min-h-0 flex-1 gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(16rem,0.34fr)]">
        <div class="flex min-h-0 flex-col gap-3">
          <ErrorQuestionListPanel
            v-if="workbenchView === 'list'"
            class="h-full min-h-0"
            :filters="filters"
            :review-status-options="reviewStatusOptions"
            :tag-names="tagNames"
            :question-types="questionTypes"
            :subjects="subjects"
            :items="items"
            :total="total"
            :page="page"
            :page-size="pageSize"
            :total-pages="totalPages"
            :loading="loading"
            :active-question-id="activeQuestion?.id"
            :select-mode="selectMode"
            :selected-ids="selectedIds"
            :has-question-project="hasQuestionProject"
            @toggle-select-mode="toggleSelectMode"
            @create-question="currentView = 'workspace'"
            @question-click="handleQuestionClick"
            @toggle-select="toggleSelect"
            @mark-status="quickMarkStatus"
            @edit-note="openEditDialog"
            @page-change="goPage"
          />

          <ErrorQuestionDetailPanel
            v-else
            v-model:active-tab="activeTab"
            class="h-full min-h-0"
            :question="activeQuestion"
            :content-blocks="contentBlocks"
            :option-list="optionList"
            :knowledge-tags="knowledgeTags"
            :detail-tabs="detailTabs"
            :ai-summary="aiSummary"
            @edit="openEditDialog"
            @delete="doDelete"
            @open-image="openModal"
            @open-detail="openDetail"
            @open-chat="openChat"
            @start-practice="startPractice"
            @back-to-list="workbenchView = 'list'"
            @open-recommend="toggleRecommendPanel"
          />
        </div>

        <!-- 右侧：列表态找题 / 详情态学习分析 -->
        <ErrorQuestionFinderAside
          v-if="workbenchView === 'list'"
          :project-id="activeQuestionProjectId"
          @select-question="handleFinderSelect"
          @error="(e) => pushToast('error', e instanceof Error ? e.message : 'AI 找题失败')"
        />
        <ErrorLearningAside
          v-if="workbenchView === 'detail' && !showRecommend"
          :knowledge-tags="knowledgeTags"
          :error-pattern-rows="errorPatternRows"
          :ai-summary="aiSummary"
          :ai-loading="aiLoading"
          @request-analysis="requestAnalysis"
        />
        <ErrorQuestionRecommendAside
          v-else-if="workbenchView === 'detail' && showRecommend"
          :current-question="activeQuestion"
          :all-items="items"
          @select-question="handleRecommendSelect"
        />
      </div>

      <SelectionPanel :visible="selectMode" :count="selectedIds.size" @export="doExport" @clear="clearSelection" />

      <EditNoteDialog :open="dialogOpen" :field="dialogField" :question="dialogQuestion" :value="dialogField === 'question'
        ? (dialogQuestion?.content_json?.filter(b => b.block_type === 'text').map(b => b.content).join('\n') || '')
        : (dialogQuestion?.[dialogField] || '')"
        :value-answer="dialogField === 'question' ? (dialogQuestion?.answer || '') : ''" :saving="dialogSaving"
        @close="dialogOpen = false" @save="onDialogSave" />

      <QuestionDetailModal :open="detailOpen" :question="detailQuestion" @close="detailOpen = false"
        @open-image="openModal" @deleted="onDetailDeleted" @push-toast="pushToast" @start-chat="openChat"
        @answer-saved="doQuery" @review-status-changed="doQuery" />
    </div>
  </component>
  </div>
</template>
