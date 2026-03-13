/**
 * API 调用层 — 集中管理所有 fetch 请求
 */

export async function fetchAppConfig() {
  const resp = await fetch('/api/config')
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data.config
  throw new Error((data && data.error) || '获取配置失败')
}

export async function updateAppConfig(config) {
  const resp = await fetch('/api/config', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data
  throw new Error((data && data.error) || '更新配置失败')
}

export async function fetchStatus() {
  const resp = await fetch('/api/status')
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data.status
  throw new Error((data && data.error) || '获取系统状态失败')
}

export async function cancelFile(fileKey) {
  const resp = await fetch('/api/cancel_file', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_key: fileKey }),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json().catch(() => null)
  if (data && data.success) return data
  throw new Error((data && data.error) || '撤销失败')
}

export function uploadFiles(formData, { onProgress, onSuccess, onError, onAbort }) {
  const xhr = new XMLHttpRequest()
  xhr.open('POST', '/api/upload', true)

  if (onProgress) {
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) onProgress(e.loaded / e.total)
    })
  }

  xhr.addEventListener('load', () => {
    let data = null
    try { data = JSON.parse(xhr.responseText) } catch (_) {}
    if (data && data.success) {
      onSuccess?.(data)
    } else {
      onError?.((data && data.error) || '文件处理失败')
    }
  })

  xhr.addEventListener('error', () => onError?.('上传失败: 网络错误'))
  xhr.addEventListener('abort', () => onAbort?.())

  xhr.send(formData)
  return xhr
}

export async function splitQuestions(modelProvider, modelName) {
  const body = { model_provider: modelProvider }
  if (modelName) body.model_name = modelName
  const resp = await fetch('/api/split', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data
  throw new Error((data && data.error) || '题目分割失败')
}

export async function exportQuestions(selectedIds) {
  const resp = await fetch('/api/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selected_ids: selectedIds }),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data
  throw new Error((data && data.error) || '导出失败')
}

export async function saveToDb(selectedIds, answers = []) {
  const resp = await fetch('/api/save-to-db', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selected_ids: selectedIds, answers }),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data
  throw new Error((data && data.error) || '导入错题库失败')
}

// ── 错题库 API ──────────────────────────────────────────

export async function fetchErrorBank(params = {}) {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== null && v !== undefined && v !== '') qs.set(k, v)
  }
  const resp = await fetch(`/api/error-bank?${qs}`)
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data
  throw new Error((data && data.error) || '查询错题库失败')
}

export async function fetchSubjects() {
  const resp = await fetch('/api/subjects')
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data.subjects
  throw new Error((data && data.error) || '获取科目列表失败')
}

export async function fetchQuestionTypes() {
  const resp = await fetch('/api/question-types')
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data.question_types
  throw new Error((data && data.error) || '获取题型列表失败')
}

export async function fetchTagNames(subject) {
  const qs = new URLSearchParams()
  if (subject) qs.set('subject', subject)
  const resp = await fetch(`/api/stats?${qs}`)
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return (data.stats || []).map(s => s.tag_name)
  throw new Error((data && data.error) || '获取标签列表失败')
}

export async function saveAnswer(questionId, userAnswer) {
  const resp = await fetch(`/api/question/${questionId}/answer`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_answer: userAnswer }),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data
  throw new Error((data && data.error) || '保存答案失败')
}

export async function exportFromDb(selectedIds) {
  const resp = await fetch('/api/export-from-db', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selected_ids: selectedIds }),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data
  throw new Error((data && data.error) || '导出失败')
}

export async function deleteQuestion(questionId) {
  const resp = await fetch(`/api/question/${questionId}`, { method: 'DELETE' })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data
  throw new Error((data && data.error) || '删除失败')
}

export async function updateReviewStatus(questionId, reviewStatus) {
  const resp = await fetch(`/api/question/${questionId}/review-status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ review_status: reviewStatus }),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data
  throw new Error((data && data.error) || '更新复习状态失败')
}

export async function fetchDashboardStats(subject) {
  const qs = subject ? `?subject=${encodeURIComponent(subject)}` : ''
  const resp = await fetch(`/api/dashboard-stats${qs}`)
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data
  throw new Error((data && data.error) || '获取统计数据失败')
}

export async function requestAiAnalysis(questionIds) {
  const resp = await fetch('/api/ai-analysis', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_ids: questionIds }),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data
  throw new Error((data && data.error) || 'AI 分析请求失败')
}

// ── AI 辅导对话 API ──────────────────────────────────────

export async function saveQuestionAnswer(questionId, answer) {
  const resp = await fetch(`/api/question/${questionId}/answer`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answer }),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data
  throw new Error((data && data.error) || '保存答案失败')
}

export async function fetchChatSessions(questionId) {
  const resp = await fetch(`/api/question/${questionId}/chats`)
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data.sessions
  throw new Error((data && data.error) || '获取对话列表失败')
}

export async function createChat(questionId) {
  const resp = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_id: questionId }),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data.session
  throw new Error((data && data.error) || '创建对话失败')
}

export async function fetchMessages(sessionId, { limit = 30, beforeId } = {}) {
  const qs = new URLSearchParams({ limit })
  if (beforeId) qs.set('before_id', beforeId)
  const resp = await fetch(`/api/chat/${sessionId}/messages?${qs}`)
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return { messages: data.messages, hasMore: data.hasMore }
  throw new Error((data && data.error) || '获取消息失败')
}

export async function streamChat(sessionId, message, modelProvider = 'openai', signal, modelName) {
  const body = { message, model_provider: modelProvider }
  if (modelName) body.model_name = modelName
  const opts = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
  if (signal) opts.signal = signal
  return fetch(`/api/chat/${sessionId}/stream`, opts)
}
