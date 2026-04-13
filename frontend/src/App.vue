<script setup>
import { onMounted } from 'vue'

// ── 全局组件 ──────────────────────────────────────────
import BaseLoading from '@/components/base/BaseLoading.vue'

// ── 全局状态与逻辑 (Composables) ──────────────────────
import { usePageTransition } from '@/composables/usePageTransition.js'
import { useTheme } from '@/composables/useTheme.js'

// 获取页面切换的加载状态及动画完成回调
const { loading, notifyEnterCompleted } = usePageTransition()
// 获取主题初始化方法
const { initTheme } = useTheme()

// ── 生命周期 ──────────────────────────────────────────
onMounted(() => {
  // 应用启动时初始化：根据本地存储或系统偏好设置深色/浅色模式
  initTheme()
})
</script>

<template>
  <!-- 路由出口：渲染当前路径匹配的页面组件 -->
  <RouterView />

  <!-- 全局加载遮罩：配合 usePageTransition 控制路由切换时的平滑过渡动画 -->
  <BaseLoading :visible="loading" @after-enter="notifyEnterCompleted" />
</template>
