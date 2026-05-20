import { onMounted, onBeforeUnmount } from 'vue'

/**
 * 点击外部关闭的通用 composable
 * @param {string} selector - CSS 选择器，点击该选择器外部时触发关闭
 * @param {() => void} onClose - 关闭回调
 */
export function useClickOutside(selector, onClose) {
  /**
   * 捕获文档点击事件，点击目标选择器外部时触发关闭。
   */
  const handler = (e) => {
    if (!e.target.closest(selector)) {
      onClose()
    }
  }

  // 组件挂载时绑定全局点击监听。
  onMounted(() => {
    document.addEventListener('click', handler)
  })

  // 组件卸载时移除监听，避免回调残留。
  onBeforeUnmount(() => {
    document.removeEventListener('click', handler)
  })
}
