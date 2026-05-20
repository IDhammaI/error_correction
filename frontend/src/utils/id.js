/**
 * ID 工具。
 *
 * 优先使用 crypto.randomUUID；旧环境回退到 getRandomValues，仍保持随机性。
 */
/** 生成唯一 ID（兼容非 HTTPS 上下文，使用 getRandomValues 确保密码学安全） */
export const genId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  const bytes = new Uint8Array(16)
  crypto.getRandomValues(bytes)
  return Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('')
}
