<script setup>
import { computed, onMounted, provide } from 'vue'

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
const { sidebarCollapsed } = useWorkspaceNav()

const sidebarOffset = computed(() => sidebarCollapsed.value ? 64 : 256)

provide(TOAST_INJECTION_KEY, pushToast)

onMounted(() => {
  initTheme()
})
</script>

<template>
  <RouterView />

  <Teleport to="body">
    <ToastContainer :toasts="toasts" :sidebar-offset="sidebarOffset" />
  </Teleport>

  <BaseLoading :visible="loading" @after-enter="notifyEnterCompleted" />
</template>
