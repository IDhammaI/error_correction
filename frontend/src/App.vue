<script setup>
import { onMounted } from 'vue'

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
  <RouterView v-slot="{ Component }">
    <Transition name="page-fade" mode="out-in" appear>
      <component :is="Component" />
    </Transition>
  </RouterView>
</template>

<style>
.page-fade-enter-active {
  transition: opacity 0.28s ease;
}
.page-fade-leave-active {
  transition: opacity 0.18s ease;
}
.page-fade-enter-from {
  opacity: 0;
}
.page-fade-leave-to {
  opacity: 0;
}
</style>
