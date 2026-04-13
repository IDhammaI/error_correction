<script setup>
/**
 * ForgotPasswordModal.vue
 * 找回密码弹窗（邮箱验证码 + 重置密码）
 */
import { ref, reactive, onUnmounted, watch } from 'vue'
import BaseButton from '@/components/base/BaseButton.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
})
const emit = defineEmits(['close'])

const step = ref(1)        // 1: 表单  2: 完成
const loading = ref(false)
const error = ref('')
const showPwd = ref(false)
const showConfirm = ref(false)
const form = reactive({ email: '', code: '', password: '', confirm: '' })

// 验证码倒计时
const codeSending = ref(false)
const countdown = ref(0)
let timer = null
onUnmounted(() => clearInterval(timer))

// 打开时重置状态
watch(() => props.open, (val) => {
  if (val) {
    step.value = 1
    error.value = ''
    showPwd.value = false
    showConfirm.value = false
    Object.assign(form, { email: '', code: '', password: '', confirm: '' })
    countdown.value = 0
    clearInterval(timer)
  }
})

function startCountdown() {
  countdown.value = 60
  timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(timer)
  }, 1000)
}

async function sendCode() {
  if (codeSending.value || countdown.value > 0) return
  const email = form.email.trim()
  if (!email || !email.includes('@')) {
    error.value = '请输入正确的邮箱'
    return
  }
  error.value = ''
  codeSending.value = true
  try {
    const res = await fetch('/api/auth/send-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, type: 'reset' }),
    })
    const data = await res.json()
    if (!res.ok) {
      error.value = data.error || '发送失败'
    } else {
      startCountdown()
    }
  } catch {
    error.value = '网络错误，请重试'
  } finally {
    codeSending.value = false
  }
}

async function resetPassword() {
  error.value = ''
  if (!form.email.trim() || !form.email.includes('@')) { error.value = '请输入正确的邮箱'; return }
  if (!form.code.trim()) { error.value = '请输入验证码'; return }
  if (form.password.length < 6) { error.value = '密码至少 6 位'; return }
  if (form.password !== form.confirm) { error.value = '两次密码不一致'; return }
  loading.value = true
  try {
    const res = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: form.email,
        code: form.code.trim(),
        password: form.password,
      }),
    })
    const data = await res.json()
    if (!res.ok) {
      error.value = data.error || '重置失败'
    } else {
      step.value = 2
    }
  } catch {
    error.value = '网络错误，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fp-fade">
      <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <!-- 遮罩 -->
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="emit('close')"></div>

        <!-- 弹窗主体 -->
        <div
          class="relative w-full max-w-sm rounded-2xl border border-white/[0.08] bg-[#0A0A0F]/95 backdrop-blur-xl p-6 shadow-xl"
          @click.stop>
          <!-- 关闭按钮 -->
          <button @click="emit('close')"
            class="absolute right-4 top-4 text-white/25 hover:text-white/50 transition-colors">
            <i class="fas fa-xmark text-sm"></i>
          </button>

          <!-- Step 1: 邮箱 + 验证码 + 新密码 -->
          <template v-if="step === 1">
            <h3 class="text-xl font-bold text-white mb-1">找回密码</h3>
            <p class="text-sm text-white/40 mb-6">输入注册邮箱和验证码，设置新密码</p>

            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-white/60 mb-2">邮箱</label>
                <div class="flex gap-2">
                  <input v-model="form.email" type="email" placeholder="your@email.com"
                    class="flex-1 min-w-0 h-10 px-4 rounded-xl border border-white/[0.08] bg-white/[0.03] text-white placeholder-white/25 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm" />
                  <button type="button" @click="sendCode" :disabled="codeSending || countdown > 0"
                    class="shrink-0 h-10 px-4 rounded-xl text-xs font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    :class="countdown > 0
                      ? 'bg-white/[0.03] text-white/30 border border-white/[0.06]'
                      : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/20 hover:bg-indigo-500/30'">
                    <i v-if="codeSending" class="fas fa-spinner fa-spin"></i>
                    <template v-else-if="countdown > 0">{{ countdown }}s</template>
                    <template v-else>发送验证码</template>
                  </button>
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-white/60 mb-2">验证码</label>
                <input v-model="form.code" type="text" inputmode="numeric" maxlength="6" placeholder="请输入验证码"
                  autocomplete="one-time-code"
                  class="w-full h-10 px-4 rounded-xl border border-white/[0.08] bg-white/[0.03] text-white placeholder-white/25 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm tracking-widest" />
              </div>

              <div>
                <label class="block text-sm font-medium text-white/60 mb-2">新密码</label>
                <div class="relative">
                  <input v-model="form.password" :type="showPwd ? 'text' : 'password'" placeholder="请输入新密码（至少 6 位）"
                    class="w-full h-10 px-4 pr-11 rounded-xl border border-white/[0.08] bg-white/[0.03] text-white placeholder-white/25 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm" />
                  <button type="button" @click="showPwd = !showPwd"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-white/25 hover:text-white/50 transition-colors">
                    <i :class="showPwd ? 'fas fa-eye-slash' : 'fas fa-eye'" class="text-xs"></i>
                  </button>
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-white/60 mb-2">确认密码</label>
                <div class="relative">
                  <input v-model="form.confirm" :type="showConfirm ? 'text' : 'password'" placeholder="再次输入新密码"
                    class="w-full h-10 px-4 pr-11 rounded-xl border border-white/[0.08] bg-white/[0.03] text-white placeholder-white/25 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm" />
                  <button type="button" @click="showConfirm = !showConfirm"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-white/25 hover:text-white/50 transition-colors">
                    <i :class="showConfirm ? 'fas fa-eye-slash' : 'fas fa-eye'" class="text-xs"></i>
                  </button>
                </div>
              </div>

              <p v-if="error" class="text-sm text-rose-400 flex items-center gap-2">
                <i class="fas fa-circle-exclamation text-xs"></i>{{ error }}
              </p>

              <BaseButton variant="cta" class="w-full" :disabled="loading" @click="resetPassword">
                <i v-if="loading" class="fas fa-spinner fa-spin text-xs"></i>
                <span>{{ loading ? '重置中...' : '重置密码' }}</span>
              </BaseButton>
            </div>
          </template>

          <!-- Step 2: 完成 -->
          <template v-else>
            <div class="text-center py-4">
              <div class="inline-flex items-center justify-center size-12 rounded-full bg-emerald-500/10 mb-4">
                <i class="fas fa-check text-emerald-400 text-xl"></i>
              </div>
              <h3 class="text-xl font-bold text-white mb-2">密码已重置</h3>
              <p class="text-sm text-white/40 mb-6">请使用新密码登录</p>
              <BaseButton variant="cta" class="w-full" @click="emit('close')">
                返回登录
              </BaseButton>
            </div>
          </template>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fp-fade-enter-active,
.fp-fade-leave-active {
  transition: opacity 0.2s ease;
}

.fp-fade-enter-active .relative,
.fp-fade-leave-active .relative {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fp-fade-enter-from,
.fp-fade-leave-to {
  opacity: 0;
}

.fp-fade-enter-from .relative {
  transform: scale(0.95) translateY(8px);
}

.fp-fade-leave-to .relative {
  transform: scale(0.97) translateY(4px);
}
</style>
