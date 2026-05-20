/**
 * 笔记预览工具。
 *
 * 笔记卡片只需要纯文本摘要，因此这里把 Markdown、图片和 LaTeX 尽量降级成可读文本。
 */
/** 简化 LaTeX 公式并生成纯文本预览 */
export const getNotePreviewText = (text, maxLen = 120) => {
  if (!text) return ''

  /** 将 LaTeX 片段降级成适合卡片摘要展示的近似纯文本。 */
  const simplifyLatex = (math) => {
    if (!math) return ''
    math = math.trim()

    // 常见符号映射表：把公式命令压缩成适合列表预览的短文本。
    const symbols = {
      'frac\\s*\\{([^{}]*)\\}\\s*\\{([^{}]*)\\}': '($1/$2)',
      'sqrt\\s*\\{([^{}]*)\\}': '√($1)',
      'cdot': '·', 'times': '×', 'div': '÷', 'pm': '±', 'neq': '≠', 'approx': '≈', 'leq': '≤', 'geq': '≥',
      'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ', 'epsilon': 'ε', 'zeta': 'ζ', 'eta': 'η', 'theta': 'θ',
      'iota': 'ι', 'kappa': 'κ', 'lambda': 'λ', 'mu': 'μ', 'nu': 'ν', 'xi': 'ξ', 'omicron': 'ο', 'pi': 'π',
      'rho': 'ρ', 'sigma': 'σ', 'tau': 'τ', 'upsilon': 'υ', 'phi': 'φ', 'chi': 'χ', 'psi': 'ψ', 'omega': 'ω',
      'Delta': 'Δ', 'Gamma': 'Γ', 'Theta': 'Θ', 'Lambda': 'Λ', 'Xi': 'Ξ', 'Pi': 'Π', 'Sigma': 'Σ', 'Upsilon': 'Υ',
      'Phi': 'Φ', 'Psi': 'Ψ', 'Omega': 'Ω',
      'sum': '∑', 'int': '∫', 'infty': '∞', 'to': '→', 'Rightarrow': '⇒', 'Leftrightarrow': '⇔',
      'parallel': '//', 'perp': '⊥',
      'text\\s*\\{([^{}]*)\\}': '$1', 'mathbf\\s*\\{([^{}]*)\\}': '$1', 'mathrm\\s*\\{([^{}]*)\\}': '$1'
    }

    Object.entries(symbols).forEach(([key, val]) => {
      math = math.replace(new RegExp(`\\\\${key}`, 'g'), val)
    })

    // 处理矩阵/方程组环境，保留行列信息但不尝试完整还原排版。
    math = math.replace(/\\begin\s*\{([bpvBpv]?matrix|cases|aligned|array)\}([\s\S]*?)\\end\s*\{\1\}/g, (match, env, content) => {
      let matrix = content.replace(/\\\\/g, '; ') // 换行替换为分号
      matrix = matrix.replace(/&/g, ', ') // 列分隔符替换为逗号
      return `[${matrix.trim()}]`
    })

    // 清理多余指令和格式
    math = math.replace(/\\left|\\right/g, '')
    math = math.replace(/\\[a-zA-Z]+/g, '')
    return ` ${math.replace(/\s+/g, ' ')} `
  }

  let s = text

  // 预览列表里不展示图片路径，否则摘要会被本地/服务端 URL 淹没。
  s = s.replace(/!\[[^\]]*\]\([^)]+\)/g, '')

  // 提取和简化 LaTeX 公式（先处理公式，避免破坏 _ 和 -）
  // 块级 $$...$$
  s = s.replace(/\$\$([\s\S]*?)\$\$/g, (match, content) => simplifyLatex(content))
  // 行内 $...$
  s = s.replace(/\$([^$]+)\$/g, (match, content) => simplifyLatex(content))
  // 行内 \(...\)
  s = s.replace(/\\\(([\s\S]*?)\\\)/g, (match, content) => simplifyLatex(content))
  // 块级 \[...\]
  s = s.replace(/\\\[([\s\S]*?)\\\]/g, (match, content) => simplifyLatex(content))

  // 简化链接：保留文本，移除 URL
  s = s.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')

  // 移除 Markdown 标题符号
  s = s.replace(/^#{1,6}\s+/gm, '')

  // 移除 Markdown 格式符号
  s = s.replace(/[*`>\-_]/g, '')

  // 清理多余空格和换行
  s = s.replace(/\s+/g, ' ').trim()
  if (s.length > maxLen) return s.slice(0, maxLen) + '...'
  return s
}
