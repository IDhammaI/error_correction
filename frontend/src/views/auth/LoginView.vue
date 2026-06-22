<script setup>
/**
 * LoginView.vue
 * 登录表单页面，负责提交账号密码、写入登录用户并进入工作台。
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseInput from '@/components/base/BaseInput.vue'
import ForgotPasswordModal from '@/components/features/auth/ForgotPasswordModal.vue'

const router = useRouter()
const { setCurrentUser } = useAuth()

const loading = ref(false)
const error = ref('')
const form = reactive({ email: '', password: '' })
const fpOpen = ref(false)

/**
 * 提交登录表单，成功后同步全局用户状态并跳转到 /app。
 */
async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: form.email, password: form.password }),
    })
    const data = await res.json()
    if (!res.ok) {
      error.value = data.error || '登录失败'
    } else {
      setCurrentUser(data.user)
      router.push('/app')
    }
  } catch {
    error.value = '网络错误，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
  <form @submit.prevent="handleLogin" class="space-y-4">
    <BaseInput
      v-model="form.email"
      label="账号"
      required
      autocomplete="username"
      placeholder="请输入邮箱或用户名"
    />

    <BaseInput
      v-model="form.password"
      type="password"
      label="密码"
      required
      autocomplete="current-password"
      placeholder="请输入密码"
    />

    <div class="flex justify-end">
      <BaseButton
        variant="ghost"
        size="sm"
        type="button"
        class="!h-auto !rounded-none !border-0 !bg-transparent !px-0 !py-0 text-xs text-gray-500 dark:text-white/40 hover:!text-[rgb(var(--accent-rgb))]"
        @click="fpOpen = true"
      >
        忘记密码？
      </BaseButton>
    </div>
    <p v-if="error" class="text-sm text-rose-500 dark:text-rose-400 flex items-center gap-2 transition-colors">
      <i class="fas fa-circle-exclamation text-xs"></i>{{ error }}
    </p>


    <BaseButton variant="cta" type="submit" class="w-full" :disabled="loading">
      <i v-if="loading" class="fas fa-spinner fa-spin text-xs"></i>
      <span>{{ loading ? '登录中...' : '登录' }}</span>
    </BaseButton>
  </form>

  <ForgotPasswordModal :open="fpOpen" @close="fpOpen = false" />
  </div>
</template>
