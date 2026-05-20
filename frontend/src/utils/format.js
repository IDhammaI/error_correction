/**
 * 文本格式化工具。
 *
 * 保持选项文本在渲染前统一转成字符串，避免 null/undefined 进入模板。
 */
/** 格式化选项文本 */
export const formatOption = (s) => String(s || '')
