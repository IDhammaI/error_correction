/**
 * Markdown 渲染工具。
 *
 * 聊天内容同时包含 Markdown、代码块和 LaTeX；渲染时需要保护数学片段，
 * 避免 marked 把公式中的下划线、星号等字符当作 Markdown 语法处理。
 */
import DOMPurify from 'dompurify'
import { ALLOWED_HTML_TAGS } from './html.js'

/** 在 Markdown 渲染前暂存数学公式，避免公式内容被 marked 当作普通 Markdown 改写。 */
const protectMathMarkdown = (text) => {
  const placeholders = []
  if (!text) return { text: '', restore: (html) => html }
  const codePlaceholders = []
  /** 暂存代码片段，避免代码中的 $ 符号被误识别为数学公式。 */
  const stashCode = (match) => {
    const key = `@@CODE_${codePlaceholders.length}@@`
    codePlaceholders.push(match)
    return key
  }

  let s = String(text)
  // 先暂存代码块/行内代码，避免其中的 $ 或 LaTeX 片段被误判为公式。
  s = s
    .replace(/```[\s\S]*?```/g, stashCode)
    .replace(/`[^`\n]+`/g, stashCode)

  s = s
    .replace(/\\\[((?:.|\n)*?)\\\]/g, (_, content) => `$$${content}$$`)
    .replace(/\\\(((?:.|\n)*?)\\\)/g, (_, content) => `$${content}$`)

  const stash = (match) => {
    const key = `@@MATH_${placeholders.length}@@`
    placeholders.push(match)
    return key
  }

  s = s
    .replace(/\$\$[\s\S]*?\$\$/g, stash)
    .replace(/\$(?!\$)[\s\S]*?(?<!\$)\$/g, stash)

  // 部分模型会直接输出裸 LaTeX 命令，补上 $...$ 后 MathJax 才能在流式内容中识别。
  s = s.replace(/(?<![A-Za-z0-9:\\\\/])\\(?:frac|sqrt|overline|bar|hat|vec|angle|triangle|pi|cdot|times|leq|geq|neq|approx|sum|int|Delta|alpha|beta|gamma|theta|lambda|mu|sigma|omega)(?:\s*\{[^{}\n]*\}){0,2}(?:\s*[_^]\s*\{?[\w+\-=]+\}?){0,2}/g, (match) => `$${match}$`)

  s = s
    .replace(/\$\$[\s\S]*?\$\$/g, stash)
    .replace(/\$(?!\$)[\s\S]*?(?<!\$)\$/g, stash)

  s = s.replace(/@@CODE_(\d+)@@/g, (_, index) => codePlaceholders[Number(index)] || '')

  return {
    text: s,
    restore: (html) => html.replace(/@@MATH_(\d+)@@/g, (_, index) => placeholders[Number(index)] || ''),
  }
}

/** 将 Markdown 文本渲染为净化后的 HTML（用于聊天消息） */
export const renderMarkdown = (text) => {
  if (!text) return ''
  // marked 通过 CDN 注入到 window；测试或降级场景下没有 marked 时直接返回原文本。
  const parse = window.marked?.parse ?? ((s) => s)
  const math = protectMathMarkdown(text)
  const html = math.restore(parse(math.text, { breaks: true }))
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      ...ALLOWED_HTML_TAGS,
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li', 'code', 'pre', 'blockquote', 'hr',
      'a', 'img',
    ],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'src', 'alt'],
  })
}
