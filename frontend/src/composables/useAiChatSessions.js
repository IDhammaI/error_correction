import { ref, nextTick, watch } from 'vue'
import * as api from '@/api/index.js'
import { useRoute, useRouter } from 'vue-router'

/**
 * useAiChatSessions.js
 * 独立 AI 对话的列表、选中项、重命名菜单和路由同步。
 *
 * Sidebar、AppLayout、ChatPageView 都会读写这份状态，
 * 所以这里用模块单例保证多个调用点看到的是同一组会话。
 */
const aiChatSessions = ref([])
const activeAiChatId = ref(null)
const chatMenuOpenId = ref(null)
const renamingChatId = ref(null)
const renameText = ref('')

let pushToastFn = null
let routerRef = null
let routeRef = null
let routeSyncInitialized = false

const toast = (type, message) => {
  if (typeof pushToastFn === 'function') pushToastFn(type, message)
}

/**
 * 管理独立 AI 对话会话，并在 /app/ai-chat/:sessionId 与状态之间双向同步。
 */
export function useAiChatSessions(pushToast) {
  if (pushToast) pushToastFn = pushToast
  if (!routerRef) routerRef = useRouter()
  if (!routeRef) routeRef = useRoute()

  if (!routeSyncInitialized) {
    routeSyncInitialized = true

    // URL -> 状态：支持直接访问 /app/ai-chat/:sessionId
    watch(
      () => [routeRef.params.view, routeRef.params.subview],
      ([view, sub]) => {
        if (view !== 'ai-chat') return
        const id = sub ? String(sub) : null
        const cur = activeAiChatId.value != null ? String(activeAiChatId.value) : null
        if (id && id !== cur) activeAiChatId.value = id
        if (!id && cur) routerRef.replace(`/app/ai-chat/${cur}`)
      },
      { immediate: true }
    )

    // 状态 -> URL：侧边栏切换会话时更新地址
    watch(activeAiChatId, (id) => {
      if (routeRef.params.view !== 'ai-chat') return
      const next = id != null ? String(id) : null
      const cur = routeRef.params.subview ? String(routeRef.params.subview) : null
      if (!next && cur) routerRef.replace('/app/ai-chat')
      if (next && cur !== next) routerRef.replace(`/app/ai-chat/${next}`)
    })
  }

  /**
   * 从后端加载当前用户的独立对话列表。
   */
  async function loadAiChatSessions() {
    try {
      const data = await api.fetchMyChatSessions({ limit: 50 })
      aiChatSessions.value = data.sessions || []
    } catch (_) {}
  }

  /**
   * 创建一个新独立对话，并切换到 AI 对话视图。
   */
  async function createAiChat(currentViewRef) {
    try {
      const session = await api.createIndependentChat('新对话')
      aiChatSessions.value.unshift(session)
      activeAiChatId.value = session.id
      if (currentViewRef && currentViewRef.value !== 'ai-chat') {
        currentViewRef.value = 'ai-chat'
      }
    } catch (e) {
      toast('error', e.message)
    }
  }

  /**
   * 选中已有独立对话，必要时同步切换当前工作台视图。
   */
  function selectAiChat(s, currentViewRef) {
    activeAiChatId.value = s.id
    if (currentViewRef && currentViewRef.value !== 'ai-chat') {
      currentViewRef.value = 'ai-chat'
    }
  }

  /**
   * 首次生成标题后，把默认“新对话”替换为模型给出的标题。
   */
  async function onAiChatTitleUpdated(sessionId, title) {
    const s = aiChatSessions.value.find(s => s.id === sessionId)
    if (s && s.title === '新对话') {
      s.title = title
      try { await api.updateChatTitle(sessionId, title) } catch (_) {}
    }
  }

  /**
   * 打开或关闭某条会话的操作菜单。
   */
  function toggleChatMenu(id) {
    chatMenuOpenId.value = chatMenuOpenId.value === id ? null : id
  }

  /**
   * 关闭当前打开的会话操作菜单。
   */
  function closeChatMenu() {
    chatMenuOpenId.value = null
  }

  /**
   * 进入重命名模式，并在 DOM 更新后聚焦输入框。
   */
  async function startRenameChat(s) {
    chatMenuOpenId.value = null
    renamingChatId.value = s.id
    renameText.value = s.title
    await nextTick()
    const input = document.querySelector('input[data-rename-input]')
    if (input) { input.focus(); input.selectionStart = input.selectionEnd = input.value.length }
  }

  /**
   * 提交会话标题修改，空标题或未变化标题不会请求后端。
   */
  async function confirmRenameChat(s) {
    const title = renameText.value.trim()
    if (title && title !== s.title) {
      try {
        await api.updateChatTitle(s.id, title)
        s.title = title
      } catch (e) {
        toast('error', e.message)
      }
    }
    renamingChatId.value = null
  }

  /**
   * 删除独立对话，并在删除当前会话时清空选中状态。
   */
  async function deleteAiChat(id) {
    try {
      await api.deleteChat(id)
      aiChatSessions.value = aiChatSessions.value.filter(s => s.id !== id)
      if (activeAiChatId.value === id) activeAiChatId.value = null
    } catch (e) {
      toast('error', e.message)
    }
  }

  return {
    aiChatSessions, activeAiChatId,
    chatMenuOpenId, renamingChatId, renameText,
    loadAiChatSessions, createAiChat, selectAiChat,
    onAiChatTitleUpdated, toggleChatMenu, closeChatMenu,
    startRenameChat, confirmRenameChat, deleteAiChat,
  }
}
