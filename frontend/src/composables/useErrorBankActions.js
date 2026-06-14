import { computed, ref } from 'vue'
import * as api from '@/api/index.js'

/**
 * useErrorBankActions
 * 管理错题库的编辑、删除、导出、复习状态和 AI 分析动作。
 */
export function useErrorBankActions({
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
}) {
  const dialogOpen = ref(false)
  const dialogField = ref('answer')
  const dialogQuestion = ref(null)
  const dialogSaving = ref(false)
  const detailOpen = ref(false)
  const detailQuestion = ref(null)
  const aiLoading = ref(false)
  const aiAnalysis = ref(null)

  const aiSummary = computed(() => {
    if (aiAnalysis.value?.summary) return aiAnalysis.value.summary
    if (activeQuestion.value?.answer) return '已根据当前题目的答案解析生成学习建议，建议先复盘核心知识点，再进行同类题训练。'
    return '当前题目还没有标准解析。可以先补充答案解析，或进入 AI 辅导对话继续追问。'
  })

  const openDetail = (question = activeQuestion.value) => {
    detailQuestion.value = question
    detailOpen.value = true
  }

  const openEditDialog = (question, field) => {
    dialogQuestion.value = question
    dialogField.value = field
    dialogOpen.value = true
  }

  /**
   * 保存题目、答案解析或个人笔记。
   */
  const onDialogSave = async (draft) => {
    if (dialogSaving.value || !dialogQuestion.value) return
    dialogSaving.value = true
    try {
      if (dialogField.value === 'question') {
        await api.updateQuestion(dialogQuestion.value.id, { content: draft.content, answer: draft.answer })
        dialogQuestion.value.content_json = [{ block_type: 'text', content: draft.content }]
        dialogQuestion.value.answer = draft.answer
      } else if (dialogField.value === 'answer') {
        await api.saveQuestionAnswer(dialogQuestion.value.id, draft)
        dialogQuestion.value.answer = draft
      } else {
        await api.saveAnswer(dialogQuestion.value.id, draft)
        dialogQuestion.value.user_answer = draft
      }
      dialogOpen.value = false
      pushToast('success', '已保存')
      await typesetMath()
    } catch (_) {
      pushToast('error', '保存失败')
    } finally {
      dialogSaving.value = false
    }
  }

  /**
   * 快速更新题目的复习状态。
   */
  const quickMarkStatus = async (question, status) => {
    if (!question || question.review_status === status) return
    try {
      const data = await api.updateReviewStatus(question.id, status)
      question.review_status = data.review_status
      pushToast('success', `已标记为「${status}」`)
      await loadStats()
    } catch (_) {
      pushToast('error', '更新状态失败')
    }
  }

  /**
   * 删除题目，并同步本地列表、总数和选择状态。
   */
  const doDelete = async (question) => {
    if (!question) return
    try {
      await api.deleteQuestion(question.id)
      items.value = items.value.filter(item => item.id !== question.id)
      total.value = Math.max(0, total.value - 1)
      grandTotal.value = Math.max(0, grandTotal.value - 1)
      selectedIds.delete(question.id)
      if (String(activeQuestionId.value) === String(question.id)) {
        activeQuestionId.value = items.value[0]?.id || null
      }
      pushToast('success', '题目已删除')
      await loadStats()
    } catch (_) {
      pushToast('error', '删除失败')
    }
  }

  /**
   * 导出当前已选中的题目。
   */
  const doExport = async () => {
    if (!selectedIds.size) return
    try {
      const data = await api.exportFromDb(Array.from(selectedIds))
      pushToast('success', '错题本导出成功')
      let filename = 'wrongbook.md'
      if (data.output_path) {
        const parts = String(data.output_path).split(/[/\\]/)
        const last = parts[parts.length - 1]
        if (last) filename = last
      }
      let downloadHref = data.download_url || `/download/${encodeURIComponent(filename)}`
      downloadHref += downloadHref.includes('?') ? `&t=${Date.now()}` : `?t=${Date.now()}`
      const link = document.createElement('a')
      link.href = downloadHref
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      pushToast('error', '导出失败: ' + (error instanceof Error ? error.message : String(error)))
    }
  }

  /**
   * 请求后端为当前题目生成 AI 分析。
   */
  const requestAnalysis = async () => {
    if (!activeQuestion.value || aiLoading.value) return
    aiLoading.value = true
    activeTab.value = 'analysis'
    try {
      const data = await api.requestAiAnalysis([activeQuestion.value.id])
      aiAnalysis.value = data.analysis || null
    } catch (error) {
      pushToast('error', 'AI 分析失败: ' + (error instanceof Error ? error.message : String(error)))
    } finally {
      aiLoading.value = false
    }
  }

  const startPractice = () => {
    if (!activeQuestion.value) return
    quickMarkStatus(activeQuestion.value, '复习中')
  }

  const clearAiAnalysis = () => {
    aiAnalysis.value = null
  }

  return {
    dialogOpen,
    dialogField,
    dialogQuestion,
    dialogSaving,
    detailOpen,
    detailQuestion,
    aiLoading,
    aiAnalysis,
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
  }
}
