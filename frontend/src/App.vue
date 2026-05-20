<script setup>
import { onMounted, provide } from 'vue'

import BaseLoading from '@/components/base/BaseLoading.vue'
import ToastContainer from '@/components/base/ToastContainer.vue'

import { usePageTransition } from '@/composables/usePageTransition.js'
import { useTheme } from '@/composables/useTheme.js'
import { useWorkspaceToast } from '@/composables/useWorkspaceToast.js'
import { TOAST_INJECTION_KEY } from '@/composables/useToast.js'
import { useWorkspaceNav } from '@/composables/useWorkspaceNav.js'

const { loading, notifyEnterCompleted } = usePageTransition()
const { initTheme } = useTheme()
const { toasts, pushToast } = useWorkspaceToast()
const { sidebarOffset } = useWorkspaceNav()

// 向子组件提供全局 toast 方法，页面内可通过 useToast 统一触发消息。
provide(TOAST_INJECTION_KEY, pushToast)

onMounted(() => {
  // 应用启动后读取本地主题偏好，并同步到根节点样式。
  initTheme()
})
</script>

<template>
  <!-- 路由出口：渲染当前匹配路由对应的页面。 -->
  <RouterView />

  <!-- Toast 浮层：容器自身使用 fixed 定位，不需要脱离 App 根组件。 -->
  <ToastContainer :toasts="toasts" :sidebar-offset="sidebarOffset" />

  <!-- 全局加载遮罩：用于跨布局页面切换的 loading 展示。 -->
  <BaseLoading :visible="loading" @after-enter="notifyEnterCompleted" />
</template>
