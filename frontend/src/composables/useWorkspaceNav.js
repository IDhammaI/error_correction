/**
 * useWorkspaceNav.js
 * 工作台视图路由 + 侧边栏导航配置
 */
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const VIEW_TO_PATH = {
  workspace: '/app/workspace',
  workspace_review: '/app/workspace/review',
  dashboard: '/app/dashboard',
  review: '/app/review',
  'error-bank': '/app/error-bank',
  notes: '/app/notes',
  'ai-chat': '/app/ai-chat',
  settings: '/app/settings',
  'split-history': '/app/split-history',
  chat: '/app/chat',
}

const WORKSPACE_VIEWS = new Set(['workspace', 'workspace_review', 'split-history'])

const NAV_GROUPS = [
  {
    label: null,
    items: [
      { id: 'workspace', label: '录入工作台', icon: 'fa-wand-magic-sparkles', match: (v) => WORKSPACE_VIEWS.has(v) },
    ],
  },
  {
    label: '数据',
    collapsible: true,
    items: [
      { id: 'dashboard', label: '数据面板', icon: 'fa-chart-pie', match: (v) => v === 'dashboard' },
      { id: 'error-bank', label: '错题库', icon: 'fa-database', match: (v) => v === 'error-bank' },
      { id: 'notes', label: '笔记库', icon: 'fa-book-open', match: (v) => v === 'notes' },
    ],
  },
  {
    label: '更多',
    collapsible: true,
    items: [
      { id: 'review-disabled', label: '刷题', icon: 'fa-clock-rotate-left', disabled: true },
    ],
  },
]

export function useWorkspaceNav() {
  const router = useRouter()
  const route = useRoute()

  const collapsedGroups = ref({})
  const chatCollapsed = ref(false)
  const lastWorkspaceView = ref('workspace')

  const currentView = computed({
    get() {
      const view = route.params.view || 'workspace'
      const subview = route.params.subview
      if (view === 'workspace' && subview === 'review') return 'workspace_review'
      return view
    },
    set(view) {
      const path = VIEW_TO_PATH[view]
      if (path && route.path !== path) router.push(path)
    },
  })

  watch(currentView, (v) => {
    if (WORKSPACE_VIEWS.has(v)) lastWorkspaceView.value = v
  })

  const navigateToHome = () => {
    document.body.style.transition = 'opacity 0.25s ease, transform 0.25s ease'
    document.body.style.opacity = '0'
    document.body.style.transform = 'translateY(-6px)'
    setTimeout(() => { window.location.href = '/' }, 260)
  }

  return {
    currentView, lastWorkspaceView, collapsedGroups, chatCollapsed,
    NAV_GROUPS, WORKSPACE_VIEWS,
    navigateToHome,
  }
}
