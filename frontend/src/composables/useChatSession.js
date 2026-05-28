/**
 * useChatSession.js
 * AI 辅导对话会话管理（题目绑定对话）— 单例 composable
 */
import { ref } from 'vue'
import * as api from '@/api/index.js'
import { useToast } from '@/composables/useToast.js'
import { useAiChatSessions } from '@/composables/useAiChatSessions.js'
import { useProjects } from '@/composables/useProjects.js'
import { useWorkspaceNav } from '@/composables/useWorkspaceNav.js'

// ── 模块级单例状态 ──────────────────────────────────────
const chatSessionId = ref(null)
const chatQuestion = ref(null)
const chatActive = ref(false)
const answerModalOpen = ref(false)
const answerModalTarget = ref(null)
const answerModalText = ref('')
const answerModalSaving = ref(false)
const pendingAiChatProjectId = ref(null)
const pendingAiChatQuestionIds = ref([])

export function useChatSession() {
  const { pushToast } = useToast()
  const { currentView } = useWorkspaceNav()
  const { createAiChat } = useAiChatSessions(pushToast)
  const { activeQuestionProjectId } = useProjects()

  /**
   * 切到新的独立 AI 对话页，并预置当前题目作为引用上下文。
   */
  const doOpenAiChat = async (question) => {
    try {
      pendingAiChatProjectId.value = activeQuestionProjectId.value || null
      pendingAiChatQuestionIds.value = question?.id ? [question.id] : []
      await createAiChat(currentView)
    } catch (e) {
      pushToast('error', '打开对话失败: ' + (e instanceof Error ? e.message : String(e)))
    }
  }

  /**
   * 打开题目辅导对话；没有答案解析时先要求用户补充答案。
   */
  const openChat = async (question) => {
    chatQuestion.value = question
    if (!question.answer) {
      answerModalTarget.value = question
      answerModalText.value = ''
      answerModalOpen.value = true
      return
    }
    await doOpenAiChat(question)
  }

  /**
   * 保存补充的答案解析，然后继续进入题目辅导对话。
   */
  const saveAnswerAndChat = async () => {
    if (!answerModalTarget.value || answerModalSaving.value) return
    const text = answerModalText.value.trim()
    if (!text) { pushToast('error', '请输入答案/解析内容'); return }
    answerModalSaving.value = true
    try {
      await api.saveQuestionAnswer(answerModalTarget.value.id, text)
      answerModalTarget.value.answer = text
      answerModalOpen.value = false
      pushToast('success', '答案已保存')
      await doOpenAiChat(answerModalTarget.value)
    } catch (e) {
      pushToast('error', '保存答案失败: ' + (e instanceof Error ? e.message : String(e)))
    } finally {
      answerModalSaving.value = false
    }
  }

  /**
   * 退出题目辅导对话，回到错题库视图。
   */
  const backToErrorBank = () => {
    chatActive.value = false
    chatSessionId.value = null
    chatQuestion.value = null
    currentView.value = 'error-bank'
  }

  return {
    chatSessionId, chatQuestion, chatActive,
    answerModalOpen, answerModalTarget, answerModalText, answerModalSaving,
    pendingAiChatProjectId, pendingAiChatQuestionIds,
    openChat, saveAnswerAndChat, backToErrorBank,
  }
}
