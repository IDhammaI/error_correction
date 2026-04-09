<script setup>
import { ref, reactive, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import LandingButton from '@/components/landing/LandingButton.vue'

const router = useRouter()
const { currentUser } = useAuth()

const loading = ref(false)
const showPwd = ref(false)
const error = ref('')
const success = ref('')
const form = reactive({ username: '', email: '', password: '', confirm: '', code: '' })

const sendingCode = ref(false)
const countdown = ref(0)
const rateLimitCountdown = ref(0)
let countdownTimer = null
let rateLimitTimer = null
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

function clearRateLimitCountdown() {
  if (rateLimitTimer) {
    clearInterval(rateLimitTimer)
    rateLimitTimer = null
  }
}

function startRateLimitCountdown(seconds) {
  clearRateLimitCountdown()
  rateLimitCountdown.value = seconds
  error.value = `发送过于频繁，请 ${seconds} 秒后再试`
  rateLimitTimer = setInterval(() => {
    rateLimitCountdown.value -= 1
    if (rateLimitCountdown.value <= 0) {
      clearRateLimitCountdown()
      rateLimitCountdown.value = 0
      error.value = ''
    } else {
      error.value = `发送过于频繁，请 ${rateLimitCountdown.value} 秒后再试`
    }
  }, 1000)
}

async function handleSendCode() {
  error.value = ''
  clearRateLimitCountdown()
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
      const res = await fetch('/api/auth/send-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, type: 'register' }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        // 429 频率限制：解析剩余秒数，启动错误提示倒计时
        if (res.status === 429) {
          const match = (data.error || '').match(/(\d+)\s*秒/)
          const wait = match ? parseInt(match[1], 10) : 30
          startRateLimitCountdown(wait)
        } else {
          error.value = data.error || '发送失败'
        }
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
  if (passwordMismatch()) { error.value = '两次密码不一致'; return }
  if (!form.code.trim()) { error.value = '请输入验证码'; return }
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
        code: form.code.trim(),
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
  clearRateLimitCountdown()
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
        class="w-full h-10 px-4 rounded-lg border border-white/[0.08] bg-white/[0.05] text-white placeholder-white/25 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm"
      />
    </div>

    <div>
      <label class="block text-sm font-medium text-white/60 mb-2">邮箱</label>
      <div class="flex gap-2">
        <input
          v-model="form.email"
          type="email"
          required
          autocomplete="email"
          placeholder="your@email.com"
          class="flex-1 min-w-0 h-10 px-4 rounded-xl border border-white/[0.08] bg-white/[0.03] text-white placeholder-white/25 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm"
        />
        <button
          type="button"
          @click="handleSendCode"
          :disabled="sendingCode || countdown > 0"
          class="shrink-0 h-10 px-4 rounded-xl text-xs font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          :class="countdown > 0
            ? 'bg-white/[0.03] text-white/30 border border-white/[0.06]'
            : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/20 hover:bg-indigo-500/30'"
        >
          <i v-if="sendingCode" class="fas fa-spinner fa-spin"></i>
          <template v-else-if="countdown > 0">{{ countdown }}s</template>
          <template v-else>发送验证码</template>
        </button>
      </div>
    </div>

    <div>
      <label class="block text-sm font-medium text-white/60 mb-2">验证码</label>
      <input
        v-model="form.code"
        type="text"
        required
        inputmode="numeric"
        maxlength="6"
        placeholder="6 位验证码"
        autocomplete="one-time-code"
        class="w-full h-10 px-4 rounded-xl border border-white/[0.08] bg-white/[0.03] text-white placeholder-white/25 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm tracking-widest"
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
          class="w-full h-10 px-4 pr-11 rounded-lg border border-white/[0.08] bg-white/[0.05] text-white placeholder-white/25 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm"
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
