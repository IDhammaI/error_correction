<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'

const router = useRouter()
const { currentUser } = useAuth()

const loading = ref(false)
const showPwd = ref(false)
const error = ref('')
const form = reactive({ email: '', password: '' })

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
  <form @submit.prevent="handleLogin" class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">邮箱或用户名</label>
      <input
        v-model="form.email"
        type="text"
        required
        autocomplete="username"
        placeholder="邮箱 或 用户名"
        class="w-full h-10 px-4 rounded-xl border border-slate-200/60 dark:border-white/10 bg-white/80 dark:bg-white/5 text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 dark:focus:border-blue-500 transition-all text-sm"
      />
    </div>

    <div>
      <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">密码</label>
      <div class="relative">
        <input
          v-model="form.password"
          :type="showPwd ? 'text' : 'password'"
          required
          autocomplete="current-password"
          placeholder="请输入密码"
          class="w-full h-10 px-4 pr-11 rounded-xl border border-slate-200/60 dark:border-white/10 bg-white/80 dark:bg-white/5 text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 dark:focus:border-blue-500 transition-all text-sm"
        />
        <button
          type="button"
          @click="showPwd = !showPwd"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
        >
          <i :class="showPwd ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
        </button>
      </div>
    </div>

    <p v-if="error" class="text-sm text-rose-500 dark:text-rose-400 flex items-center gap-2">
      <i class="fas fa-circle-exclamation"></i>{{ error }}
    </p>

    <button
      type="submit"
      :disabled="loading"
      class="w-full h-12 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-all shadow-md shadow-blue-500/30 hover:shadow-blue-500/50 flex items-center justify-center gap-2 text-sm"
    >
      <i v-if="loading" class="fas fa-spinner fa-spin"></i>
      <span>{{ loading ? '登录中...' : '登录' }}</span>
    </button>
  </form>
</template>
