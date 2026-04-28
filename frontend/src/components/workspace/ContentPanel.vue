<script setup>
/**
 * ContentPanel.vue
 * 右侧内容面板布局 — Linear 风格
 * 支持：顶部栏（标题 + 步骤 tab + 工具栏）+ 主内容区 + 可选右侧属性栏
 */
import { PanelLeft } from 'lucide-vue-next'
import { useWorkspaceNav } from '@/composables/useWorkspaceNav.js'
import BaseTooltip from '@/components/base/BaseTooltip.vue'

defineProps({
  title: { type: String, required: true },
  steps: { type: Array, default: () => [] },  // [{ label, active, done }]
  currentStep: { type: Number, default: -1 }, // -1 = 不显示步骤
})

const emit = defineEmits(['step-click'])

const { sidebarMode, isMobile, toggleSidebar } = useWorkspaceNav()
</script>

<template>
  <div
    class="h-full flex flex-col rounded-none lg:rounded-lg brand-btn overflow-hidden dark:!bg-white/[0.04] transition-colors duration-200">
    <!-- 顶部栏 -->
    <header
      class="flex items-center h-14 px-4 border-b border-gray-200 dark:border-white/[0.08] shrink-0 gap-4 transition-colors">
      <!-- 操作按钮组 -->
      <div class="flex items-center bg-gray-100/50 dark:bg-white/[0.04] rounded-full p-1 gap-0.5 -ml-1">
        <BaseTooltip :text="isMobile ? '打开菜单' : (sidebarMode === 'collapsed-icon' ? '展开侧边栏' : '收起侧边栏')"
          placement="bottom">
          <button @click="toggleSidebar"
            class="flex h-8 w-8 items-center justify-center rounded-full text-gray-500 hover:bg-white dark:text-[#8a8f98] dark:hover:bg-white/[0.08] dark:hover:text-white transition-all">
            <PanelLeft class="w-4 h-4" :class="!isMobile && sidebarMode === 'expanded' ? 'rotate-180' : ''" />
          </button>
        </BaseTooltip>

        <!-- 额外的头部操作插槽 (如 AI 新建对话) -->
        <slot name="header-actions"></slot>
      </div>

      <!-- 标题 -->
      <h2 class="text-sm font-medium text-gray-900 dark:text-[#f7f8f8] shrink-0 transition-colors">{{ title }}</h2>

      <!-- 步骤 tab（可选） -->
      <div v-if="steps.length" class="flex items-center gap-1 ml-2">
        <button v-for="(s, i) in steps" :key="i" @click="emit('step-click', i)"
          class="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs transition-colors" :class="i === currentStep
            ? 'brand-gradient-bg text-white shadow-sm font-medium'
            : s.done
              ? 'text-gray-500 dark:text-[#8a8f98] hover:bg-gray-100 dark:hover:bg-white/[0.04] hover:text-gray-700 dark:hover:text-[#d0d6e0]'
              : 'text-gray-400 dark:text-[#62666d] cursor-default'">
          <span class="flex h-4 w-4 items-center justify-center rounded text-[10px] transition-colors" :class="s.done
            ? 'bg-[rgb(129,115,223)] text-white'
            : i === currentStep
              ? 'bg-white/20 text-white'
              : 'bg-gray-100 dark:bg-white/[0.04] text-gray-400 dark:text-[#62666d]'">
            <i v-if="s.done" class="fa-solid fa-check text-[8px]"></i>
            <span v-else>{{ i + 1 }}</span>
          </span>
          <span>{{ s.label }}</span>
        </button>
      </div>

      <!-- 左侧附加操作 -->
      <div v-if="$slots.actions" class="flex items-center gap-1 text-gray-500 dark:text-[#62666d] transition-colors">
        <slot name="actions"></slot>
      </div>

      <!-- 右侧工具栏 -->
      <div class="flex shrink-0 items-center gap-3 ml-auto">
        <!-- 子组件可通过 Teleport 注入内容 -->
        <div :id="'panel-toolbar-' + title" class="flex items-center gap-3"></div>
        <slot name="toolbar"></slot>
      </div>
    </header>

    <!-- 内容区：主体 + 可选右侧栏 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 主内容 -->
      <div class="flex-1 min-h-0 overflow-y-auto px-4 py-3 flex flex-col">
        <slot></slot>
      </div>

      <!-- 右侧属性栏（可选） -->
      <aside v-if="$slots.sidebar"
        class="hidden lg:flex w-80 shrink-0 flex-col border-l border-gray-200 dark:border-white/[0.05] overflow-y-auto transition-colors">
        <slot name="sidebar"></slot>
      </aside>
    </div>
  </div>
</template>

<style scoped></style>
