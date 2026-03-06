import DOMPurify from 'dompurify'

/** 生成文件唯一标识 */
export const fileKey = (file) => `${file.name}|${file.size}|${file.lastModified}`

/** 格式化选项文本 */
export const formatOption = (s) => String(s || '')

/** 判断内容是否包含 HTML 表格标签 */
export const isHtml = (s) => /<\/?(?:table|tr|td|th|thead|tbody)\b/i.test(s || '')

/** 允许渲染的 HTML 标签白名单 */
export const ALLOWED_HTML_TAGS = [
  'table', 'tr', 'td', 'th', 'thead', 'tbody',
  'p', 'br', 'span', 'b', 'i', 'em', 'strong', 'sub', 'sup',
]

/** 使用 DOMPurify 过滤 HTML，仅保留白名单标签 */
export const sanitizeHtml = (html) =>
  DOMPurify.sanitize(html, { ALLOWED_TAGS: ALLOWED_HTML_TAGS })

/** 计算滚轮缩放后的 scale 值 */
export const clampScale = (current, deltaY, min = 0.25, max = 5) => {
  const delta = deltaY > 0 ? -0.1 : 0.1
  return Math.min(max, Math.max(min, current + delta))
}
