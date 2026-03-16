import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'

const routes = [
  {
    path: '/auth',
    component: () => import('../components/AuthView.vue'),
  },
  {
    path: '/app/:view?/:subview?',
    component: () => import('../views/WorkspaceView.vue'),
    meta: { requiresAuth: true },
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

router.beforeEach(async (to) => {
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
    return '/auth'
  }

  if (to.path === '/auth' && currentUser.value) {
    return '/app/workspace'
  }
})

export default router
