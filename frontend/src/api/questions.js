/**
 * 错题库 API。
 *
 * 覆盖错题查询、筛选项、题目编辑、复习状态、统计看板和 AI 分析。
 */
import { assertJsonSuccess } from './client.js'

/** 查询错题库列表，支持科目、题型、标签、项目等筛选参数。 */
export async function fetchErrorBank(params = {}) {
  const qs = new URLSearchParams()
  // 过滤空值，避免把未选择的筛选项传给后端影响查询语义。
  for (const [k, v] of Object.entries(params)) {
    if (v !== null && v !== undefined && v !== '') qs.set(k, v)
  }
  const resp = await fetch(`/api/error-bank?${qs}`)
  return assertJsonSuccess(resp, '查询错题库失败')
}

/** 获取错题库中的科目筛选项。 */
export async function fetchSubjects(projectId) {
  const qs = new URLSearchParams()
  if (projectId) qs.set('project_id', projectId)
  const resp = await fetch(`/api/subjects?${qs}`)
  const data = await assertJsonSuccess(resp, '获取科目列表失败')
  return data.subjects
}

/** 获取错题库中的题型筛选项。 */
export async function fetchQuestionTypes(projectId) {
  const qs = new URLSearchParams()
  if (projectId) qs.set('project_id', projectId)
  const resp = await fetch(`/api/question-types?${qs}`)
  const data = await assertJsonSuccess(resp, '获取题型列表失败')
  return data.question_types
}

/** 根据科目和项目获取知识点标签名称列表。 */
export async function fetchTagNames(subject, projectId) {
  const qs = new URLSearchParams()
  if (subject) qs.set('subject', subject)
  if (projectId) qs.set('project_id', projectId)
  const resp = await fetch(`/api/stats?${qs}`)
  const data = await assertJsonSuccess(resp, '获取标签列表失败')
  return (data.stats || []).map(s => s.tag_name)
}

/** 保存用户对某道题填写的答案。 */
export async function saveAnswer(questionId, userAnswer) {
  const resp = await fetch(`/api/question/${questionId}/answer`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_answer: userAnswer }),
  })
  return assertJsonSuccess(resp, '保存答案失败')
}

/** 从数据库中的错题记录导出选中题目。 */
export async function exportFromDb(selectedIds) {
  const resp = await fetch('/api/export-from-db', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selected_ids: selectedIds }),
  })
  return assertJsonSuccess(resp, '导出失败')
}

/** 删除指定错题记录。 */
export async function deleteQuestion(questionId) {
  const resp = await fetch(`/api/question/${questionId}`, { method: 'DELETE' })
  return assertJsonSuccess(resp, '删除失败')
}

/** 更新错题复习状态，例如待复习、复习中、已掌握。 */
export async function updateReviewStatus(questionId, reviewStatus) {
  const resp = await fetch(`/api/question/${questionId}/review-status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ review_status: reviewStatus }),
  })
  return assertJsonSuccess(resp, '更新复习状态失败')
}

/** 获取仪表盘统计数据。 */
export async function fetchDashboardStats(subject, projectId) {
  const qs = new URLSearchParams()
  if (subject) qs.set('subject', subject)
  if (projectId) qs.set('project_id', projectId)
  const resp = await fetch(`/api/dashboard-stats?${qs}`)
  return assertJsonSuccess(resp, '获取统计数据失败')
}

/** 请求后端对选中错题做 AI 分析。 */
export async function requestAiAnalysis(questionIds, { providerSource, providerId, modelProvider, modelName } = {}) {
  const body = { question_ids: questionIds }
  // 模型来源字段按需透传，兼容系统默认模型和用户自定义 provider。
  if (modelProvider) body.model_provider = modelProvider
  if (modelName) body.model_name = modelName
  if (providerSource) body.provider_source = providerSource
  if (providerId) body.provider_id = providerId

  const resp = await fetch('/api/ai-analysis', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return assertJsonSuccess(resp, 'AI 分析请求失败')
}

/** 更新题目详情内容或备注等字段。 */
export async function updateQuestion(questionId, payload) {
  const resp = await fetch(`/api/question/${questionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return assertJsonSuccess(resp, '保存失败')
}

/** 保存题目的标准答案或解析答案。 */
export async function saveQuestionAnswer(questionId, answer) {
  const resp = await fetch(`/api/question/${questionId}/answer`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answer }),
  })
  return assertJsonSuccess(resp, '保存答案失败')
}
