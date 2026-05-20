/**
 * 题目内容工具。
 *
 * 题目可能来自 content_blocks 或旧版 content_json，摘要提取需要兼容两种结构。
 */
/** 从题目的 content_json 中提取纯文本摘要 */
export const getQuestionSnippet = (q, maxLen = 0, fallback = '') => {
  if (!q) return fallback
  const blocks = q.content_blocks || q.content_json || []
  const texts = blocks.filter(b => b.block_type === 'text').map(b => b.content || '')
  const raw = texts.join(' ').replace(/<[^>]+>/g, '').trim()
  if (!raw) return fallback
  if (maxLen > 0 && raw.length > maxLen) return raw.slice(0, maxLen) + '…'
  return raw
}
