<script setup>
/**
 * WorkspaceView.vue
 * 录入工作台 — 上传/擦除/OCR/分割/导出 全流程
 */
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from '@/composables/useToast.js'
import { useSystemStatus } from '@/composables/useSystemStatus.js'
import { useImageModal } from '@/composables/useImageModal.js'
import { useWorkspaceNav } from '@/composables/useWorkspaceNav.js'
import { useQuestionList } from '@/composables/useQuestionList.js'
import { useFileUpload } from '@/composables/useFileUpload.js'
import { useSplitPipeline } from '@/composables/useSplitPipeline.js'
import { useProjects } from '@/composables/useProjects.js'
import ContentPanel from '@/components/workspace/ContentPanel.vue'
import SelectionPanel from '@/components/workspace/SelectionPanel.vue'
import UploadStage from '@/components/workspace/UploadStage.vue'
import ReviewStage from '@/components/workspace/ReviewStage.vue'
import SplitHistory from '@/views/app/SplitHistoryView.vue'
import BaseModal from '@/components/base/BaseModal.vue'
import BaseButton from '@/components/base/BaseButton.vue'

const WORKSPACE_STATE_KEY = 'workspace_split_state_v1'

const route = useRoute()
const { pushToast } = useToast()
const { openModal } = useImageModal()
const { currentView } = useWorkspaceNav()
const { questionProjects, activeQuestionProjectId, setActiveProject } = useProjects()
const {
  statusLoading, statusError,
  providerOptions, hasConfiguredModel, statusPills,
  modelOptionsData, selectedLlmOptionId, selectedLlmOption, doFetchModelOptions
} = useSystemStatus()
const {
  questions, selectedIds,
  toggleQuestion, selectAll, deselectAll, reorderQuestions, typesetMath,
} = useQuestionList()

const props = defineProps({
  theme: { type: String, default: 'dark' },
})

// ── 步骤控制 ────────────────────────────────────────────
const step = ref(1)
const uploadMode = ref('exam')
const splitting = ref(false)
const splitCompleted = ref(false)
const showSplitHistory = ref(false)

const S = computed(() => {
  const off = eraseEnabled.value ? 1 : 0
  return { UPLOAD: 1, ERASE: 2, OCR: 2 + off, SPLIT: 3 + off, EXPORT: 4 + off }
})
const workspaceSteps = computed(() => {
  const labels = uploadMode.value === 'note'
    ? (eraseEnabled.value ? ['上传', '擦除', 'OCR', '整理', '保存'] : ['上传', 'OCR', '整理', '保存'])
    : (eraseEnabled.value ? ['上传', '擦除', 'OCR', '分割', '导出'] : ['上传', 'OCR', '分割', '导出'])
  return labels.map((label, i) => ({
    label,
    done: i + 1 < step.value,
    active: i + 1 === step.value,
  }))
})

// ── 文件上传 ────────────────────────────────────────────
const {
  uploadBusy, uploadReady, pendingFiles, pendingPreviewUrls,
  fileProgress, waitingKeys,
  enqueueUpload, removePendingFile, stopFakeProgress, doReset: _doReset,
} = useFileUpload(pushToast, S, questions, selectedIds, splitCompleted, splitting, uploadMode)

const splitEnabled = computed(() => !splitting.value && !splitCompleted.value && uploadReady.value && !uploadBusy.value && hasConfiguredModel.value)

const clearPersistedWorkspaceState = () => {
  try { localStorage.removeItem(WORKSPACE_STATE_KEY) } catch (_) { }
}

const savePersistedWorkspaceState = () => {
  const shouldPersist = splitCompleted.value && questions.value.length > 0
  if (!shouldPersist) {
    clearPersistedWorkspaceState()
    return
  }
  const payload = {
    step: step.value,
    splitCompleted: splitCompleted.value,
    questions: questions.value,
    selectedIds: Array.from(selectedIds),
    currentView: currentView.value,
    uploadMode: uploadMode.value,
    savedAt: Date.now(),
  }
  try {
    localStorage.setItem(WORKSPACE_STATE_KEY, JSON.stringify(payload))
  } catch (_) { }
}

