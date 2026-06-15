<script setup>
/**
 * ContentPanel.vue
 * Workspace content shell: title bar, optional step tabs, tool slots, main content,
 * and an optional resizable right sidebar.
 */
import { computed, onBeforeUnmount, onMounted, ref, useSlots } from 'vue'
import { PanelLeft } from 'lucide-vue-next'
import { useWorkspaceNav } from '@/composables/useWorkspaceNav.js'
import BaseBreadcrumb from '@/components/base/BaseBreadcrumb.vue'
import PanelStepTabs from '@/components/features/app/layout/PanelStepTabs.vue'

const props = defineProps({
  title: { type: String, required: true },
  steps: { type: Array, default: () => [] },
  currentStep: { type: Number, default: -1 },
  sidebarOpen: { type: Boolean, default: undefined },
  breadcrumbs: { type: Array, default: () => [] },
})

const emit = defineEmits(['step-click'])
const slots = useSlots()

const { isMobile, canHover, mobileDrawerOpen, toggleSidebar } = useWorkspaceNav()

const SIDEBAR_WIDTH_KEY = 'content_panel_sidebar_width_v1'
const SIDEBAR_MIN_WIDTH = 280
const SIDEBAR_MAX_WIDTH = 520
const sidebarWidth = ref(320)
const resizingSidebar = ref(false)

const sidebarWidthPx = computed(() => `${sidebarWidth.value}px`)
const hasSidebar = computed(() => Boolean(slots.sidebar))
const isSidebarOpen = computed(() => hasSidebar.value && (props.sidebarOpen ?? true))

const clampSidebarWidth = (width) => Math.min(SIDEBAR_MAX_WIDTH, Math.max(SIDEBAR_MIN_WIDTH, width))

const onSidebarResizeMove = (event) => {
  if (!resizingSidebar.value) return
  sidebarWidth.value = clampSidebarWidth(window.innerWidth - event.clientX)
}

const stopSidebarResize = () => {
  if (!resizingSidebar.value) return
  resizingSidebar.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  try { localStorage.setItem(SIDEBAR_WIDTH_KEY, String(sidebarWidth.value)) } catch (_) { }
  window.removeEventListener('pointermove', onSidebarResizeMove)
  window.removeEventListener('pointerup', stopSidebarResize)
  window.removeEventListener('pointercancel', stopSidebarResize)
}

const startSidebarResize = (event) => {
  if (isMobile.value) return
  event.preventDefault()
  resizingSidebar.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  window.addEventListener('pointermove', onSidebarResizeMove)
  window.addEventListener('pointerup', stopSidebarResize)
  window.addEventListener('pointercancel', stopSidebarResize)
}

onMounted(() => {
  let saved = null
  try { saved = Number(localStorage.getItem(SIDEBAR_WIDTH_KEY)) } catch (_) { }
  if (saved) sidebarWidth.value = clampSidebarWidth(saved)
})

onBeforeUnmount(stopSidebarResize)
</script>

<template>
  <div
    class="flex h-full flex-col overflow-hidden rounded-none brand-btn transition-colors duration-200 dark:!bg-white/[0.04] lg:rounded-lg">
    <header
      class="flex h-14 shrink-0 items-center gap-4 border-b border-gray-200 bg-white/70 px-4 transition-colors dark:border-white/[0.08] dark:bg-white/[0.065]">
      <button v-if="isMobile" @click="toggleSidebar"
        class="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-md text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-[#62666d] dark:hover:bg-white/[0.04] dark:hover:text-[#8a8f98]"
        :title="canHover ? (mobileDrawerOpen ? '关闭侧边栏' : '打开侧边栏') : null">
        <PanelLeft
          class="h-4 w-4 transition-transform"
          :class="mobileDrawerOpen ? 'rotate-180' : ''"
        />
      </button>

      <BaseBreadcrumb v-if="breadcrumbs.length" :items="breadcrumbs" class="min-w-0 shrink" />
      <h2 v-else class="shrink-0 text-sm font-medium text-gray-900 transition-colors dark:text-[#f7f8f8]">{{ title }}</h2>

      <PanelStepTabs :steps="steps" :current-step="currentStep" @step-click="(index) => emit('step-click', index)" />

      <div v-if="$slots.actions" class="flex items-center gap-1 text-gray-500 transition-colors dark:text-[#62666d]">
        <slot name="actions"></slot>
      </div>

      <div class="ml-auto flex shrink-0 items-center gap-3">
        <div v-if="$slots['header-actions']"
          class="flex items-center gap-0.5 rounded-full bg-gray-100/50 p-1 dark:bg-white/[0.04]">
          <slot name="header-actions"></slot>
        </div>
        <div :id="'panel-toolbar-' + title" class="flex items-center gap-3"></div>
        <slot name="toolbar"></slot>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden p-3">
      <div class="flex min-h-0 flex-1 flex-col overflow-y-auto pr-2">
        <slot></slot>
      </div>

      <aside v-if="hasSidebar"
        class="relative hidden shrink-0 overflow-hidden transition-[width,border-color] duration-[280ms] ease-[var(--sidebar-transition-timing)] lg:flex"
        :class="[
          resizingSidebar ? '!transition-none' : '',
          isSidebarOpen ? 'border-l border-gray-200 dark:border-white/[0.05]' : 'border-l border-transparent'
        ]"
        :style="{ width: isSidebarOpen ? sidebarWidthPx : '0px' }">
        <button
          v-show="isSidebarOpen"
          class="absolute inset-y-0 left-0 z-20 w-2 -translate-x-1 cursor-col-resize outline-none transition-colors hover:bg-[rgb(var(--accent-rgb)/0.14)] focus-visible:bg-[rgb(var(--accent-rgb)/0.18)]"
          title="拖动调整宽度"
          @pointerdown="startSidebarResize"
        ></button>
        <div
          class="flex h-full shrink-0 flex-col overflow-y-auto transition-[opacity,transform] duration-[280ms] ease-[var(--sidebar-transition-timing)]"
          :class="isSidebarOpen ? 'translate-x-0 opacity-100' : 'pointer-events-none translate-x-4 opacity-0'"
          :style="{ width: sidebarWidthPx }">
          <slot name="sidebar"></slot>
        </div>
      </aside>
    </div>
  </div>
</template>
