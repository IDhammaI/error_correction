/**
 * 缩放工具。
 *
 * 图片预览通过滚轮调整 scale，这里统一处理步进和上下界。
 */
/** 计算滚轮缩放后的 scale 值 */
export const clampScale = (current, deltaY, min = 0.25, max = 5) => {
  const delta = deltaY > 0 ? -0.1 : 0.1
  return Math.min(max, Math.max(min, current + delta))
}
