import { computed, ref } from 'vue'

/**
 * useAuth.js
 * 登录用户与额度快照的全局单例状态。
 *
 * 认证信息需要被路由守卫、导航栏、设置页等多个位置读取，
 * 因此这里使用模块级 ref 保持同一份登录状态。
 */
const currentUser = ref(null)
const authChecked = ref(false)

const quota = computed(() => currentUser.value?.quota || null)
const remainingQuota = computed(() => quota.value?.remaining ?? null)

/**
 * 写入当前登录用户，并标记“认证检查已完成”。
 */
function setCurrentUser(user) {
  currentUser.value = user || null
  authChecked.value = true
  return currentUser.value
}

/**
 * 清空登录用户，通常用于接口返回未登录或主动退出后。
 */
function clearCurrentUser() {
  currentUser.value = null
  authChecked.value = true
}

/**
 * 只更新用户对象里的额度快照，避免重新请求完整用户信息。
 */
function setQuotaSnapshot(snapshot) {
  if (!snapshot || !currentUser.value) return currentUser.value
  currentUser.value = {
    ...currentUser.value,
    quota: snapshot,
  }
  authChecked.value = true
  return currentUser.value
}

/**
 * 向后端确认当前登录态，并同步最新用户信息。
 */
async function refreshCurrentUser() {
  try {
    const res = await fetch('/api/auth/me', { credentials: 'include' })
    if (!res.ok) {
      clearCurrentUser()
      return null
    }
    const data = await res.json().catch(() => null)
    if (data?.user) {
      return setCurrentUser(data.user)
    }
  } catch (_) {
    clearCurrentUser()
    return null
  }
  clearCurrentUser()
  return null
}

/**
 * 暴露认证相关的响应式状态和写入方法。
 */
export function useAuth() {
  return {
    currentUser,
    authChecked,
    quota,
    remainingQuota,
    setCurrentUser,
    clearCurrentUser,
    setQuotaSnapshot,
    refreshCurrentUser,
  }
}
