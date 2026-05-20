/**
 * useChatSession.js
 * AI 辅导对话会话管理（题目绑定对话）— 单例 composable
 */
import { ref } from 'vue'
import * as api from '@/api/index.js'
import { useToast } from '@/composables/useToast.js'
import { useWorkspaceNav } from '@/composables/useWorkspaceNav.js'

// ── 模块级单例状态 ──────────────────────────────────────
const chatSessionId = ref(null)
const chatQuestion = ref(null)
const chatActive = ref(false)
const answerModalOpen = ref(false)
const answerModalTarget = ref(null)
const answerModalText = ref('')
const answerModalSaving = ref(false)

export function useChatSession() {
  const { pushToast } = useToast()
  const { currentView } = useWorkspaceNav()

  /**
   * 获取题目绑定的对话会话；没有历史会话时创建一个新会话。
   */
  const doOpenChatSession = async (question) => {
    try {
      const sessions = await api.fetchChatSessions(question.id)
      chatSessionId.value = sessions.length ? sessions[0].id : (await api.createChat(question.id)).id
      chatActive.value = true
      currentView.value = 'chat'
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
    await doOpenChatSession(question)
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
      await doOpenChatSession(answerModalTarget.value)
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
    openChat, saveAnswerAndChat, backToErrorBank,
  }
}
