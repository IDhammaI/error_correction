<script setup>
import { onMounted } from 'vue'
import AppLoading from './components/AppLoading.vue'
import { usePageTransition } from './composables/usePageTransition.js'

const { loading, notifyEnterCompleted } = usePageTransition()

// 尽早应用已保存的主题，减少闪烁
onMounted(() => {
  const saved = localStorage.getItem('theme')
  const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches
  const initial = saved || (prefersDark ? 'dark' : 'light')
  if (initial === 'dark') document.documentElement.classList.add('dark')
  else document.documentElement.classList.remove('dark')
})
</script>

<template>
  <RouterView />
  <AppLoading :visible="loading" @after-enter="notifyEnterCompleted" />
</template>
