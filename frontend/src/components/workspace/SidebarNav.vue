<script setup>
/**
 * SidebarNav.vue
 * 工作台左侧边栏导航（PC 端双模式 + 移动端抽屉）+ 底部 Tab 导航（移动端）
 */
import { computed } from 'vue'
import { PanelLeft, MessageSquarePlus } from 'lucide-vue-next'
import BaseLogo from '@/components/base/BaseLogo.vue'
import BaseDropdown from '@/components/base/BaseDropdown.vue'
import BaseTooltip from '@/components/base/BaseTooltip.vue'

const props = defineProps({
  currentView: { type: String, required: true },
  currentSettingsSubView: { type: String, default: 'profile' },
  settingsNavItems: { type: Array, default: () => [] },
  lastWorkspaceView: { type: String, default: 'workspace' },
  currentUser: { type: Object, default: null },
  isDark: { type: Boolean, default: true },
  theme: { type: String, default: 'dark' },
  // 导航配置
  navGroups: { type: Array, required: true },
  workspaceViews: { type: Object, required: true },
  collapsedGroups: { type: Object, required: true },
  // 指示器
  navRef: { type: Object, default: null },
  navBtnRefs: { type: Object, required: true },
  indicatorStyle: { type: Object, default: () => ({}) },
  indicatorTransition: { type: Boolean, default: false },
  // AI 对话
  chatCollapsed: { type: Boolean, default: false },
  aiChatSessions: { type: Array, default: () => [] },
  activeAiChatId: { type: [String, Number], default: null },
  chatListRef: { type: Object, default: null },
  chatBtnRefs: { type: Object, required: true },
  chatIndicatorStyle: { type: Object, default: () => ({}) },
  chatIndicatorTransition: { type: Boolean, default: false },
  chatMenuOpenId: { type: [String, Number], default: null },
  renamingChatId: { type: [String, Number], default: null },
  renameText: { type: String, default: '' },
  // 用户菜单
  userMenuOpen: { type: Boolean, default: false },
  // 响应式状态
  sidebarMode: { type: String, default: 'expanded' }, // 'expanded' | 'collapsed-icon'
  isMobile: { type: Boolean, default: false },
  mobileDrawerOpen: { type: Boolean, default: false },
})

const emit = defineEmits([
  'update:currentView', 'update:currentSettingsSubView', 'update:collapsedGroups', 'update:chatCollapsed',
  'update:userMenuOpen', 'update:chatMenuOpenId', 'update:renameText', 'update:renamingChatId',
  'update:navRef', 'update:chatListRef',
  'navigate-home', 'logout', 'toggle-theme',
  'create-ai-chat', 'select-ai-chat',
  'start-rename-chat', 'confirm-rename-chat', 'delete-ai-chat', 'toggle-chat-menu',
  'toggle-sidebar',
])

const isSettingsView = computed(() => props.currentView === 'settings')
const isNarrow = computed(() => !props.isMobile && props.sidebarMode === 'collapsed-icon')

const setView = (view) => {
  emit('update:currentView', view)
  if (props.isMobile && props.mobileDrawerOpen) {
    emit('toggle-sidebar')
  }
}

const setSettingsEntry = (subview) => {
  emit('update:currentSettingsSubView', subview)
  if (props.isMobile && props.mobileDrawerOpen) {
    emit('toggle-sidebar')
  }
}

const openSettings = (subview = 'profile') => {
  if (props.currentView !== 'settings') {
    emit('update:currentView', 'settings')
  }
  setSettingsEntry(subview)
}

const returnToApp = () => {
  emit('update:currentView', props.lastWorkspaceView || 'workspace')
  if (props.isMobile && props.mobileDrawerOpen) {
    emit('toggle-sidebar')
  }
}

const selectChat = (s) => {
  emit('select-ai-chat', s)
  if (props.isMobile && props.mobileDrawerOpen) {
    emit('toggle-sidebar')
  }
}

const createChat = () => {
  emit('create-ai-chat')
  if (props.isMobile && props.mobileDrawerOpen) {
    emit('toggle-sidebar')
  }
}

const toggleGroup = (gi) => {
  if (isNarrow.value) return // 窄栏模式下不允许折叠分组
  const next = { ...props.collapsedGroups }
  next[gi] = !next[gi]
  emit('update:collapsedGroups', next)
}

