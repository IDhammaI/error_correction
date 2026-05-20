/**
 * HTML 富文本安全工具。
 *
 * 后端会返回题目表格、图片和基础富文本；渲染前必须经过白名单净化。
 */
import DOMPurify from 'dompurify'

/** 判断内容是否包含 HTML 表格或列表等富文本标签 */
export const isHtml = (s) => /<\/?(?:table|tr|td|th|thead|tbody|ul|ol|li|img|a|strong|em)\b/i.test(s || '')

/** 允许渲染的 HTML 标签白名单 */
export const ALLOWED_HTML_TAGS = [
  'table', 'tr', 'td', 'th', 'thead', 'tbody',
  'ul', 'ol', 'li',
  'p', 'br', 'span', 'b', 'i', 'em', 'strong', 'sub', 'sup',
  'img', 'a',
]

/** 使用 DOMPurify 过滤 HTML，仅保留白名单标签和属性，防止 XSS */
export const sanitizeHtml = (html) => {
  if (!html) return ''
  // 兼容旧数据的图片路径，并修复历史数据里保存的转义换行和引号。
  let fixed = html.replace(/src="imgs\//g, 'src="/images/')
  fixed = fixed.replace(/\\n/g, '\n').replace(/\\"/g, '"')
  return DOMPurify.sanitize(fixed, {
    ALLOWED_TAGS: ALLOWED_HTML_TAGS,
    ALLOWED_ATTR: ['src', 'alt', 'href', 'target', 'rel', 'title', 'class', 'style'],
    ALLOW_DATA_ATTR: false
  })
}
