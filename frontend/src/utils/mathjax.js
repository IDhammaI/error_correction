/**
 * MathJax 渲染工具。
 *
 * MathJax 由页面 CDN 异步加载，调用方可能早于脚本就绪，因此这里统一等待。
 */
/** 等待 MathJax 加载就绪（最多等 10 秒） */
const waitForMathJax = () => new Promise((resolve) => {
  const mj = window.MathJax
  if (mj && typeof mj.typesetPromise === 'function') return resolve(mj)
  let tries = 0
  const timer = setInterval(() => {
    const mj = window.MathJax
    if (mj && typeof mj.typesetPromise === 'function') {
      clearInterval(timer)
      resolve(mj)
    } else if (++tries > 100) {
      clearInterval(timer)
      resolve(null)
    }
  }, 100)
})

/** 对指定元素触发 MathJax 公式渲染 */
export const typesetMath = async (el) => {
  const mj = await waitForMathJax()
  if (!mj) return
  try {
    if (el) {
      // 局部重排前先清理旧渲染缓存，避免动态内容重复 typeset 后残留。
      mj.typesetClear?.([el])
      await mj.typesetPromise([el])
    } else {
      await mj.typesetPromise()
    }
  } catch (_) { }
}
