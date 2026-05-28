<script setup>
import { onMounted, provide } from 'vue'

import BaseLoading from '@/components/base/BaseLoading.vue'
import BaseToastContainer from '@/components/base/BaseToastContainer.vue'

import { usePageTransition } from '@/composables/usePageTransition.js'
import { useTheme } from '@/composables/useTheme.js'
import { useWorkspaceToast } from '@/composables/useWorkspaceToast.js'
import { TOAST_INJECTION_KEY } from '@/composables/useToast.js'
import { useWorkspaceNav } from '@/composables/useWorkspaceNav.js'

const { loading, notifyEnterCompleted } = usePageTransition()
const { initTheme } = useTheme()
const { toasts, pushToast, dismissToast } = useWorkspaceToast()
const { sidebarOffset } = useWorkspaceNav()

// Provide the global toast API to app pages and nested components.
provide(TOAST_INJECTION_KEY, pushToast)

onMounted(() => {
  // Restore the persisted theme after app startup.
  initTheme()
})
</script>

<template>
  <RouterView />

  <BaseToastContainer :toasts="toasts" :sidebar-offset="sidebarOffset" @dismiss="dismissToast" />

  <BaseLoading :visible="loading" @after-enter="notifyEnterCompleted" />
</template>
