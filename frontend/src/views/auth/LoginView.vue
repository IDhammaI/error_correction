<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import LandingButton from '@/components/landing/LandingButton.vue'
import ForgotPasswordModal from '@/components/auth/ForgotPasswordModal.vue'

const router = useRouter()
const { currentUser } = useAuth()

const loading = ref(false)
const showPwd = ref(false)
const error = ref('')
const form = reactive({ email: '', password: '' })
const fpOpen = ref(false)

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
      currentUser.value = data.user
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
    <div>
      <label class="block text-sm font-medium text-white/60 mb-2">邮箱或用户名</label>
      <input v-model="form.email" type="text" required autocomplete="username" placeholder="邮箱 或 用户名"
        class="w-full h-10 px-4 rounded-xl border border-white/[0.08] bg-white/[0.03] text-white placeholder-white/25 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm" />
    </div>

    <div>
      <label class="block text-sm font-medium text-white/60 mb-2">密码</label>
      <div class="relative">
        <input v-model="form.password" :type="showPwd ? 'text' : 'password'" required autocomplete="current-password"
          placeholder="请输入密码"
          class="w-full h-10 px-4 pr-11 rounded-xl border border-white/[0.08] bg-white/[0.03] text-white placeholder-white/25 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm" />
        <button type="button" @click="showPwd = !showPwd"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-white/25 hover:text-white/50 transition-colors">
          <i :class="showPwd ? 'fas fa-eye-slash' : 'fas fa-eye'" class="text-xs"></i>
        </button>
      </div>
    </div>
    <div class="flex justify-end">
      <button type="button" @click="fpOpen = true"
        class="text-xs text-white/40 hover:text-indigo-400 transition-colors">
        忘记密码？
      </button>
    </div>
    <p v-if="error" class="text-sm text-rose-400 flex items-center gap-2">
      <i class="fas fa-circle-exclamation text-xs"></i>{{ error }}
    </p>


    <LandingButton variant="cta" type="submit" class="w-full" :disabled="loading">
      <i v-if="loading" class="fas fa-spinner fa-spin text-xs"></i>
      <span>{{ loading ? '登录中...' : '登录' }}</span>
    </LandingButton>
  </form>

  <ForgotPasswordModal :open="fpOpen" @close="fpOpen = false" />
  </div>
</template>
