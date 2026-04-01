<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'

const router = useRouter()
const { currentUser } = useAuth()

const loading = ref(false)
const showPwd = ref(false)
const error = ref('')
const success = ref('')
const form = reactive({ username: '', email: '', password: '', confirm: '' })

const passwordMismatch = () => form.confirm && form.password !== form.confirm

async function handleRegister() {
  error.value = ''
  success.value = ''
  if (passwordMismatch()) { error.value = '两次密码不一致'; return }
  loading.value = true
  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: form.username, email: form.email, password: form.password }),
    })
    const data = await res.json()
    if (!res.ok) {
      error.value = data.error || '注册失败'
    } else {
      success.value = '注册成功！正在登录...'
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
  <form @submit.prevent="handleRegister" class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-white/60 mb-2">用户名</label>
      <input
        v-model="form.username"
        type="text"
        required
        autocomplete="username"
        placeholder="您的昵称"
        maxlength="50"
        class="w-full h-10 px-4 rounded-xl border border-white/[0.08] bg-white/[0.03] text-white placeholder-white/25 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm"
      />
    </div>

    <div>
      <label class="block text-sm font-medium text-white/60 mb-2">邮箱</label>
      <input
        v-model="form.email"
        type="email"
        required
        autocomplete="email"
        placeholder="your@email.com"
        class="w-full h-10 px-4 rounded-xl border border-white/[0.08] bg-white/[0.03] text-white placeholder-white/25 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm"
      />
    </div>

    <div>
      <label class="block text-sm font-medium text-white/60 mb-2">密码</label>
      <div class="relative">
        <input
          v-model="form.password"
          :type="showPwd ? 'text' : 'password'"
          required
          autocomplete="new-password"
          placeholder="至少 6 位"
          minlength="6"
          class="w-full h-10 px-4 pr-11 rounded-xl border border-white/[0.08] bg-white/[0.03] text-white placeholder-white/25 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm"
        />
        <button
          type="button"
          @click="showPwd = !showPwd"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-white/25 hover:text-white/50 transition-colors"
        >
          <i :class="showPwd ? 'fas fa-eye-slash' : 'fas fa-eye'" class="text-xs"></i>
        </button>
      </div>
    </div>

    <div>
      <label class="block text-sm font-medium text-white/60 mb-2">确认密码</label>
      <input
        v-model="form.confirm"
        type="password"
        required
        autocomplete="new-password"
        placeholder="再次输入密码"
        class="w-full h-10 px-4 rounded-xl border bg-white/[0.03] text-white placeholder-white/25 focus:outline-none focus:ring-1 transition-all text-sm"
        :class="passwordMismatch()
          ? 'border-rose-500/50 focus:border-rose-500/50 focus:ring-rose-500/30'
          : 'border-white/[0.08] focus:border-indigo-500/50 focus:ring-indigo-500/30'"
      />
      <p v-if="passwordMismatch()" class="text-xs text-rose-400 mt-1">两次密码不一致</p>
    </div>

    <p v-if="error" class="text-sm text-rose-400 flex items-center gap-2">
      <i class="fas fa-circle-exclamation text-xs"></i>{{ error }}
    </p>
    <p v-if="success" class="text-sm text-emerald-400 flex items-center gap-2">
      <i class="fas fa-circle-check text-xs"></i>{{ success }}
    </p>

    <button
      type="submit"
      :disabled="loading || passwordMismatch()"
      class="auth-submit-btn w-full h-10 text-sm font-medium text-white rounded-xl transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <i v-if="loading" class="fas fa-spinner fa-spin text-xs"></i>
      <span>{{ loading ? '注册中...' : '创建账户' }}</span>
    </button>
  </form>
</template>

<style scoped>
.auth-submit-btn {
  background: linear-gradient(to bottom, rgba(129, 115, 223, 0.9), rgba(99, 87, 199, 0.9));
  border: none;
  box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.12);
}
.auth-submit-btn:hover:not(:disabled) {
  background: linear-gradient(to bottom, rgba(145, 132, 235, 0.95), rgba(113, 100, 212, 0.95));
  box-shadow:
    inset 0 1px 0 0 rgba(255, 255, 255, 0.15),
    0 0 20px 0 rgba(129, 115, 223, 0.25);
}
</style>
