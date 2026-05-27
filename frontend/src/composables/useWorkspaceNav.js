/**
 * useWorkspaceNav.js
 * 工作台视图路由 + 侧边栏导航配置 — 单例 composable
 */
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const DEFAULT_SETTINGS_SUBVIEW = 'profile'

export const SIDEBAR_WIDTH = Object.freeze({
  collapsed: 64,
  expanded: 256,
})

const VIEW_TO_PATH = {
  workspace: '/app/workspace',
  workspace_review: '/app/workspace/review',
  'search-chat': '/app/search-chat',
  library: '/app/library',
  dashboard: '/app/dashboard',
  review: '/app/review',
  'error-bank': '/app/error-bank',
  notes: '/app/notes',
  'ai-chat': '/app/ai-chat',
  settings: `/app/settings/${DEFAULT_SETTINGS_SUBVIEW}`,
  'split-history': '/app/split-history',
  chat: '/app/chat',
}

const WORKSPACE_VIEWS = new Set(['workspace', 'workspace_review', 'split-history'])

const SETTINGS_NAV_ITEMS = [
  { id: 'quota', label: '免费额度', icon: 'fa-gauge-high' },
  { id: 'system-providers', label: '平台托管', icon: 'fa-server', adminOnly: true },
  { id: 'appearance', label: '外观设置', icon: 'fa-palette' },
  { id: 'profile', label: '用户资料设置', icon: 'fa-user-gear' },
  { id: 'api', label: 'API 设置', icon: 'fa-plug-circle-bolt' },
]

const NAV_GROUPS = [
  {
    label: null,
    items: [
      { id: 'workspace', label: '录入工作台', icon: 'fa-wand-magic-sparkles', match: (v) => WORKSPACE_VIEWS.has(v) },
      { id: 'search-chat', label: '搜索聊天', icon: 'fa-magnifying-glass', match: (v) => v === 'search-chat' },
      { id: 'library', label: '库', icon: 'fa-box-archive', match: (v) => v === 'library' },
    ],
  },
]

// 模块级单例状态：侧边栏展开状态和上次工作台视图需要跨组件共享。
let initialized = false
const collapsedGroups = ref({})
const chatCollapsed = ref(false)
const lastWorkspaceView = ref('workspace')

// 响应式状态：区分移动端抽屉和桌面端折叠侧边栏。
const isMobile = ref(false)
const canHover = ref(true)
const sidebarMode = ref('expanded') // 'expanded' | 'collapsed-icon' (仅大屏)
const mobileDrawerOpen = ref(false) // (仅小屏)

/**
 * 根据窗口宽度和 hover 能力更新导航形态。
 */
const checkMobile = () => {
  if (typeof window !== 'undefined') {
    const mobile = window.innerWidth < 1024
    if (mobile !== isMobile.value) {
      isMobile.value = mobile
      // 从大屏切换到小屏时，强制关闭抽屉
      if (mobile) {
        mobileDrawerOpen.value = false
      }
    }
    canHover.value = window.matchMedia('(hover: hover)').matches
  }
}

/**
 * 移动端切换抽屉，桌面端切换侧边栏展开/图标模式。
 */
const toggleSidebar = () => {
  if (isMobile.value) {
    mobileDrawerOpen.value = !mobileDrawerOpen.value
  } else {
    sidebarMode.value = sidebarMode.value === 'expanded' ? 'collapsed-icon' : 'expanded'
    if (typeof window !== 'undefined') {
      localStorage.setItem('sidebar-mode', sidebarMode.value)
    }
  }
}

/**
 * 仅在移动端关闭抽屉，桌面端调用不会改变侧边栏状态。
 */
const closeDrawer = () => {
  if (isMobile.value) {
    mobileDrawerOpen.value = false
  }
}

/**
 * 工作台导航状态和路由路径之间的适配层。
 */
export function useWorkspaceNav() {
  const router = useRouter()
  const route = useRoute()

  const currentView = computed({
    // 从 /app/:view?/:subview? 还原内部视图名。
    get() {
      const view = route.params.view || 'workspace'
      const subview = route.params.subview
      if (view === 'workspace' && subview === 'review') return 'workspace_review'
      return view
    },
    // 写入内部视图名时，统一映射为真实路由地址。
    set(view) {
      const path = VIEW_TO_PATH[view]
      if (path && route.path !== path) router.push(path)
    },
  })

  /**
   * 当前设置页子视图，不合法时回退到默认 profile。
   */
  const currentSettingsSubView = computed(() => {
    if (currentView.value !== 'settings') return DEFAULT_SETTINGS_SUBVIEW
    const subview = String(route.params.subview || '').trim()
    return SETTINGS_NAV_ITEMS.some(item => item.id === subview)
      ? subview
      : DEFAULT_SETTINGS_SUBVIEW
  })

  /**
   * 切换设置页子视图，支持 replace 避免补全默认路由时污染历史记录。
   */
  const setSettingsSubView = (subview, { replace = false } = {}) => {
    const target = SETTINGS_NAV_ITEMS.some(item => item.id === subview)
      ? subview
      : DEFAULT_SETTINGS_SUBVIEW
    const path = `/app/settings/${target}`
    if (route.path === path) return
    return replace ? router.replace(path) : router.push(path)
  }

  if (!initialized) {
    initialized = true

    if (typeof window !== 'undefined') {
      checkMobile()
      window.addEventListener('resize', checkMobile)

      const savedMode = localStorage.getItem('sidebar-mode')
      if (savedMode === 'expanded' || savedMode === 'collapsed-icon') {
        sidebarMode.value = savedMode
      }
    }

    watch(currentView, (v) => {
      if (WORKSPACE_VIEWS.has(v)) lastWorkspaceView.value = v
    }, { immediate: true })
  }

  watch(
    () => [route.params.view, route.params.subview],
    ([view, subview]) => {
      if (view === 'settings' && !subview) {
        setSettingsSubView(DEFAULT_SETTINGS_SUBVIEW, { replace: true })
      }
    },
    { immediate: true },
  )

  /**
   * 回到首页前做一个轻量淡出动画。
   */
  const navigateToHome = () => {
    document.body.style.transition = 'opacity 0.25s ease, transform 0.25s ease'
    document.body.style.opacity = '0'
    document.body.style.transform = 'translateY(-6px)'
    setTimeout(() => { window.location.href = '/' }, 260)
  }

  // 只有工作台布局才有侧边栏偏移，认证页和首页不应该让出宽度。
  const isInAppLayout = computed(() => route.meta.layout === 'app')

  /**
   * 给 Toast、Modal 等全局浮层使用的侧边栏偏移量。
   */
  const sidebarOffset = computed(() => {
    if (!isInAppLayout.value || isMobile.value) return 0
    return sidebarMode.value === 'collapsed-icon'
      ? SIDEBAR_WIDTH.collapsed
      : SIDEBAR_WIDTH.expanded
  })

  return {
    currentView, currentSettingsSubView, setSettingsSubView,
    lastWorkspaceView, collapsedGroups, chatCollapsed,
    sidebarMode, isMobile, canHover, mobileDrawerOpen, toggleSidebar, closeDrawer, sidebarOffset,
    NAV_GROUPS, WORKSPACE_VIEWS, SETTINGS_NAV_ITEMS, navigateToHome,
  }
}
