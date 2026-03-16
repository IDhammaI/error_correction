<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-[#0A0A0F] dark:to-slate-900 px-4">
    <div class="w-full max-w-md">
      <!-- Logo / Title -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-600 text-white text-2xl mb-4 shadow-lg shadow-blue-500/30">
          <i class="fas fa-book-open"></i>
        </div>
        <h1 class="text-2xl font-bold text-slate-800 dark:text-white">错题本</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">智能错题管理系统</p>
      </div>

      <!-- Card -->
      <div class="bg-white/70 dark:bg-white/5 backdrop-blur-xl rounded-3xl border border-slate-200/60 dark:border-white/10 shadow-xl p-8">
        <!-- Tabs -->
        <div class="flex rounded-xl bg-slate-100/80 dark:bg-white/5 p-1 mb-6">
          <button
            @click="activeTab = 'login'"
            :class="[
              'flex-1 py-2 text-sm font-bold rounded-lg transition-all',
              activeTab === 'login'
                ? 'bg-white dark:bg-white/10 text-blue-600 dark:text-blue-400 shadow-sm'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
            ]"
          >
            登录
          </button>
          <button
            @click="activeTab = 'register'"
            :class="[
              'flex-1 py-2 text-sm font-bold rounded-lg transition-all',
              activeTab === 'register'
                ? 'bg-white dark:bg-white/10 text-blue-600 dark:text-blue-400 shadow-sm'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
            ]"
          >
            注册
          </button>
        </div>

        <!-- Login Form -->
        <form v-if="activeTab === 'login'" @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">邮箱或用户名</label>
            <input
              v-model="loginForm.email"
              type="text"
              required
              autocomplete="username"
              placeholder="邮箱 或 用户名"
              class="w-full h-11 px-4 rounded-xl border border-slate-200/80 dark:border-white/10 bg-white/80 dark:bg-white/5 text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 dark:focus:border-blue-500 transition-all text-sm"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">密码</label>
            <div class="relative">
              <input
                v-model="loginForm.password"
                :type="showLoginPwd ? 'text' : 'password'"
                required
                autocomplete="current-password"
                placeholder="请输入密码"
                class="w-full h-11 px-4 pr-11 rounded-xl border border-slate-200/80 dark:border-white/10 bg-white/80 dark:bg-white/5 text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 dark:focus:border-blue-500 transition-all text-sm"
              />
              <button
                type="button"
                @click="showLoginPwd = !showLoginPwd"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
              >
                <i :class="showLoginPwd ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
              </button>
            </div>
          </div>

          <p v-if="loginError" class="text-sm text-rose-500 dark:text-rose-400 flex items-center gap-1.5">
            <i class="fas fa-circle-exclamation"></i>{{ loginError }}
          </p>

          <button
            type="submit"
            :disabled="loading"
            class="w-full h-12 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-bold rounded-xl transition-all shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 disabled:cursor-not-allowed disabled:shadow-none flex items-center justify-center gap-2 text-sm"
          >
            <i v-if="loading" class="fas fa-spinner fa-spin"></i>
            <span>{{ loading ? '登录中...' : '登录' }}</span>
          </button>
        </form>

        <!-- Register Form -->
        <form v-if="activeTab === 'register'" @submit.prevent="handleRegister" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">用户名</label>
            <input
              v-model="registerForm.username"
              type="text"
              required
              autocomplete="username"
              placeholder="您的昵称"
              maxlength="50"
              class="w-full h-11 px-4 rounded-xl border border-slate-200/80 dark:border-white/10 bg-white/80 dark:bg-white/5 text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 dark:focus:border-blue-500 transition-all text-sm"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">邮箱</label>
            <input
              v-model="registerForm.email"
              type="email"
              required
              autocomplete="email"
              placeholder="your@email.com"
              class="w-full h-11 px-4 rounded-xl border border-slate-200/80 dark:border-white/10 bg-white/80 dark:bg-white/5 text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 dark:focus:border-blue-500 transition-all text-sm"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">密码</label>
            <div class="relative">
              <input
                v-model="registerForm.password"
                :type="showRegPwd ? 'text' : 'password'"
                required
                autocomplete="new-password"
                placeholder="至少 6 位"
                minlength="6"
                class="w-full h-11 px-4 pr-11 rounded-xl border border-slate-200/80 dark:border-white/10 bg-white/80 dark:bg-white/5 text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 dark:focus:border-blue-500 transition-all text-sm"
              />
              <button
                type="button"
                @click="showRegPwd = !showRegPwd"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
              >
                <i :class="showRegPwd ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
              </button>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">确认密码</label>
            <input
              v-model="registerForm.confirm"
              type="password"
              required
              autocomplete="new-password"
              placeholder="再次输入密码"
              class="w-full h-11 px-4 rounded-xl border border-slate-200/80 dark:border-white/10 bg-white/80 dark:bg-white/5 text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 dark:focus:border-blue-500 transition-all text-sm"
              :class="{ 'border-rose-400 dark:border-rose-500': registerForm.confirm && registerForm.password !== registerForm.confirm }"
            />
            <p v-if="registerForm.confirm && registerForm.password !== registerForm.confirm" class="text-xs text-rose-500 mt-1">
              两次密码不一致
            </p>
          </div>

          <p v-if="registerError" class="text-sm text-rose-500 dark:text-rose-400 flex items-center gap-1.5">
            <i class="fas fa-circle-exclamation"></i>{{ registerError }}
          </p>
          <p v-if="registerSuccess" class="text-sm text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
            <i class="fas fa-circle-check"></i>{{ registerSuccess }}
          </p>

          <button
            type="submit"
            :disabled="loading || (registerForm.confirm && registerForm.password !== registerForm.confirm)"
            class="w-full h-12 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-bold rounded-xl transition-all shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 disabled:cursor-not-allowed disabled:shadow-none flex items-center justify-center gap-2 text-sm"
          >
            <i v-if="loading" class="fas fa-spinner fa-spin"></i>
            <span>{{ loading ? '注册中...' : '创建账户' }}</span>
          </button>
        </form>
      </div>

      <p class="text-center text-xs text-slate-400 dark:text-slate-600 mt-6">
        错题本智能管理系统 &copy; {{ new Date().getFullYear() }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'

const router = useRouter()
const { currentUser } = useAuth()

const activeTab = ref('login')
const loading = ref(false)
const showLoginPwd = ref(false)
const showRegPwd = ref(false)
const loginError = ref('')
const registerError = ref('')
const registerSuccess = ref('')

const loginForm = reactive({ email: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '', confirm: '' })

async function handleLogin() {
  loginError.value = ''
  loading.value = true
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: loginForm.email, password: loginForm.password })
    })
    const data = await res.json()
    if (!res.ok) {
      loginError.value = data.error || '登录失败'
    } else {
      currentUser.value = data.user
      router.push('/app')
    }
  } catch {
    loginError.value = '网络错误，请重试'
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  registerError.value = ''
  registerSuccess.value = ''
  if (registerForm.password !== registerForm.confirm) {
    registerError.value = '两次密码不一致'
    return
  }
  loading.value = true
  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: registerForm.username,
        email: registerForm.email,
        password: registerForm.password
      })
    })
    const data = await res.json()
    if (!res.ok) {
      registerError.value = data.error || '注册失败'
    } else {
      registerSuccess.value = '注册成功！正在登录...'
      currentUser.value = data.user
      router.push('/app')
    }
  } catch {
    registerError.value = '网络错误，请重试'
  } finally {
    loading.value = false
  }
}
</script>
