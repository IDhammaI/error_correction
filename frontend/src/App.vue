<script setup>
import { onMounted } from 'vue'
import AppLoading from './components/AppLoading.vue'
import { usePageTransition } from './composables/usePageTransition.js'
import { useTheme } from './composables/useTheme.js'

const { loading, notifyEnterCompleted } = usePageTransition()
const { initTheme } = useTheme()

onMounted(() => {
  initTheme()
})
</script>

<template>
  <RouterView />
  <AppLoading :visible="loading" @after-enter="notifyEnterCompleted" />
</template>
