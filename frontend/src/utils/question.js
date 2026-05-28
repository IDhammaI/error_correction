/**
 * Question content helpers.
 */
const cleanInlineMath = (text) => {
  return String(text || '')
    .replace(/\\\((.*?)\\\)/g, '$1')
    .replace(/\\\[(.*?)\\\]/g, '$1')
    .replace(/\${1,2}([^$]+)\${1,2}/g, '$1')
    .replace(/\\sqrt\s*\{([^{}]+)\}/g, '√$1')
    .replace(/\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}/g, '$1/$2')
    .replace(/\\angle/g, '∠')
    .replace(/\\overline\s*\{([^{}]+)\}/g, '$1')
    .replace(/\\bar\s*\{([^{}]+)\}/g, '$1')
    .replace(/\\[a-zA-Z]+/g, '')
    .replace(/[{}]/g, '')
    .replace(/\\+/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

const safeTruncate = (text, maxLen) => {
  if (maxLen <= 0 || text.length <= maxLen) return text
  let end = maxLen
  while (end > Math.max(0, maxLen - 8) && /[\\$({[]/.test(text[end - 1] || '')) end -= 1
  return text.slice(0, end).trimEnd() + '...'
}

export const getQuestionSnippet = (q, maxLen = 0, fallback = '') => {
  if (!q) return fallback
  const blocks = q.content_blocks || q.content_json || []
  const texts = blocks.filter(b => b.block_type === 'text').map(b => b.content || '')
  const raw = cleanInlineMath(texts.join(' ').replace(/<[^>]+>/g, ''))
  if (!raw) return fallback
  return safeTruncate(raw, maxLen)
}

const clamp = (value, min, max) => Math.min(max, Math.max(min, value))

const daysSince = (iso) => {
  if (!iso) return 30
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return 30
  return Math.max(0, Math.floor((Date.now() - date.getTime()) / 86400000))
}

/**
 * 计算错题复习优先级。
 * 分数来自题目的真实状态、更新时间和资料完整度，而不是固定展示值。
 */
export const calculateQuestionPriority = (question) => {
  if (!question) return 0

  const status = question.review_status || '待复习'
  const statusScore = {
    待复习: 58,
    复习中: 44,
    已掌握: 18,
  }[status] ?? 50

  const staleDays = daysSince(question.updated_at || question.created_at)
  const staleScore = clamp(staleDays * 2, 0, 26)
  const answerScore = question.user_answer ? 0 : 8
  const analysisScore = question.answer ? 0 : 6
  const correctionScore = question.needs_correction ? 8 : 0
  const tagScore = question.knowledge_tags?.length ? 0 : 4
  const mediaScore = question.has_image || question.has_formula ? 2 : 0

  return Math.round(clamp(
    statusScore + staleScore + answerScore + analysisScore + correctionScore + tagScore + mediaScore,
    5,
    99,
  ))
}
