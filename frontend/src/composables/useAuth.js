import { ref } from 'vue'

// 模块单例，跨组件共享登录状态
const currentUser = ref(null)
const authChecked = ref(false)

export function useAuth() {
  return { currentUser, authChecked }
}
