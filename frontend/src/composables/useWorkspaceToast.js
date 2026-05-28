import { ref } from 'vue'

/**
 * useWorkspaceToast.js
 * 工作台全局 Toast 队列。
 *
 * App.vue 提供 pushToast，业务组件通过 useToast 注入后调用。
 */
export function useWorkspaceToast() {
  const toasts = ref([])
  let toastId = 0

  const normalizeToastPayload = (message, options = {}) => {
    if (message && typeof message === 'object') {
      return {
        title: message.title || message.message || '',
        description: message.description || '',
        action: message.action || null,
      }
    }
    return {
      title: String(message || ''),
      description: options.description || '',
      action: options.action || null,
    }
  }

  /**
   * 插入一条 Toast，并按 timeout 自动移除；最多保留最近 5 条。
   */
  const pushToast = (type, message, timeout = 2600, options = {}) => {
    const id = ++toastId
    toasts.value = [{ id, type, ...normalizeToastPayload(message, options) }, ...toasts.value].slice(0, 5)
    if (timeout > 0) {
      window.setTimeout(() => {
        toasts.value = toasts.value.filter(t => t.id !== id)
      }, timeout)
    }
  }

  const dismissToast = (id) => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  return { toasts, pushToast, dismissToast }
}
