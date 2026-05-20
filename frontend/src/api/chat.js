/**
 * AI 对话 API。
 *
 * 普通会话接口返回 JSON；streamChat 保留原生 fetch 响应，让调用方自行读取流式内容。
 */
import { assertJsonSuccess, buildModelBody } from './client.js'

/** 获取某道错题关联的辅导对话列表。 */
export async function fetchChatSessions(questionId) {
  const resp = await fetch(`/api/question/${questionId}/chats`)
  const data = await assertJsonSuccess(resp, '获取对话列表失败')
  return data.sessions
}

/** 为指定错题创建新的辅导对话。 */
export async function createChat(questionId) {
  const resp = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_id: questionId }),
  })
  const data = await assertJsonSuccess(resp, '创建对话失败')
  return data.session
}

/** 分页获取会话消息，beforeId 用于向前加载历史消息。 */
export async function fetchMessages(sessionId, { limit = 30, beforeId } = {}) {
  const qs = new URLSearchParams({ limit })
  if (beforeId) qs.set('before_id', beforeId)
  const resp = await fetch(`/api/chat/${sessionId}/messages?${qs}`)
  const data = await assertJsonSuccess(resp, '获取消息失败')
  return { messages: data.messages, hasMore: data.hasMore }
}

/** 发起流式聊天请求，返回原始 Response 交给调用方读取流。 */
export async function streamChat(sessionId, message, modelProvider = 'openai', signal, modelName, { deepThink = false, providerSource, providerId, contextRefs = [] } = {}) {
  const opts = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(buildModelBody(modelProvider, modelName, providerSource, providerId, { message, deep_think: deepThink, context_refs: contextRefs })),
  }
  if (signal) opts.signal = signal
  // 流式响应不能在这里统一 json 化，否则调用方无法逐段读取模型输出。
  return fetch(`/api/chat/${sessionId}/stream`, opts)
}

/** 创建不绑定具体错题的独立对话。 */
export async function createIndependentChat(title = '新对话') {
  const resp = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
  const data = await assertJsonSuccess(resp, '创建对话失败')
  return data.session
}

/** 获取当前用户的独立对话列表。 */
export async function fetchMyChatSessions(params = {}) {
  const query = new URLSearchParams()
  if (params.page) query.set('page', params.page)
  if (params.limit) query.set('limit', params.limit)
  const resp = await fetch(`/api/chat/my-sessions?${query}`)
  return assertJsonSuccess(resp, '获取对话列表失败')
}

/** 更新独立对话或会话标题。 */
export async function updateChatTitle(sessionId, title) {
  const resp = await fetch(`/api/chat/${sessionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
  const data = await assertJsonSuccess(resp, '更新标题失败')
  return data.session
}

/** 删除指定对话会话。 */
export async function deleteChat(sessionId) {
  const resp = await fetch(`/api/chat/${sessionId}`, { method: 'DELETE' })
  await assertJsonSuccess(resp, '删除对话失败')
  return true
}
