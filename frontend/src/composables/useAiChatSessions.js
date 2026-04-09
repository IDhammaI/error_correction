import { ref, nextTick } from 'vue'
import * as api from '@/api.js'

export function useAiChatSessions(pushToast) {
  const aiChatSessions = ref([])
  const activeAiChatId = ref(null)
  const chatMenuOpenId = ref(null)
  const renamingChatId = ref(null)
  const renameText = ref('')

  async function loadAiChatSessions() {
    try {
      const data = await api.fetchMyChatSessions({ limit: 50 })
      aiChatSessions.value = data.sessions || []
    } catch (_) {}
  }

  async function createAiChat(currentView) {
    try {
      const session = await api.createIndependentChat('新对话')
      aiChatSessions.value.unshift(session)
      activeAiChatId.value = session.id
      if (currentView.value !== 'ai-chat') currentView.value = 'ai-chat'
    } catch (e) {
      pushToast('error', e.message)
    }
  }

  function selectAiChat(s, currentView) {
    activeAiChatId.value = s.id
    if (currentView.value !== 'ai-chat') currentView.value = 'ai-chat'
  }

  async function onAiChatTitleUpdated(sessionId, title) {
    const s = aiChatSessions.value.find(s => s.id === sessionId)
    if (s && s.title === '新对话') {
      s.title = title
      try { await api.updateChatTitle(sessionId, title) } catch (_) {}
    }
  }

  function toggleChatMenu(id) {
    chatMenuOpenId.value = chatMenuOpenId.value === id ? null : id
  }

  function closeChatMenu() {
    chatMenuOpenId.value = null
  }

  async function startRenameChat(s) {
    chatMenuOpenId.value = null
    renamingChatId.value = s.id
    renameText.value = s.title
    await nextTick()
    const input = document.querySelector('input[data-rename-input]')
    if (input) { input.focus(); input.selectionStart = input.selectionEnd = input.value.length }
  }

  async function confirmRenameChat(s) {
    const title = renameText.value.trim()
    if (title && title !== s.title) {
      try {
        await api.updateChatTitle(s.id, title)
        s.title = title
      } catch (e) {
        pushToast('error', e.message)
      }
    }
    renamingChatId.value = null
  }

  async function deleteAiChat(id) {
    try {
      await api.deleteChat(id)
      aiChatSessions.value = aiChatSessions.value.filter(s => s.id !== id)
      if (activeAiChatId.value === id) activeAiChatId.value = null
    } catch (e) {
      pushToast('error', e.message)
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
