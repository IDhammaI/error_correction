<script setup>
/**
 * AppLayout.vue
 * App 布局容器 — 侧边栏导航 + 内容区视图切换
 * 仅负责：导航、布局、全局状态（主题/认证/Toast/弹窗）
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
import { useWorkspaceNav } from '@/composables/useWorkspaceNav.js'
import { useChatSession } from '@/composables/useChatSession.js'
import SidebarNav from '@/components/workspace/SidebarNav.vue'
import ImageModal from '@/components/base/ImageModal.vue'
import ToastContainer from '@/components/base/ToastContainer.vue'
import WorkspaceBackground from '@/components/workspace/WorkspaceBackground.vue'
import AnswerInputModal from '@/components/workspace/AnswerInputModal.vue'
import WorkspaceView from '@/views/app/WorkspaceView.vue'
import Dashboard from '@/views/app/DashboardView.vue'
import ReviewView from '@/views/app/ReviewView.vue'
import ErrorBank from '@/views/app/ErrorBankView.vue'
import ChatView from '@/views/app/ChatView.vue'
import SettingsView from '@/views/app/SettingsView.vue'
import NoteView from '@/views/app/NoteView.vue'
import ChatPage from '@/views/app/ChatPageView.vue'

// ── 全局 Composables ────────────────────────────────────
const router = useRouter()
const { currentUser } = useAuth()
const { loading: globalLoading } = usePageTransition()
const { isDark, toggleTheme, initTheme } = useTheme()
const { toasts, pushToast } = useWorkspaceToast()
const { modalOpen, modalSrc, modalScale, closeModal } = useImageModal()
const { doFetchStatus } = useSystemStatus()
const {
  navRef, navBtnRefs, indicatorStyle, indicatorTransition,
  chatListRef, chatBtnRefs, chatIndicatorStyle, chatIndicatorTransition,
  updateIndicator: _updateIndicator,
} = useSidebarIndicator()
const {
  aiChatSessions, activeAiChatId,
  chatMenuOpenId, renamingChatId, renameText,
  loadAiChatSessions, createAiChat: _createAiChat, selectAiChat: _selectAiChat,
  toggleChatMenu, closeChatMenu,
  startRenameChat, confirmRenameChat, deleteAiChat,
} = useAiChatSessions(pushToast)
const {
  currentView, lastWorkspaceView, collapsedGroups, chatCollapsed,
  NAV_GROUPS, WORKSPACE_VIEWS, navigateToHome,
} = useWorkspaceNav()
const {
  answerModalOpen, answerModalText, answerModalSaving,
  saveAnswerAndChat,
} = useChatSession()

provide('pushToast', pushToast) // useToast() composable injects this key

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

watch(currentView, () => nextTick(updateIndicator))
watch(collapsedGroups, () => {
  updateIndicator(false)
  nextTick(() => updateIndicator(false))
}, { deep: true })

// ── AI 独立对话包装 ────────────────────────────────────
const createAiChat = () => _createAiChat(currentView)
const selectAiChat = (s) => _selectAiChat(s, currentView)

// ── 键盘事件 ────────────────────────────────────────────
const onKeydown = (e) => {
  if (e.key === 'Escape' && modalOpen.value) closeModal()
}

// ── 视图切换 ────────────────────────────────────────────
watch(currentView, (newView) => {
  if (newView === 'ai-chat') loadAiChatSessions()
})

// ── 生命周期 ────────────────────────────────────────────
onMounted(() => {
  initTheme()
  document.addEventListener('keydown', onKeydown)
  document.addEventListener('click', closeChatMenu)
  loadAiChatSessions()
  nextTick(updateIndicator)
  watch(() => activeAiChatId.value, () => nextTick(updateIndicator))

  if (!globalLoading.value) {
    doFetchStatus()
  } else {
    const unwatch = watch(globalLoading, (val) => {
      if (!val) { doFetchStatus(); unwatch() }
    })
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.removeEventListener('click', closeChatMenu)
})
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden bg-[#0c0c0e] font-sans text-slate-300 relative">

    <WorkspaceBackground />

    <!-- 侧边栏导航 -->
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

    <!-- ================== 右侧内容区 ================== -->
    <div class="relative z-10 flex-1 overflow-hidden pb-20 md:pb-3 md:pt-3 md:pr-3">
      <Transition name="view-fade" mode="out-in">
        <WorkspaceView v-if="currentView === 'workspace' || currentView === 'workspace_review'" key="workspace" :theme="theme" />
        <ReviewView v-else-if="currentView === 'review'" key="review" />
        <Dashboard v-else-if="currentView === 'dashboard'" key="dashboard" />
        <ErrorBank v-else-if="currentView === 'error-bank'" key="error-bank" />
        <SettingsView v-else-if="currentView === 'settings'" key="settings" />
        <ChatView v-else-if="currentView === 'chat'" key="chat" />
        <NoteView v-else-if="currentView === 'notes'" key="notes" />
        <ChatPage v-else-if="currentView === 'ai-chat'" key="ai-chat" />
      </Transition>
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
      <AnswerInputModal
        :open="answerModalOpen"
        :text="answerModalText"
        :saving="answerModalSaving"
        @update:open="(v) => answerModalOpen = v"
        @update:text="(v) => answerModalText = v"
        @confirm="saveAnswerAndChat"
      />
    </Teleport>
  </div>
</template>

<style>
::view-transition-old(root),
::view-transition-new(root) {
  animation: none;
  mix-blend-mode: normal;
}

/* 视图切换淡入淡出 */
.view-fade-enter-active,
.view-fade-leave-active {
  transition: opacity 0.3s ease;
}
.view-fade-enter-from,
.view-fade-leave-to {
  opacity: 0;
}
</style>