const restorePersistedWorkspaceState = async () => {
  let raw = ''
  try { raw = localStorage.getItem(WORKSPACE_STATE_KEY) || '' } catch (_) { }
  if (!raw) return

  let state = null
  try { state = JSON.parse(raw) } catch (_) { }
  if (!state || !Array.isArray(state.questions) || state.questions.length === 0) return

  questions.value = state.questions
  selectedIds.clear()
  for (const id of (state.selectedIds || [])) selectedIds.add(id)
  splitCompleted.value = Boolean(state.splitCompleted)
  uploadMode.value = state.uploadMode === 'note' ? 'note' : 'exam'
  step.value = Number(state.step) || S.value.EXPORT
  currentView.value = 'workspace_review'
  await nextTick()
  setTimeout(() => { reviewStageRef.value?.triggerTypeset?.() }, 400)
}

const doReset = async () => {
  await _doReset(modelOptionsData, selectedLlmOptionId, step)
  clearPersistedWorkspaceState()
  step.value = S.value.UPLOAD
}

// ── 分割流水线 ──────────────────────────────────────────
const {
  eraseEnabled, eraseLoading, eraseImages, eraseDone,
  ocrLoading, ocrPages, ocrDone,
  startProcess, doErase, doOcr, doSplit, doSaveToDb,
} = useSplitPipeline(pushToast, currentView, step, S, uploadReady, splitting, splitCompleted, uploadMode, selectedLlmOption, questions, selectedIds, pendingFiles, typesetMath)

const reviewStageRef = ref(null)
const restoringWorkspaceState = ref(true)
const importDialogOpen = ref(false)
const importTargetProjectId = ref(null)
const importSaving = ref(false)
const hasReviewContent = computed(() => {
  if (eraseLoading.value) return true
  if (eraseDone.value) return true
  if (ocrLoading.value) return true
  if (ocrDone.value) return true
  if (splitting.value) return true
  if (splitCompleted.value && questions.value.length > 0) return true
  return false
})

const handleLoadRecord = (qs, record) => {
  questions.value = qs || []; selectedIds.clear()
  splitCompleted.value = true; step.value = S.value.EXPORT
  currentView.value = 'workspace_review'
  pushToast('success', `已加载「${record?.subject || '历史记录'}」的 ${qs.length} 道题目`)
  nextTick(() => typesetMath())
}

const handleBack = async () => {
  await doReset()
  eraseImages.value = []; eraseDone.value = false
  ocrPages.value = []; ocrDone.value = false
  currentView.value = 'workspace'
}

const openImportDialog = () => {
  if (!selectedIds.size) {
    pushToast('error', '请至少选择一道题目！')
    return
  }
  if (!questionProjects.value.length) {
    pushToast('error', '请先创建一个错题库')
    return
  }
  importTargetProjectId.value = activeQuestionProjectId.value || questionProjects.value[0]?.id || null
  importDialogOpen.value = true
}

const closeImportDialog = () => {
  if (importSaving.value) return
  importDialogOpen.value = false
}

const confirmImportToProject = async () => {
  if (!importTargetProjectId.value || importSaving.value) return
  importSaving.value = true
  try {
    const saved = await doSaveToDb(importTargetProjectId.value)
    if (saved) {
      setActiveProject(importTargetProjectId.value, 'question')
      importDialogOpen.value = false
    }
  } finally {
    importSaving.value = false
  }
}

// ── 键盘事件 ────────────────────────────────────────────
const onKeydown = (e) => {
  if (e.key === 'a' && (e.ctrlKey || e.metaKey) && questions.value.length) {
    e.preventDefault(); selectAll()
  }
}

// ── 视图切换 ────────────────────────────────────────────
watch(currentView, async (v) => {
  if (v === 'workspace_review') {
    // 首次挂载恢复期间先不做空态回退，避免 refresh 时路由在 review/workspace 间抖动。
    if (restoringWorkspaceState.value) return
    // 兜底：避免导航恢复到 review 路由但没有任何可展示数据，出现空白页。
    if (!hasReviewContent.value) {
      currentView.value = 'workspace'
      step.value = S.value.UPLOAD
      return
    }
    await nextTick()
    setTimeout(() => { reviewStageRef.value?.triggerTypeset?.() }, 650)
  }
}, { immediate: true })

watch(
  [questions, splitCompleted, step, currentView, uploadMode],
  () => savePersistedWorkspaceState(),
  { deep: true },
)

