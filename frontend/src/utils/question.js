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
