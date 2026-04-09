import { nextTick } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import { usePageTransition } from '@/composables/usePageTransition.js'

const routes = [
  {
    path: '/',
    component: () => import('@/views/LandingView.vue'),
    meta: { layout: 'landing' },
  },
  {
    path: '/auth',
    component: () => import('@/views/auth/AuthLayout.vue'),
    redirect: '/auth/login',
    meta: { layout: 'auth' },
    children: [
      { path: 'login',    component: () => import('@/views/auth/LoginView.vue'),    meta: { order: 0, layout: 'auth' } },
      { path: 'register', component: () => import('@/views/auth/RegisterView.vue'), meta: { order: 1, layout: 'auth' } },
    ],
  },
  {
    path: '/app/:view?/:subview?',
    component: () => import('@/views/WorkspaceView.vue'),
    meta: { requiresAuth: true, layout: 'app' },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/app/workspace',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from) => {
  const { currentUser, authChecked } = useAuth()

  // 首次导航时请求登录态
  if (!authChecked.value) {
    try {
      const res = await fetch('/api/auth/me')
      if (res.ok) {
        const data = await res.json()
        currentUser.value = data.user
      }
    } catch (_) {}
    authChecked.value = true
  }

  if (to.meta.requiresAuth && !currentUser.value) {
    return '/auth/login'
  }

  if (to.path.startsWith('/auth') && currentUser.value) {
    return '/app/workspace'
  }

  // 跨布局跳转：先让 loading 完全进场，再放行路由
  const fromLayout = from.meta.layout || ''
  const toLayout = to.meta.layout || ''
  if (fromLayout && toLayout && fromLayout !== toLayout) {
    const { show } = usePageTransition()
    await show() // 等淡入动画结束
  }
})

router.afterEach(async (to, from) => {
  const fromLayout = from.meta.layout || ''
  const toLayout = to.meta.layout || ''
  if (fromLayout && toLayout && fromLayout !== toLayout) {
    const { hide } = usePageTransition()
    // 等待 DOM 更新，确保新页面组件已挂载
    await nextTick()
    // 新页面渲染完成后再淡出，给一点缓冲时间
    hide(500)
  }
})

export default router