const userDisplayName = computed(() => {
  const user = props.currentUser || {}
  return user.display_name || user.nickname || user.username || '未登录用户'
})

const userInitial = computed(() => {
  const source = userDisplayName.value || props.currentUser?.username || ''
  return source.trim()?.[0]?.toUpperCase() || '?'
})

const userQuota = computed(() => props.currentUser?.quota || null)
const userQuotaSummary = computed(() => {
  const remaining = userQuota.value?.remaining
  const total = userQuota.value?.daily_free_quota
  if (remaining == null || total == null) return ''
  return `今日剩余 ${remaining} / ${total} 次`
})
</script>

<template>
  <!-- ================== 侧边栏容器 ================== -->
  <aside
    class="flex min-h-0 flex-col z-20 transition-all duration-[var(--sidebar-transition-duration)] ease-[var(--sidebar-transition-timing)] bg-white dark:bg-[#0c0c0e] border-r border-gray-200/50 dark:border-white/[0.05] overflow-hidden"
    :class="[
      isMobile
        ? 'fixed inset-y-0 left-0 w-64 transform ' + (mobileDrawerOpen ? 'translate-x-0' : '-translate-x-full')
        : 'hidden lg:flex lg:fixed lg:left-0 lg:top-0 lg:bottom-0 ' + (isNarrow ? 'w-16' : 'w-64')
    ]">

    <!-- 设置视图 -->
    <template v-if="isSettingsView">
      <div class="flex min-h-0 flex-1 flex-col px-4 py-4 overflow-hidden">
        <button @click="returnToApp"
          class="mb-4 inline-flex items-center gap-2 px-3 pt-2 text-sm font-medium text-gray-500 dark:text-[#8a8f98] transition-colors hover:text-gray-700 dark:hover:text-white"
          :class="isNarrow ? 'justify-center px-0' : ''">
          <i class="fa-solid fa-arrow-left text-xs"></i>
          <span v-if="!isNarrow">返回应用</span>
        </button>

        <nav :ref="(el) => $emit('update:navRef', el)" class="flex flex-col gap-1.5 relative">
          <div v-if="!isNarrow"
            class="px-3 pt-2 pb-1 text-xs font-medium uppercase tracking-[0.15em] text-gray-400 dark:text-[#62666d]">
            设置
          </div>
          <div class="flex flex-col gap-1">
            <template v-for="item in settingsNavItems" :key="item.id">
              <BaseTooltip :text="item.label" :placement="isNarrow ? 'right' : 'bottom'" :disabled="!isNarrow">
                <button @click="setSettingsEntry(item.id)"
                  class="group relative z-10 flex items-center gap-3 rounded-lg border px-3 py-2 text-sm font-medium transition-colors duration-200 w-full"
                  :class="[
                    currentSettingsSubView === item.id
                      ? 'brand-gradient-bg text-white shadow-sm border-transparent'
                      : 'border-transparent text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-[#8a8f98] dark:hover:bg-white/[0.04] dark:hover:text-[#d0d6e0]',
                    isNarrow ? 'justify-center px-0' : ''
                  ]">
                  <i class="fa-solid w-4 text-center text-sm" :class="item.icon"></i>
                  <span v-if="!isNarrow">{{ item.label }}</span>
                </button>
              </BaseTooltip>
            </template>
          </div>
        </nav>
      </div>
    </template>

    <!-- 主视图 -->
    <template v-else>
      <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
        <div>
          <!-- Logo 标题区 -->
          <div class="flex h-14 items-center justify-between transition-all"
            :class="isNarrow ? 'px-3 justify-center' : 'px-4'">
            <button @click="emit('navigate-home')" class="flex min-w-0 items-center gap-2 rounded-md transition-all"
              :class="isNarrow ? 'w-10 h-10 justify-center' : 'px-1 py-1 hover:bg-gray-100 dark:hover:bg-white/[0.04]'"
              title="返回首页">
              <BaseLogo size="sm" class="shrink-0" />
              <span v-if="!isNarrow"
                class="text-sm font-semibold text-gray-900 dark:text-[#f7f8f8] transition-all duration-300 overflow-hidden whitespace-nowrap">
                智卷错题本
              </span>
            </button>
            <div v-if="!isNarrow" class="flex items-center gap-1 transition-all duration-200">
              <button @click="openSettings('profile')"
                class="flex h-7 w-7 items-center justify-center rounded-md text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-[#62666d] dark:hover:bg-white/[0.04] dark:hover:text-[#8a8f98] transition-colors"
                title="系统设置">
                <i class="fa-solid fa-gear text-xs"></i>
              </button>
            </div>
          </div>

          <!-- 视图切换菜单 -->
          <nav :ref="(el) => $emit('update:navRef', el)" class="flex flex-col gap-1.5 relative transition-all"
            :class="isNarrow ? 'px-3' : 'px-4'">

            <template v-for="(group, gi) in navGroups" :key="gi">
              <!-- 分组标题（可折叠） -->
              <button v-if="group.label && !isNarrow" @click="group.collapsible && toggleGroup(gi)"
                class="flex items-center gap-1 px-3 mt-6 pb-2 text-xs font-medium uppercase tracking-[0.15em] text-gray-400 hover:text-gray-700 dark:text-[#62666d] dark:hover:text-[#8a8f98] transition-colors"
                :class="group.collapsible ? 'cursor-pointer' : 'cursor-default'">
                <span>{{ group.label }}</span>
                <i v-if="group.collapsible"
                  class="fa-solid fa-play text-[8px] text-gray-400 dark:text-[#62666d] transition-transform duration-200"
                  :class="collapsedGroups[gi] ? '' : 'rotate-90'"></i>
              </button>

              <!-- 分组内容（grid 折叠动画） -->
              <div class="grid transition-[grid-template-rows] duration-200 ease-out"
                :class="isNarrow || !collapsedGroups[gi] ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'">
                <div class="overflow-hidden">
                  <div class="flex flex-col gap-1">
                    <template v-for="item in group.items" :key="item.id">
                      <!-- 禁用项 -->
                      <BaseTooltip :text="item.label" placement="right" :disabled="!isNarrow">
                        <button v-if="item.disabled" disabled
                          class="flex items-center justify-between rounded-lg px-3 py-3 text-sm cursor-not-allowed text-gray-400 dark:text-[#62666d]"
                          :class="isNarrow ? 'justify-center px-0 w-10 h-10 mx-auto' : ''">
                          <div class="flex items-center gap-3">
                            <i class="fa-solid w-4 shrink-0 text-center text-sm" :class="item.icon"></i>
                            <span v-if="!isNarrow">{{ item.label }}</span>
                          </div>
                          <span v-if="!isNarrow"
                            class="text-[10px] font-medium px-2 py-0.5 rounded-md bg-gray-100 text-gray-500 dark:bg-white/[0.04] dark:text-[#62666d]">敬请期待</span>
                        </button>
                        <!-- 普通项 -->
                        <button v-else :ref="el => navBtnRefs[item.id] = el"
                          @click="setView(item.id === 'workspace' ? lastWorkspaceView : item.id)"
                          class="group relative z-10 flex items-center gap-3 rounded-lg text-sm font-medium outline-none transition-[width,height,padding,margin] duration-300 ease-[var(--sidebar-transition-timing)]"
                          :class="[
                            item.match(currentView)
                              ? 'brand-gradient-bg text-white shadow-sm border-none transition-none'
                              : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-[#8a8f98] dark:hover:bg-white/[0.04] dark:hover:text-[#d0d6e0] transition-colors duration-150',
                            isNarrow ? 'justify-center w-10 h-10 mx-auto' : 'w-full px-3 py-2'
                          ]">
                          <i class="fa-solid w-4 shrink-0 text-center text-sm" :class="item.icon"></i>
                          <span v-if="!isNarrow" class="truncate opacity-0 animate-fadeIn">
                            {{ item.label }}
                          </span>
                        </button>
                      </BaseTooltip>
                    </template>
                  </div>
                </div>
              </div>
            </template>
          </nav>
        </div>

        <!-- AI 对话历史列表 -->
        <div class="mt-2 flex min-h-0 flex-1 flex-col transition-all" :class="isNarrow ? 'px-3' : 'px-4'">
          <div class="flex items-center justify-between mt-6 pb-2 transition-all"
            :class="isNarrow ? 'justify-center' : 'px-3'">
            <button v-if="!isNarrow" @click="emit('update:chatCollapsed', !chatCollapsed)"
              class="flex items-center gap-1 text-xs font-medium uppercase tracking-[0.15em] text-gray-400 hover:text-gray-700 dark:text-[#62666d] dark:hover:text-[#8a8f98] transition-colors cursor-pointer">
              <span>对话</span>
              <i class="fa-solid fa-play text-[8px] text-gray-400 dark:text-[#62666d] transition-transform duration-200"
                :class="chatCollapsed ? '' : 'rotate-90'"></i>
            </button>
            <button v-if="!isNarrow" @click="createChat"
              class="text-gray-500 hover:text-gray-700 dark:text-[#8a8f98] dark:hover:text-[#d0d6e0] transition-colors"
              title="新对话">
              <i class="fa-solid fa-plus text-[10px]"></i>
            </button>
          </div>
          <!-- 折叠动画 -->
          <div class="grid min-h-0 flex-1 transition-[grid-template-rows] duration-200 ease-out"
            :class="isNarrow || !chatCollapsed ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'">
            <div class="flex min-h-0 flex-col overflow-hidden">
              <div :ref="(el) => $emit('update:chatListRef', el)"
                class="relative h-full overflow-y-auto pb-2 custom-scrollbar"
                @click="emit('update:chatMenuOpenId', null)">

                <div v-if="aiChatSessions.length === 0 && !isNarrow"
                  class="px-3 py-4 text-center text-xs text-gray-400 dark:text-[#62666d]">
                  暂无对话
                </div>
                <div v-for="s in aiChatSessions" :key="s.id" :ref="el => chatBtnRefs[s.id] = el"
                  class="group relative mb-px flex cursor-pointer items-center rounded-lg text-sm font-medium outline-none transition-[width,height,padding,margin] duration-300"
                  :class="[
                    chatMenuOpenId === s.id ? 'z-20' : 'z-10',
                    activeAiChatId === s.id && currentView === 'ai-chat'
                      ? 'brand-gradient-bg text-white shadow-sm border-none transition-none'
                      : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-[#8a8f98] dark:hover:bg-white/[0.04] dark:hover:text-[#d0d6e0] transition-colors duration-150',
                    isNarrow ? 'justify-center w-10 h-10 mx-auto' : 'w-full px-3 py-2 gap-3'
                  ]" @click="renamingChatId !== s.id && selectChat(s)">
                  <BaseTooltip :text="s.title" placement="right" :disabled="!isNarrow">
                    <i class="fa-solid fa-message w-4 shrink-0 text-center text-sm transition-colors"></i>
                  </BaseTooltip>

                  <template v-if="!isNarrow">
                    <!-- 重命名输入框 -->
                    <input v-if="renamingChatId === s.id" :value="renameText"
                      @input="emit('update:renameText', $event.target.value)" data-rename-input @click.stop
                      @keydown.enter="emit('confirm-rename-chat', s)"
                      @keydown.escape="$emit('update:renamingChatId', null)" @blur="emit('confirm-rename-chat', s)"
                      class="flex-1 min-w-0 bg-transparent text-xs outline-none border-b border-gray-300 py-0.5 text-gray-900 dark:border-white/[0.12] dark:text-[#f7f8f8]" />
                    <span v-else class="relative z-10 flex-1 truncate">{{ s.title }}</span>

                    <!-- 三个点按钮 -->
                    <button @click.stop="emit('toggle-chat-menu', s.id)"
                      class="shrink-0 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-gray-700 dark:text-[#62666d] dark:hover:text-[#d0d6e0] transition-all ">
                      <i class="fa-solid fa-ellipsis text-[10px]"></i>
                    </button>

                    <!-- Dropdown 菜单 -->
                    <Transition enter-active-class="transition duration-100 ease-out"
                      enter-from-class="opacity-0 scale-95" enter-to-class="opacity-100 scale-100"
                      leave-active-class="transition duration-75 ease-in" leave-from-class="opacity-100 scale-100"
                      leave-to-class="opacity-0 scale-95">
                      <div v-if="chatMenuOpenId === s.id"
                        class="absolute right-2 top-full mt-1 z-50 w-32 rounded-md brand-btn overflow-hidden"
                        @click.stop>
                        <button @click="emit('start-rename-chat', s)"
                          class="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-50 hover:text-gray-900 dark:text-[#d0d6e0] dark:hover:bg-white/[0.05] transition-colors">
                          <i class="fa-solid fa-pen text-[10px] w-3 text-center text-gray-400 dark:text-[#62666d]"></i>
                          重命名
                        </button>
                        <button @click="emit('update:chatMenuOpenId', null); emit('delete-ai-chat', s.id)"
                          class="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-rose-500 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-500/10 transition-colors">
                          <i class="fa-solid fa-trash text-[10px] w-4 text-center"></i> 删除
                        </button>
                      </div>
                    </Transition>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部用户区 -->
      <div class="relative p-2" :class="isNarrow ? 'p-1' : ''">
        <BaseDropdown :modelValue="userMenuOpen" @update:modelValue="(val) => emit('update:userMenuOpen', val)"
          :position="isNarrow ? 'right' : 'top'" :align="isNarrow ? 'end' : 'center'"
          :width="isNarrow ? 'w-48' : 'w-full'" :offset="isNarrow ? 'ml-4' : 'mb-1'"
          panelClass="rounded-md brand-btn dark:bg-[#1b1b1d] backdrop-blur-md"
          :wrapperClass="isNarrow ? 'inline-block' : 'block w-full'">
          <!-- 背景噪点 -->
          <template #background>
            <div class="ws-bg-noise hidden dark:block"></div>
          </template>

          <template #trigger="{ toggle }">
            <!-- 用户信息 -->
            <button @click.stop="toggle"
              class="flex w-full items-center gap-2 px-2 py-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-white/[0.04] transition-all"
              :class="isNarrow ? 'justify-center px-0 w-10 h-10 mx-auto' : ''">
              <div
                class="h-8 w-8 shrink-0 rounded-xl relative overflow-hidden flex items-center justify-center text-white text-sm font-medium"
                style="background: linear-gradient(to bottom, rgba(129,115,223,0.9), rgba(99,87,199,0.9)); box-shadow: inset 0 1px 0 0 rgba(255,255,255,0.12);">
                <img v-if="currentUser?.avatar_url" :src="currentUser.avatar_url" alt="用户头像"
                  class="h-full w-full object-cover" />
                <template v-else>
                  <span class="absolute inset-0 pointer-events-none"
                    style="background-image: linear-gradient(to right, rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.06) 1px, transparent 1px); background-size: 8px 8px; mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%); -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);"></span>
                  <span class="relative z-10">{{ userInitial }}</span>
                </template>
              </div>
              <div v-if="!isNarrow" class="flex-1 min-w-0 text-left">
                <p class="text-sm text-gray-900 dark:text-[#f7f8f8] truncate leading-tight transition-colors">{{
                  userDisplayName }}
                </p>
                <p v-if="userQuotaSummary"
                  class="mt-0.5 text-xs text-[#5e6ad2] dark:text-[#7170ff] truncate leading-tight transition-colors">
                  {{
                    userQuotaSummary }}</p>
                <p v-else class="text-xs text-gray-500 dark:text-[#62666d] truncate leading-tight transition-colors">@{{
                  currentUser?.username || 'guest' }}</p>
              </div>
              <i v-if="!isNarrow"
                class="fa-solid fa-chevron-up text-[10px] text-gray-400 dark:text-[#62666d] transition-colors"></i>
            </button>
          </template>

          <!-- Dropdown 菜单内容 -->
          <template #default="{ close }">
            <button @click="openSettings('profile'); close()"
              class="flex w-full items-center gap-2.5 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900 dark:text-[#d0d6e0] dark:hover:bg-white/[0.05] transition-colors">
              <i class="fa-solid fa-gear w-4 text-center text-xs text-gray-400 dark:text-[#62666d]"></i>
              系统设置
            </button>
            <button @click="(e) => { close(); emit('toggle-theme', e.currentTarget) }"
              class="flex w-full items-center gap-2.5 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900 dark:text-[#d0d6e0] dark:hover:bg-white/[0.05] transition-colors">
              <i class="fa-solid w-4 text-center text-xs text-gray-400 dark:text-[#62666d]"
                :class="isDark ? 'fa-sun' : 'fa-moon'"></i>
              {{ isDark ? '浅色模式' : '深色模式' }}
            </button>
            <div class="border-t border-gray-200 dark:border-white/[0.05]"></div>
            <button @click="emit('logout'); close()"
              class="flex w-full items-center gap-3 px-4 py-3 text-sm font-bold text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-500/10 transition-colors">
              <i class="fas fa-right-from-bracket w-4 text-center text-xs"></i>
              退出登录
            </button>
          </template>
        </BaseDropdown>
      </div>
    </template>
  </aside>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 10px;
}

.dark .custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.05);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
