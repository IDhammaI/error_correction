<script setup>
/**
 * ErrorBankView.vue
 * 閿欓搴撳伐浣滃彴锛氬乏渚ч鐩垪琛?+ 涓棿棰樼洰璇︽儏 + 鍙充晶瀛︿範鍒嗘瀽銆?
 *
 * 绗竴鐗堝彧浣跨敤鐜版湁鍚庣鑳藉姏锛氶敊棰樻煡璇€佺瓫閫夈€佺粺璁°€佸涔犵姸鎬佸拰 AI 鍒嗘瀽鍗犱綅鎺ュ彛銆?
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
const { activeQuestionProjectId, questionProjects } = useProjects()
const hasQuestionProject = computed(() => questionProjects.value.length > 0)

const activeTab = ref('analysis')
const workbenchView = ref('list')
const statsCollapsed = ref(false)

const { selectMode, selectedIds, toggleSelectMode, toggleSelect, clearSelection } = useSelectableList()

const detailTabs = [
  { value: 'analysis', label: 'AI 解析', icon: 'fa-wand-magic-sparkles' },
  { value: 'answer', label: '答案解析', icon: 'fa-circle-check' },
  { value: 'note', label: '作答记录', icon: 'fa-camera' },
]

const typesetMath = async () => {
  await nextTick()
  await _typesetMath()
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
  pushToast,
  typesetMath,
  loadStats,
})

const errorPatternRows = computed(() => {
  const tags = knowledgeTags.value.slice(0, 4)
  if (!tags.length) {
    return [
      { label: '鍩虹姒傚康涓嶇ǔ', percent: 48, color: 'bg-orange-400' },
      { label: '璁＄畻杩囩▼澶辫', percent: 32, color: 'bg-blue-400' },
      { label: '瀹￠淇℃伅閬楁紡', percent: 20, color: 'bg-emerald-400' },
    ]
  }
  return tags.map((tag, idx) => ({
    label: tag,
    percent: Math.max(12, 48 - idx * 10),
    color: ['bg-orange-400', 'bg-blue-400', 'bg-emerald-400', 'bg-violet-400'][idx] || 'bg-slate-400',
  }))
})

/**
 * 閫夋嫨棰樼洰鍚庡悓姝ヨ鎯呭拰鍒嗘瀽鍖哄煙銆?
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

defineExpose({
  refresh: doQuery,
  toggleSelectMode,
})
</script>

<template>
  <component
    :is="embedded ? 'div' : ContentPanel"
    :title="embedded ? undefined : '错题库'"
    :class="embedded ? 'flex h-full min-h-0 flex-col overflow-hidden p-4' : ''"
  >
    <template v-if="!embedded" #toolbar>
      <BaseButton size="sm" variant="primary" @click="currentView = 'workspace'">
        <i class="fa-solid fa-plus"></i>
        褰曞叆棰樼洰
      </BaseButton>
    </template>

    <div class="flex h-full min-h-0 flex-col gap-4 overflow-hidden">
      <!-- 椤堕儴缁熻鍗＄墖 -->
      <div class="grid shrink-0 grid-cols-2 gap-3 lg:grid-cols-5">
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

      <!-- 涓讳綋锛氬垪琛?璇︽儏涓讳粠鍒囨崲 + 鍙充晶瀛︿範鍒嗘瀽 -->
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
          />
        </div>

        <!-- 鍙充晶锛氬垪琛ㄦ€佹壘棰?/ 璇︽儏鎬佸涔犲垎鏋?-->
        <ErrorQuestionFinderAside
          v-if="workbenchView === 'list'"
          :project-id="activeQuestionProjectId"
          @select-question="handleFinderSelect"
          @error="(e) => pushToast('error', e instanceof Error ? e.message : 'AI 鎵鹃澶辫触')"
        />
        <ErrorLearningAside
          v-else
          :knowledge-tags="knowledgeTags"
          :error-pattern-rows="errorPatternRows"
          :ai-summary="aiSummary"
          :ai-loading="aiLoading"
          @request-analysis="requestAnalysis"
        />
      </div>

      <SelectionPanel :visible="selectMode" :count="selectedIds.size" @export="doExport" @clear="clearSelection" />

      <EditNoteDialog :open="dialogOpen" :field="dialogField" :question="dialogQuestion" :value="dialogField === 'question'
        ? (dialogQuestion?.content_json?.filter(b => b.block_type === 'text').map(b => b.content).join('\n') || '')
        : (dialogQuestion?.[dialogField] || '')"
        :value-answer="dialogField === 'question' ? (dialogQuestion?.answer || '') : ''" :saving="dialogSaving"
        @close="dialogOpen = false" @save="onDialogSave" />

      <QuestionDetailModal :open="detailOpen" :question="detailQuestion" @close="detailOpen = false"
        @open-image="openModal" @deleted="doQuery" @push-toast="pushToast" @start-chat="openChat"
        @answer-saved="doQuery" @review-status-changed="doQuery" />
    </div>
  </component>
</template>
