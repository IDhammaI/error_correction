<script setup>
/**
 * WorkspaceView.vue
 * 工作台主容器 — 侧边栏导航 + 内容区视图切换
 */
import { computed, nextTick, onBeforeUnmount, onMounted, provide, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import { usePageTransition } from '@/composables/usePageTransition.js'
import { useTheme } from '@/composables/useTheme.js'
import { useImageModal } from '@/composables/useImageModal.js'
import { useWorkspaceToast } from '@/composables/useWorkspaceToast.js'
import { useSystemStatus } from '@/composables/useSystemStatus.js'
import { useSidebarIndicator } from '@/composables/useSidebarIndicator.js'
import { useAiChatSessions } from '@/composables/useAiChatSessions.js'
import { useQuestionList } from '@/composables/useQuestionList.js'
import { useFileUpload } from '@/composables/useFileUpload.js'
import { useSplitPipeline } from '@/composables/useSplitPipeline.js'
import { useWorkspaceNav } from '@/composables/useWorkspaceNav.js'
import { useChatSession } from '@/composables/useChatSession.js'
import BrandLogo from '@/components/base/BrandLogo.vue'
import ContentPanel from '@/components/workspace/ContentPanel.vue'
import StatusBar from '@/components/workspace/StatusBar.vue'
import StepIndicator from '@/components/workspace/StepIndicator.vue'
import FileList from '@/components/workspace/FileList.vue'
import FileUploader from '@/components/workspace/FileUploader.vue'
import QuestionList from '@/components/question/QuestionList.vue'
import ActionBar from '@/components/workspace/ActionBar.vue'
import SelectionPanel from '@/components/workspace/SelectionPanel.vue'
import SplitLoading from '@/components/workspace/SplitLoading.vue'
import ErasePreview from '@/components/workspace/ErasePreview.vue'
import OcrPreview from '@/components/workspace/OcrPreview.vue'
import SidebarNav from '@/components/workspace/SidebarNav.vue'
import ImageModal from '@/components/base/ImageModal.vue'
import ToastContainer from '@/components/base/ToastContainer.vue'
import Dashboard from '@/views/workspace/DashboardView.vue'
import ReviewView from '@/views/workspace/ReviewView.vue'
import ErrorBank from '@/views/workspace/ErrorBankView.vue'
import ChatView from '@/views/workspace/ChatView.vue'
import SettingsView from '@/views/workspace/SettingsView.vue'
import SplitHistory from '@/views/workspace/SplitHistoryView.vue'
import NoteView from '@/views/workspace/NoteView.vue'
import ChatPage from '@/views/workspace/ChatPageView.vue'

// ── Composables ─────────────────────────────────────────
const router = useRouter()
const { currentUser } = useAuth()
const { loading: globalLoading } = usePageTransition()
const { isDark, toggleTheme, initTheme } = useTheme()
const { toasts, pushToast } = useWorkspaceToast()
const { modalOpen, modalSrc, modalScale, openModal, closeModal } = useImageModal()
const {
  statusLoading, systemStatus, statusError, selectedModel,
  providerOptions, hasConfiguredModel, selectedProvider, statusPills,
  doFetchStatus,
} = useSystemStatus()
const {
  navRef, navBtnRefs, indicatorStyle, indicatorTransition,
  chatListRef, chatBtnRefs, chatIndicatorStyle, chatIndicatorTransition,
  updateIndicator: _updateIndicator,
} = useSidebarIndicator()
const {
  aiChatSessions, activeAiChatId,
  chatMenuOpenId, renamingChatId, renameText,
  loadAiChatSessions, createAiChat: _createAiChat, selectAiChat: _selectAiChat,
  onAiChatTitleUpdated, toggleChatMenu, closeChatMenu,
  startRenameChat, confirmRenameChat, deleteAiChat,
} = useAiChatSessions(pushToast)
const {
  questions, selectedIds, questionListRef,
  toggleQuestion, selectAll, deselectAll, reorderQuestions, typesetMath,
} = useQuestionList()
const {
  currentView, lastWorkspaceView, collapsedGroups, chatCollapsed,
  NAV_GROUPS, WORKSPACE_VIEWS, navigateToHome,
} = useWorkspaceNav()

provide('pushToast', pushToast)

// ── 认证 ────────────────────────────────────────────────
const theme = computed(() => isDark.value ? 'dark' : 'light')
const userMenuOpen = ref(false)

const handleLogout = async () => {
  try { await fetch('/api/auth/logout', { method: 'POST' }) } catch (_) {}
  currentUser.value = null
  router.push('/auth')
}

// ── 指示器更新 ──────────────────────────────────────────
const updateIndicator = (animate = true) => {
  _updateIndicator(currentView.value, activeAiChatId.value, NAV_GROUPS, collapsedGroups.value, animate)
}

watch(currentView, (v) => {
  if (WORKSPACE_VIEWS.has(v)) lastWorkspaceView.value = v
  nextTick(updateIndicator)
})
watch(collapsedGroups, () => {
  updateIndicator(false)
  nextTick(() => updateIndicator(false))
}, { deep: true })

// ── AI 独立对话包装 ────────────────────────────────────
const createAiChat = () => _createAiChat(currentView)
const selectAiChat = (s) => _selectAiChat(s, currentView)

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
const exportEnabled = computed(() => splitCompleted.value && selectedIds.size > 0)

const doReset = () => {
  _doReset(providerOptions, selectedModel, step)
  step.value = S.value.UPLOAD
}

// ── 分割流水线（擦除 → OCR → 分割 → 导出） ─────────────
const {
  eraseEnabled, eraseLoading, eraseImages, eraseDone,
  ocrLoading, ocrPages, ocrDone,
  startProcess, doSplit, doExport, doSaveToDb,
} = useSplitPipeline(pushToast, currentView, step, S, uploadReady, splitting, splitCompleted, uploadMode, selectedProvider, selectedModel, questions, selectedIds, pendingFiles, typesetMath)

const errorBankRef = ref(null)
const noteViewRef = ref(null)

const handleLoadRecord = (qs, record) => {
  questions.value = qs || []; selectedIds.clear()
  splitCompleted.value = true; step.value = S.value.EXPORT
  currentView.value = 'workspace_review'
  pushToast('success', `已加载「${record?.subject || '历史记录'}」的 ${qs.length} 道题目`)
  nextTick(() => typesetMath())
}

// ── AI 辅导对话（题目绑定） ────────────────────────────
const {
  chatSessionId, chatQuestion, chatActive,
  answerModalOpen, answerModalTarget, answerModalText, answerModalSaving,
  openChat, saveAnswerAndChat, backToErrorBank,
} = useChatSession(pushToast, currentView)

// ── 背景星星 ────────────────────────────────────────────
const bgStars = (() => {
  const list = []
  for (let i = 0; i < 50; i++) {
    list.push({
      left: Math.random() * 100, top: Math.random() * 100,
      size: 0.5 + Math.random() * 2, opacity: 0.1 + Math.random() * 0.4,
      duration: 2 + Math.random() * 4, delay: Math.random() * 5,
    })
  }
  return list
})()

// ── 键盘事件 ────────────────────────────────────────────
const onKeydown = (e) => {
  if (e.key === 'Escape' && modalOpen.value) closeModal()
  if (e.key === 'a' && (e.ctrlKey || e.metaKey) && questions.value.length) {
    e.preventDefault(); selectAll()
  }
}

// ── 视图切换 watcher ────────────────────────────────────
watch(currentView, async (newView) => {
  if (newView === 'workspace_review') {
    await nextTick()
    setTimeout(() => { questionListRef.value?.triggerTypeset?.() }, 650)
  }
  if (newView === 'ai-chat') loadAiChatSessions()
})

// ── 生命周期 ────────────────────────────────────────────
const pageLoading = ref(true)

onMounted(() => {
  initTheme()
  document.addEventListener('keydown', onKeydown)
  document.addEventListener('click', closeChatMenu)
  loadAiChatSessions()
  nextTick(updateIndicator)
  watch(() => activeAiChatId.value, () => nextTick(updateIndicator))

  if (currentView.value === 'workspace_review' && !splitCompleted.value) {
    router.replace('/app/workspace')
  }

  setTimeout(() => {
    pageLoading.value = false
    if (!globalLoading.value) {
      doFetchStatus()
    } else {
      const unwatch = watch(globalLoading, (val) => {
        if (!val) { doFetchStatus(); unwatch() }
      })
    }
  }, 2000)
})

onBeforeUnmount(() => {
  stopFakeProgress()
  document.removeEventListener('keydown', onKeydown)
  document.removeEventListener('click', closeChatMenu)
})
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden bg-[#0c0c0e] font-sans text-slate-300 relative">

    <!-- 全局背景装饰（Linear 风格） -->
    <div class="fixed inset-0 z-0 pointer-events-none">
      <!-- 左上角光圈 -->
      <div class="ws-bg-glow"></div>
      <!-- 噪点纹理 -->
      <div class="ws-bg-noise"></div>
      <!-- 闪烁星星 -->
      <div
        v-for="(s, i) in bgStars"
        :key="i"
        class="absolute rounded-full bg-white ws-star"
        :style="{
          left: s.left + '%',
          top: s.top + '%',
          width: s.size + 'px',
          height: s.size + 'px',
          '--star-opacity': s.opacity,
          animationDuration: s.duration + 's',
          animationDelay: s.delay + 's',
        }"
      ></div>
    </div>

    <Transition name="ws-loading-fade">
      <div v-if="pageLoading" class="fixed inset-0 z-[200] flex flex-col items-center justify-center gap-8 bg-[#0A0A0F]">
        <BrandLogo size="lg" breathe />
        <div class="w-48">
          <div class="h-0.5 w-full rounded-full bg-white/10 overflow-hidden">
            <div class="h-full rounded-full ws-loading-bar" style="background: linear-gradient(to right, rgba(129,115,223,0.8), rgba(99,87,199,0.8));"></div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 侧边栏导航（PC + 移动端） -->
    <SidebarNav
      :current-view="currentView"
      :last-workspace-view="lastWorkspaceView"
      :current-user="currentUser"
      :is-dark="isDark"
      :theme="theme"
      :nav-groups="NAV_GROUPS"
      :workspace-views="WORKSPACE_VIEWS"
      :collapsed-groups="collapsedGroups"
      :nav-btn-refs="navBtnRefs"
      :indicator-style="indicatorStyle"
      :indicator-transition="indicatorTransition"
      :chat-collapsed="chatCollapsed"
      :ai-chat-sessions="aiChatSessions"
      :active-ai-chat-id="activeAiChatId"
      :chat-btn-refs="chatBtnRefs"
      :chat-indicator-style="chatIndicatorStyle"
      :chat-indicator-transition="chatIndicatorTransition"
      :chat-menu-open-id="chatMenuOpenId"
      :renaming-chat-id="renamingChatId"
      :rename-text="renameText"
      :user-menu-open="userMenuOpen"
      @update:current-view="(v) => currentView = v"
      @update:collapsed-groups="(v) => Object.assign(collapsedGroups, v)"
      @update:chat-collapsed="(v) => chatCollapsed = v"
      @update:user-menu-open="(v) => userMenuOpen = v"
      @update:chat-menu-open-id="(v) => chatMenuOpenId = v"
      @update:rename-text="(v) => renameText = v"
      @update:nav-ref="(el) => navRef = el"
      @navigate-home="navigateToHome"
      @logout="handleLogout"
      @toggle-theme="toggleTheme"
      @create-ai-chat="createAiChat"
      @select-ai-chat="selectAiChat"
      @start-rename-chat="startRenameChat"
      @confirm-rename-chat="confirmRenameChat"
      @delete-ai-chat="deleteAiChat"
      @toggle-chat-menu="toggleChatMenu"
    />

    <!-- ================== 右侧区域 ================== -->
    <div class="relative z-10 flex-1 overflow-hidden pb-20 md:pb-3 md:pt-3 md:pr-3">

      <Transition name="view-fade" mode="out-in">
        <!-- 视图 1：录入工作台（分两页：上传解析页 / 题目核对页） -->
        <div v-if="currentView === 'workspace' || currentView === 'workspace_review'" key="workspace" class="h-full">
          <Transition name="flip" mode="out-in">
            <!-- 第一页：录入与分析 -->
            <ContentPanel v-if="currentView === 'workspace'" key="upload" title="智能录入与分析" :steps="workspaceSteps" :current-step="step - 1">
              <template #toolbar>
                <button
                  @click="showSplitHistory = !showSplitHistory"
                  class="inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
                  :class="showSplitHistory
                    ? 'bg-white/[0.06] text-[#f7f8f8] border border-white/[0.12]'
                    : 'border border-white/[0.08] bg-white/[0.02] text-[#d0d6e0] hover:bg-white/[0.05] hover:border-white/[0.12]'"
                >
                  <i class="fa-solid fa-clock-rotate-left text-[10px]"></i>
                  分割历史
                </button>
              </template>

              <!-- 右侧栏：分割历史 -->
              <template v-if="showSplitHistory" #sidebar>
                <SplitHistory
                  :theme="theme"
                  :visible="showSplitHistory"
                  @push-toast="pushToast"
                  @open-image="openModal"
                  @load-record="(r) => { handleLoadRecord(r); showSplitHistory = false }"
                  @go-workspace="currentView = splitCompleted ? 'workspace_review' : 'workspace'"
                />
              </template>

                <!-- 工具栏：状态 + 模式切换 + 擦除开关 -->
                <div class="flex flex-wrap items-center gap-3 py-2">
                  <!-- 模式切换 -->
                  <div class="flex items-center rounded-md brand-btn p-0.5">
                    <button
                      @click="uploadMode = 'exam'"
                      class="h-7 px-3 rounded text-xs font-medium transition-all"
                      :class="uploadMode === 'exam' ? 'bg-white/[0.06] text-[#f7f8f8]' : 'text-[#62666d] hover:text-[#8a8f98]'"
                    >
                      <i class="fa-solid fa-file-lines mr-1.5"></i>试卷分割
                    </button>
                    <button
                      @click="uploadMode = 'note'"
                      class="h-7 px-3 rounded text-xs font-medium transition-all"
                      :class="uploadMode === 'note' ? 'bg-white/[0.06] text-[#f7f8f8]' : 'text-[#62666d] hover:text-[#8a8f98]'"
                    >
                      <i class="fa-solid fa-book-open mr-1.5"></i>笔记整理
                    </button>
                  </div>

                  <!-- 分隔 -->
                  <div class="h-4 w-px bg-white/[0.08]"></div>

                  <!-- 擦除开关 -->
                  <label class="flex cursor-pointer items-center gap-2" @click="eraseEnabled = !eraseEnabled">
                    <div class="relative h-4 w-7 rounded-full transition-colors" :class="eraseEnabled ? 'bg-[rgb(129,115,223)]' : 'bg-white/[0.08]'">
                      <div class="absolute top-0.5 h-3 w-3 rounded-full bg-white transition-transform" :class="eraseEnabled ? 'translate-x-3' : 'translate-x-0.5'"></div>
                    </div>
                    <span class="text-xs text-[#8a8f98]">擦除笔迹</span>
                    <span class="relative group/tip">
                      <i class="fa-solid fa-circle-question text-[10px] text-[#62666d] cursor-help"></i>
                      <span class="absolute bottom-full right-0 mb-2 px-3 py-1.5 rounded-md bg-[#191a1b] border border-white/[0.08] text-xs text-[#d0d6e0] whitespace-nowrap opacity-0 pointer-events-none group-hover/tip:opacity-100 transition-opacity">
                        上传后自动擦除图片中的手写笔迹
                      </span>
                    </span>
                  </label>

                  <!-- 引擎状态（推到右侧） -->
                  <div class="ml-auto">
                    <StatusBar
                      :status-loading="statusLoading"
                      :status-error="statusError"
                      :status-pills="statusPills"
                      :provider-options="providerOptions"
                      :selected-model="selectedModel"
                      :disabled="splitting || splitCompleted"
                      :no-models="!hasConfiguredModel"
                      @update:selected-model="(v) => selectedModel = v"
                    />
                  </div>
                </div>

                <!-- 上传区（一体化） -->
                <div class="flex-1 min-h-0 overflow-y-auto custom-scrollbar flex flex-col items-center justify-center py-8 gap-6">

                  <!-- 引导信息 -->
                  <div class="text-center max-w-md">
                    <h3 class="text-base font-medium text-[#f7f8f8] mb-2">
                      {{ uploadMode === 'note' ? '上传手写笔记' : '上传试卷图片' }}
                    </h3>
                    <p class="text-sm text-[#62666d] leading-relaxed">
                      {{ uploadMode === 'note'
                        ? '支持拍照或扫描件，AI 将自动识别内容并整理为结构化笔记'
                        : '支持 PDF 和图片格式，AI 将自动完成 OCR 识别、题目分割和知识点标注'
                      }}
                    </p>
                  </div>

                  <!-- 流程步骤卡片 -->
                  <div class="grid grid-cols-4 gap-4 w-full max-w-2xl">
                    <div class="flex flex-col items-center gap-3 rounded-lg brand-btn p-4 text-center">
                      <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-white/[0.04]">
                        <i class="fa-solid fa-cloud-arrow-up text-xl text-[rgb(129,115,223)]"></i>
                      </div>
                      <span class="text-sm text-[#8a8f98]">{{ uploadMode === 'note' ? '上传笔记' : '上传文件' }}</span>
                    </div>
                    <div class="flex flex-col items-center gap-3 rounded-lg brand-btn p-4 text-center">
                      <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-white/[0.04]">
                        <i class="fa-solid fa-eye text-xl text-[rgb(129,115,223)]"></i>
                      </div>
                      <span class="text-sm text-[#8a8f98]">AI 识别</span>
                    </div>
                    <div class="flex flex-col items-center gap-3 rounded-lg brand-btn p-4 text-center">
                      <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-white/[0.04]">
                        <i class="fa-solid text-xl text-[rgb(129,115,223)]" :class="uploadMode === 'note' ? 'fa-wand-magic-sparkles' : 'fa-scissors'"></i>
                      </div>
                      <span class="text-sm text-[#8a8f98]">{{ uploadMode === 'note' ? '智能整理' : '分割纠错' }}</span>
                    </div>
                    <div class="flex flex-col items-center gap-3 rounded-lg brand-btn p-4 text-center">
                      <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-white/[0.04]">
                        <i class="fa-solid text-xl text-[rgb(129,115,223)]" :class="uploadMode === 'note' ? 'fa-bookmark' : 'fa-file-export'"></i>
                      </div>
                      <span class="text-sm text-[#8a8f98]">{{ uploadMode === 'note' ? '保存笔记' : '导出归档' }}</span>
                    </div>
                  </div>

                  <!-- 拖拽上传（与步骤卡片同宽） -->
                  <FileUploader
                    :pending-files="pendingFiles"
                    :file-progress="fileProgress"
                    :waiting-keys="waitingKeys"
                    :upload-busy="uploadBusy"
                    :upload-ready="uploadReady"
                    :splitting="splitting"
                    :split-completed="splitCompleted"
                    :expand="false"
                    :disabled="!hasConfiguredModel"
                    @upload="enqueueUpload"
                    @remove-file="removePendingFile"
                    class="w-full max-w-2xl"
                  />

                  <!-- 已上传文件 -->
                  <FileList
                    class="w-full max-w-2xl"
                    :pending-files="pendingFiles"
                    :file-progress="fileProgress"
                    :waiting-keys="waitingKeys"
                    :upload-busy="uploadBusy"
                    :upload-ready="uploadReady"
                    :splitting="splitting"
                    :split-completed="splitCompleted"
                    @remove-file="removePendingFile"
                  />

                  <!-- 操作按钮 -->
                  <ActionBar
                    class="mt-4"
                    :split-enabled="splitEnabled"
                    :export-enabled="false"
                    :splitting="splitting"
                    :split-completed="splitCompleted"
                    :upload-mode="uploadMode"
                    :erase-enabled="eraseEnabled"
                    @split="startProcess"
                  />
                </div>
            </ContentPanel>

            <!-- 第二页：解析结果核对 -->
            <ContentPanel
              v-else-if="currentView === 'workspace_review'"
              key="review"
              :title="eraseLoading ? '正在擦除...' : eraseDone && !ocrLoading && !ocrDone ? '擦除预览' : splitting ? '正在分割...' : ocrDone && !splitCompleted ? 'OCR 预览' : '题目数据核对'"
              :steps="workspaceSteps"
              :current-step="step - 1"
            >
              <template #toolbar>
                <!-- 返回按钮（始终显示） -->
                <button
                  @click="() => { doReset(); eraseImages = []; eraseDone = false; ocrPages = []; ocrDone = false; currentView = 'workspace' }"
                  class="group inline-flex items-center gap-2 rounded-md border border-white/[0.08] bg-white/[0.02] px-3 py-1.5 text-xs font-medium text-[#d0d6e0] hover:bg-white/[0.05] hover:border-white/[0.12] transition-colors"
                >
                  <i class="fa-solid fa-arrow-left-long text-xs transition-transform group-hover:-translate-x-0.5"></i>
                  返回
                </button>

                <!-- 擦除阶段按钮 -->
                <template v-if="eraseDone && !ocrLoading && !ocrDone">
                  <button @click="doErase" class="inline-flex items-center gap-1.5 rounded-md border border-white/[0.08] bg-white/[0.02] px-3 py-1.5 text-xs font-medium text-[#d0d6e0] hover:bg-white/[0.05] transition-colors">
                    <i class="fa-solid fa-arrows-rotate text-[10px]"></i> 重新擦除
                  </button>
                  <button @click="doOcr" class="inline-flex items-center gap-1.5 rounded-md bg-[rgb(129,115,223)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[rgb(145,132,235)] transition-colors">
                    <i class="fa-solid fa-check text-[10px]"></i> 确认，开始 OCR
                  </button>
                </template>

                <!-- OCR 阶段按钮 -->
                <template v-else-if="ocrDone && !splitCompleted && !splitting">
                  <button @click="doOcr" class="inline-flex items-center gap-1.5 rounded-md border border-white/[0.08] bg-white/[0.02] px-3 py-1.5 text-xs font-medium text-[#d0d6e0] hover:bg-white/[0.05] transition-colors">
                    <i class="fa-solid fa-arrows-rotate text-[10px]"></i> 重新识别
                  </button>
                  <button @click="doSplit" class="inline-flex items-center gap-1.5 rounded-md bg-[rgb(129,115,223)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[rgb(145,132,235)] transition-colors">
                    <i class="fa-solid fa-check text-[10px]"></i> 确认并分割
                  </button>
                </template>
              </template>

                <!-- 擦除加载中 / 擦除对比预览 -->
                <ErasePreview
                  v-if="eraseLoading || (eraseDone && !ocrLoading && !ocrDone)"
                  :images="eraseImages"
                  :loading="eraseLoading"
                  :preview-url="pendingPreviewUrls[0]"
                />

                <!-- OCR 加载中 / OCR 预览 -->
                <OcrPreview
                  v-else-if="ocrLoading || (ocrDone && !splitCompleted && !splitting)"
                  :pages="ocrPages"
                  :loading="ocrLoading"
                  :preview-url="pendingPreviewUrls[0]"
                />

                <!-- 分割进行中 -->
                <div v-else-if="splitting" class="flex-1 min-h-0 relative">
                  <img v-if="pendingPreviewUrls[0]" :src="pendingPreviewUrls[0]" class="absolute inset-0 w-full h-full object-contain opacity-10 blur-sm" alt="" />
                  <SplitLoading />
                </div>

                <!-- 题目列表 -->
                <div v-if="splitCompleted && questions.length" class="flex-1 overflow-y-auto pr-2 custom-scrollbar py-2 pb-24">
                  <QuestionList
                    ref="questionListRef"
                    :questions="questions"
                    :selected-ids="selectedIds"
                    @toggle-select="toggleQuestion"
                    @select-all="selectAll"
                    @deselect-all="deselectAll"
                    @open-image="openModal"
                    @reorder="reorderQuestions"
                  />
                </div>

            </ContentPanel>
          </Transition>
        </div>

        <!-- 视图 2：待复习 -->
        <ContentPanel v-else-if="currentView === 'review'" key="review_view" title="待复习">
          <ReviewView
            :theme="theme"
            :visible="currentView === 'review'"
            @go-workspace="currentView = 'workspace'"
            @push-toast="pushToast"
            @open-image="openModal"
            @start-chat="openChat"
          />
        </ContentPanel>

        <!-- 视图 3：数据面板 -->
        <ContentPanel v-else-if="currentView === 'dashboard'" key="dashboard_view" title="数据面板">
          <template #toolbar>
            <button @click="currentView = 'workspace'" class="inline-flex items-center gap-2 rounded-md brand-btn px-3 py-1.5 text-xs font-medium text-[#f7f8f8]">
              <i class="fa-solid fa-plus-circle text-[10px]"></i> 录入新题目
            </button>
          </template>
          <Dashboard
            :theme="theme"
            :visible="currentView === 'dashboard'"
            @go-workspace="currentView = 'workspace'"
            @push-toast="pushToast"
          />
        </ContentPanel>

        <!-- 视图 4：错题库 -->
        <ContentPanel v-else-if="currentView === 'error-bank'" key="error_bank_view" title="错题库">
          <template #toolbar>
            <button @click="currentView = 'workspace'" class="flex h-7 w-7 items-center justify-center rounded-md text-[#62666d] hover:bg-white/[0.04] hover:text-[#8a8f98] transition-colors" title="录入新题目">
              <i class="fa-solid fa-plus text-xs"></i>
            </button>
          </template>
          <template v-if="errorBankRef?.filterPanelOpen" #sidebar>
            <div class="p-4 space-y-4">
              <div class="flex items-center justify-between">
                <span class="text-xs font-medium text-[#f7f8f8]">筛选设置</span>
                <button @click="errorBankRef.filterPanelOpen = false" class="text-[#62666d] hover:text-[#8a8f98] transition-colors">
                  <i class="fa-solid fa-xmark text-xs"></i>
                </button>
              </div>

              <!-- 学科 -->
              <div>
                <label class="mb-1.5 block text-xs font-medium text-[#62666d]">学科</label>
                <CustomSelect v-model="errorBankRef.filters.subject" :options="errorBankRef.subjects" placeholder="全部学科" />
              </div>

              <!-- 题型 -->
              <div>
                <label class="mb-1.5 block text-xs font-medium text-[#62666d]">题型</label>
                <CustomSelect v-model="errorBankRef.filters.question_type" :options="errorBankRef.questionTypes" placeholder="全部题型" />
              </div>

              <!-- 复习状态 -->
              <div>
                <label class="mb-1.5 block text-xs font-medium text-[#62666d]">复习状态</label>
                <CustomSelect v-model="errorBankRef.filters.review_status" :options="['待复习', '复习中', '已掌握']" placeholder="全部状态" />
              </div>

              <!-- 知识点标签 -->
              <div v-if="errorBankRef.tagNames?.length">
                <label class="mb-1.5 block text-xs font-medium text-[#62666d]">知识点</label>
                <div class="flex flex-wrap gap-1.5">
                  <button v-for="tag in errorBankRef.tagNames" :key="tag"
                    @click="errorBankRef.toggleTagSelect(tag)"
                    class="rounded-md px-2 py-0.5 text-xs font-medium transition-all"
                    :class="errorBankRef.selectedTags?.has(tag)
                      ? 'bg-[rgb(129,115,223)] text-white'
                      : 'border border-white/[0.06] bg-white/[0.02] text-[#62666d] hover:text-[#8a8f98] hover:border-white/[0.1]'"
                  >{{ tag }}</button>
                </div>
              </div>
            </div>
          </template>

          <ErrorBank
            ref="errorBankRef"
            :theme="theme"
            :visible="currentView === 'error-bank'"
            @go-workspace="currentView = 'workspace'"
            @push-toast="pushToast"
            @open-image="openModal"
            @start-chat="openChat"
          />
        </ContentPanel>

        <!-- 视图 6：系统设置 -->
        <ContentPanel v-else-if="currentView === 'settings'" key="settings_view" title="系统设置">
          <SettingsView
            :visible="currentView === 'settings'"
            @saved="doFetchStatus"
          />
        </ContentPanel>

        <!-- 视图 7：AI 辅导对话 -->
        <ContentPanel v-else-if="currentView === 'chat'" key="chat_view" title="AI 辅导">
          <ChatView
            v-if="chatActive"
            :session-id="chatSessionId"
            :question="chatQuestion"
            :model-provider="selectedProvider"
            :model-name="selectedModel"
            :username="currentUser?.username"
            @back="backToErrorBank"
          />
        </ContentPanel>

        <!-- 视图 8：笔记 -->
        <ContentPanel v-else-if="currentView === 'notes'" key="notes_view" title="笔记库">
          <template #toolbar>
            <button @click="noteViewRef?.triggerUpload?.()" class="inline-flex items-center gap-2 rounded-md brand-btn px-3 py-1.5 text-xs font-medium text-[#f7f8f8]">
              <i class="fa-solid fa-plus text-[10px]"></i> 上传笔记
            </button>
          </template>
          <NoteView
            ref="noteViewRef"
            :visible="currentView === 'notes'"
            :model-provider="selectedProvider"
            :model-name="selectedModel"
            :theme="theme"
            @push-toast="pushToast"
          />
        </ContentPanel>

        <!-- 视图 9：AI 对话 -->
        <ContentPanel v-else-if="currentView === 'ai-chat'" key="ai_chat_view" title="AI 对话">
          <ChatPage
            :visible="currentView === 'ai-chat'"
            :session-id="activeAiChatId"
            :model-provider="selectedProvider"
            :model-name="selectedModel"
            :username="currentUser?.username"
            @push-toast="pushToast"
            @create-chat="createAiChat"
            @session-title-updated="onAiChatTitleUpdated"
          />
        </ContentPanel>
      </Transition>

      <!-- workspace_review 浮动选择面板 -->
      <SelectionPanel
        :visible="currentView === 'workspace_review'"
        :count="selectedIds.size"
        export-label="导出错题本"
        :show-save="true"
        @export="doExport"
        @save="doSaveToDb"
        @clear="deselectAll"
      />

    </div>

    <!-- 全局弹窗与通知 -->
    <Teleport to="body">
      <ImageModal
        :open="modalOpen"
        :src="modalSrc"
        :scale="modalScale"
        @close="closeModal"
        @update:scale="(s) => modalScale = s"
      />
      <ToastContainer :toasts="toasts" />

      <!-- 答案录入弹窗（AI 辅导前置） -->
      <div v-if="answerModalOpen" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/60" @click="answerModalOpen = false"></div>
        <div class="relative w-full max-w-lg rounded-lg brand-btn p-6">
          <h3 class="mb-1 text-base font-medium text-[#f7f8f8]">录入答案</h3>
          <p class="mb-4 text-xs text-[#62666d]">
            AI 辅导需要正确答案作为参考。支持 Markdown 格式，数学公式使用 LaTeX（$..$ 行内，$$...$$ 独占行）
          </p>
          <textarea
            v-model="answerModalText"
            rows="10"
            placeholder="在此粘贴或输入答案/解析..."
            class="w-full resize-none rounded-md border border-white/[0.08] bg-white/[0.02] px-4 py-3 font-mono text-sm text-[#d0d6e0] placeholder-[#62666d] focus:border-white/[0.12] focus:outline-none transition-colors"
          ></textarea>
          <div class="mt-4 flex justify-end gap-3">
            <button
              @click="answerModalOpen = false"
              class="rounded-md border border-white/[0.08] bg-white/[0.02] px-4 py-2 text-sm font-medium text-[#d0d6e0] transition-colors hover:bg-white/[0.05]"
            >
              取消
            </button>
            <button
              @click="saveAnswerAndChat"
              :disabled="answerModalSaving"
              class="rounded-md bg-[#5e6ad2] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#7170ff] disabled:opacity-50"
            >
              {{ answerModalSaving ? '保存中...' : '保存并开始辅导' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style>
::view-transition-old(root),
::view-transition-new(root) {
  animation: none;
  mix-blend-mode: normal;
}


.ws-loading-fade-leave-active { transition: opacity 0.4s ease; }
.ws-loading-fade-leave-to { opacity: 0; }

/* 星星闪烁 */
@keyframes ws-star-twinkle {
  0%, 100% { opacity: var(--star-opacity); }
  50% { opacity: 0.02; }
}
.ws-star {
  animation: ws-star-twinkle ease-in-out infinite;
}

.ws-loading-bar {
  animation: wsLoadProgress 2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}
@keyframes wsLoadProgress {
  from { width: 0%; }
  to   { width: 100%; }
}

/* 视图切换：极简淡入淡出 (Simple Fade) */
.view-fade-enter-active,
.view-fade-leave-active {
  transition: opacity 0.3s ease;
}

.view-fade-enter-from,
.view-fade-leave-to {
  opacity: 0;
}

/* 工作台内部页面切换：左右滑动淡入 (Flip) */
.flip-enter-active,
.flip-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.flip-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.flip-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* 背景装饰 */
.ws-bg-glow {
  position: absolute;
  top: -20%;
  left: -10%;
  width: 600px;
  height: 600px;
  border-radius: 9999px;
  background: radial-gradient(circle, rgba(129,115,223,0.06) 0%, transparent 70%);
}
.ws-bg-noise {
  position: absolute;
  inset: 0;
  opacity: 0.04;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-size: 256px 256px;
}

</style>