// ── 生命周期 ────────────────────────────────────────────
import { onMounted } from 'vue'
onMounted(async () => {
  document.addEventListener('keydown', onKeydown)
  // 检查 URL 参数，设置上传模式
  const mode = route.query.mode
  if (mode === 'note') {
    uploadMode.value = 'note'
  }
  try {
    await restorePersistedWorkspaceState()
  } finally {
    restoringWorkspaceState.value = false
  }
  if (currentView.value === 'workspace_review' && !hasReviewContent.value) {
    currentView.value = 'workspace'
    step.value = S.value.UPLOAD
  }
})
onBeforeUnmount(() => {
  stopFakeProgress()
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div class="h-full">
    <Transition name="flip" mode="out-in">
      <!-- 第一页：上传与分析 -->
      <ContentPanel v-if="currentView === 'workspace'" key="upload" title="智能录入与分析" :steps="workspaceSteps"
        :current-step="step - 1" :sidebar-open="showSplitHistory">
        <template #toolbar>
          <button @click="showSplitHistory = !showSplitHistory"
            class="inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
            :class="showSplitHistory
              ? 'bg-gray-200 dark:bg-white/[0.06] text-gray-900 dark:text-[#f7f8f8] border border-gray-300 dark:border-white/[0.12]'
              : 'border border-gray-200 dark:border-white/[0.08] bg-white dark:bg-white/[0.02] text-gray-700 dark:text-[#d0d6e0] hover:bg-gray-50 dark:hover:bg-white/[0.05] hover:border-gray-300 dark:hover:border-white/[0.12]'">
            <i class="fa-solid fa-clock-rotate-left text-[10px]"></i>
            分割历史
          </button>
        </template>

        <template #sidebar>
          <SplitHistory :theme="theme" :visible="showSplitHistory" @push-toast="pushToast" @open-image="openModal"
            @load-record="(r) => { handleLoadRecord(r); showSplitHistory = false }"
            @go-workspace="currentView = splitCompleted ? 'workspace_review' : 'workspace'" />
        </template>

        <UploadStage :upload-mode="uploadMode" :erase-enabled="eraseEnabled" :status-loading="statusLoading"
          :status-error="statusError" :status-pills="statusPills" :model-options-data="modelOptionsData"
          :selected-llm-option-id="selectedLlmOptionId" :has-configured-model="hasConfiguredModel"
          :splitting="splitting" :split-completed="splitCompleted" :pending-files="pendingFiles"
          :file-progress="fileProgress" :waiting-keys="waitingKeys" :upload-busy="uploadBusy"
          :upload-ready="uploadReady" :split-enabled="splitEnabled" @update:upload-mode="(v) => uploadMode = v"
          @update:erase-enabled="(v) => eraseEnabled = v"
          @update:selected-llm-option-id="(v) => selectedLlmOptionId = v" @upload="enqueueUpload"
          @remove-file="removePendingFile" @split="startProcess" />
      </ContentPanel>

      <!-- 第二页：解析结果核对 -->
      <ContentPanel v-else-if="currentView === 'workspace_review'" key="review"
        :title="eraseLoading ? '正在擦除...' : eraseDone && !ocrLoading && !ocrDone ? '擦除预览' : splitting ? '正在分割...' : ocrDone && !splitCompleted ? 'OCR 预览' : '题目数据核对'"
        :steps="workspaceSteps" :current-step="step - 1">
        <template #toolbar>
          <button @click="handleBack"
            class="group inline-flex items-center gap-2 rounded-md border border-gray-200 dark:border-white/[0.08] bg-white dark:bg-white/[0.02] px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-[#d0d6e0] hover:bg-gray-50 dark:hover:bg-white/[0.05] hover:border-gray-300 dark:hover:border-white/[0.12] transition-colors">
            <i class="fa-solid fa-arrow-left-long text-xs transition-transform group-hover:-translate-x-0.5"></i>
            返回
          </button>
          <template v-if="eraseDone && !ocrLoading && !ocrDone">
            <button @click="doErase"
              class="inline-flex items-center gap-1.5 rounded-md border border-gray-200 dark:border-white/[0.08] bg-white dark:bg-white/[0.02] px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-[#d0d6e0] hover:bg-gray-50 dark:hover:bg-white/[0.05] transition-colors">
              <i class="fa-solid fa-arrows-rotate text-[10px]"></i> 重新擦除
            </button>
            <button @click="doOcr"
              class="inline-flex items-center gap-1.5 rounded-md accent-bg px-3 py-1.5 text-xs font-medium text-white hover:bg-[rgb(var(--accent-hover-rgb))] transition-colors">
              <i class="fa-solid fa-check text-[10px]"></i> 确认，开始 OCR
            </button>
          </template>
          <template v-else-if="ocrDone && !splitCompleted && !splitting">
            <button @click="doOcr"
              class="inline-flex items-center gap-1.5 rounded-md border border-gray-200 dark:border-white/[0.08] bg-white dark:bg-white/[0.02] px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-[#d0d6e0] hover:bg-gray-50 dark:hover:bg-white/[0.05] transition-colors">
              <i class="fa-solid fa-arrows-rotate text-[10px]"></i> 重新识别
            </button>
            <button @click="doSplit"
              class="inline-flex items-center gap-1.5 rounded-md accent-bg px-3 py-1.5 text-xs font-medium text-white hover:bg-[rgb(var(--accent-hover-rgb))] transition-colors">
              <i class="fa-solid fa-check text-[10px]"></i> 确认并分割
            </button>
          </template>
        </template>

        <ReviewStage ref="reviewStageRef" :erase-loading="eraseLoading" :erase-done="eraseDone"
          :erase-images="eraseImages" :ocr-loading="ocrLoading" :ocr-done="ocrDone" :ocr-pages="ocrPages"
          :splitting="splitting" :split-completed="splitCompleted" :questions="questions" :selected-ids="selectedIds"
          :preview-url="pendingPreviewUrls[0]" @toggle-select="toggleQuestion" @select-all="selectAll"
          @deselect-all="deselectAll" @open-image="openModal" @reorder="reorderQuestions" />
      </ContentPanel>
    </Transition>

    <!-- 浮动选择面板 -->
    <SelectionPanel :visible="currentView === 'workspace_review'" :count="selectedIds.size" :show-export="false"
      :show-save="true" @save="openImportDialog" @clear="deselectAll" />

    <BaseModal :open="importDialogOpen" title="导入错题库" icon="fa-database" iconBg="accent-bg-soft"
      iconClass="accent-text" maxWidth="max-w-[30rem]" bodyClass="px-6 pb-3 pt-1" @close="closeImportDialog">
      <div class="space-y-3">
        <p class="text-sm text-slate-500 dark:text-[#8a8f98]">
          将 {{ selectedIds.size }} 道已选题目导入到：
        </p>
        <div class="max-h-64 space-y-2 overflow-y-auto pr-1 custom-scrollbar">
          <button v-for="project in questionProjects" :key="project.id" type="button"
            class="flex w-full items-center gap-3 rounded-lg border px-3 py-2.5 text-left transition-colors"
            :class="String(importTargetProjectId) === String(project.id)
              ? 'border-[rgb(var(--accent-rgb)/0.35)] bg-[rgb(var(--accent-rgb)/0.12)] text-[rgb(var(--accent-strong-rgb))] dark:text-[rgb(var(--accent-hover-rgb))]'
              : 'border-slate-200/70 bg-white/50 text-slate-600 hover:border-slate-300 hover:bg-slate-50 dark:border-white/[0.08] dark:bg-white/[0.03] dark:text-[#aeb6c2] dark:hover:bg-white/[0.05]'"
            @click="importTargetProjectId = project.id">
            <i class="fa-solid fa-database w-4 text-center text-xs"></i>
            <span class="min-w-0 flex-1 truncate text-sm font-medium">{{ project.name }}</span>
            <i v-if="String(importTargetProjectId) === String(project.id)" class="fa-solid fa-check text-xs"></i>
          </button>
        </div>
      </div>
      <template #footer>
        <BaseButton variant="secondary" size="sm" :disabled="importSaving" @click="closeImportDialog">
          取消
        </BaseButton>
        <BaseButton variant="primary" size="sm" :disabled="importSaving || !importTargetProjectId"
          @click="confirmImportToProject">
          {{ importSaving ? '导入中...' : '确认导入' }}
        </BaseButton>
      </template>
    </BaseModal>
  </div>
</template>
