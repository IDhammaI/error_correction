<script setup>
import { ref, reactive, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import LandingButton from './landing/LandingButton.vue'

const router = useRouter()
const { currentUser } = useAuth()

const loading = ref(false)
const showPwd = ref(false)
const error = ref('')
const success = ref('')
const form = reactive({ username: '', email: '', password: '', confirm: '', code: '' })

const sendingCode = ref(false)
const countdown = ref(0)
let countdownTimer = null
let sendDebounceTimer = null

const passwordMismatch = () => form.confirm && form.password !== form.confirm

function clearCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

function startCountdown(seconds = 60) {
  clearCountdown()
  countdown.value = seconds
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      clearCountdown()
      countdown.value = 0
    }
  }, 1000)
}

async function handleSendCode() {
  error.value = ''
  if (sendingCode.value || countdown.value > 0) return
  const email = (form.email || '').trim()
  if (!email || !email.includes('@')) {
    error.value = '请先填写有效邮箱'
    return
  }
  if (sendDebounceTimer) clearTimeout(sendDebounceTimer)
  sendDebounceTimer = setTimeout(async () => {
    sendDebounceTimer = null
    sendingCode.value = true
    try {
      const res = await fetch('/api/auth/send-registration-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        error.value = data.error || '发送失败'
        return
      }
      success.value = '验证码已发送到邮箱，请查收'
      startCountdown(60)
    } catch {
      error.value = '网络错误，请重试'
    } finally {
      sendingCode.value = false
    }
  }, 280)
}

async function handleRegister() {
  error.value = ''
  success.value = ''
  if (passwordMismatch()) {
    error.value = '两次密码不一致'
    return
  }
  loading.value = true
  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        username: form.username,
        email: form.email,
        password: form.password,
        code: form.code,
      }),
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

onBeforeUnmount(() => {
  clearCountdown()
  if (sendDebounceTimer) clearTimeout(sendDebounceTimer)
})
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
      <label class="block text-sm font-medium text-white/60 mb-2">邮箱验证码</label>
      <div class="flex gap-2">
        <input
          v-model="form.code"
          type="text"
          inputmode="numeric"
          maxlength="6"
          pattern="[0-9]*"
          required
          autocomplete="one-time-code"
          placeholder="6 位数字"
          class="min-w-0 flex-1 h-10 px-4 rounded-xl border border-white/[0.08] bg-white/[0.03] text-white placeholder-white/25 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm"
        />
        <button
          type="button"
          class="shrink-0 h-10 px-3 rounded-xl border border-white/[0.12] bg-white/[0.06] text-sm text-white/90 hover:bg-white/[0.1] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          :disabled="sendingCode || countdown > 0"
          @click="handleSendCode"
        >
          <span v-if="countdown > 0">{{ countdown }}s</span>
          <span v-else-if="sendingCode">发送中…</span>
          <span v-else>获取验证码</span>
        </button>
      </div>
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

    <LandingButton variant="cta" type="submit" class="w-full" :disabled="loading || passwordMismatch()">
      <i v-if="loading" class="fas fa-spinner fa-spin text-xs"></i>
      <span>{{ loading ? '注册中...' : '创建账户' }}</span>
    </LandingButton>
  </form>
</template>
