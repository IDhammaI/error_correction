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

  /**
   * 插入一条 Toast，并按 timeout 自动移除；最多保留最近 5 条。
   */
  const pushToast = (type, message, timeout = 2600) => {
    const id = ++toastId
    toasts.value = [{ id, type, message }, ...toasts.value].slice(0, 5)
    if (timeout > 0) {
      window.setTimeout(() => {
        toasts.value = toasts.value.filter(t => t.id !== id)
      }, timeout)
    }
  }

  return { toasts, pushToast }
}
