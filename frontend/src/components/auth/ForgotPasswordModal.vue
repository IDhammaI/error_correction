<script setup>
import { ref, reactive, onUnmounted, watch } from 'vue'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseInput from '@/components/base/BaseInput.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])

const step = ref(1)
const loading = ref(false)
const error = ref('')
const form = reactive({ email: '', code: '', password: '', confirm: '' })

const codeSending = ref(false)
const countdown = ref(0)
let timer = null

onUnmounted(() => clearInterval(timer))

watch(() => props.open, (val) => {
  if (!val) return
  step.value = 1
  error.value = ''
  Object.assign(form, { email: '', code: '', password: '', confirm: '' })
  countdown.value = 0
  clearInterval(timer)
})

function startCountdown() {
  countdown.value = 60
  timer = setInterval(() => {
    countdown.value -= 1
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
  if (!form.email.trim() || !form.email.includes('@')) {
    error.value = '请输入正确的邮箱'
    return
  }
  if (!form.code.trim()) {
    error.value = '请输入验证码'
    return
  }
  if (form.password.length < 6) {
    error.value = '密码至少 6 位'
    return
  }
  if (form.password !== form.confirm) {
    error.value = '两次密码不一致'
    return
  }

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
    <Transition name="fp-overlay" appear>
      <div
        v-if="open"
        class="fp-backdrop fixed inset-0 z-50 bg-black/60"
        @click="emit('close')"
      ></div>
    </Transition>

    <Transition name="fp-content" appear>
      <div v-if="open" class="fixed inset-0 z-[51] flex items-center justify-center p-4">
        <div
          class="relative w-full max-w-sm rounded-2xl border border-gray-200 bg-white/95 p-6 shadow-xl transition-colors duration-200 backdrop-blur-xl dark:border-white/[0.08] dark:bg-[#0A0A0F]/95"
          @click.stop
        >
          <button
            @click="emit('close')"
            class="absolute right-4 top-4 text-gray-400 transition-colors hover:text-gray-600 dark:text-white/25 dark:hover:text-white/50"
          >
            <i class="fas fa-xmark text-sm"></i>
          </button>

          <template v-if="step === 1">
            <h3 class="mb-1 text-xl font-bold text-gray-900 transition-colors dark:text-white">找回密码</h3>
            <p class="mb-6 text-sm text-gray-500 transition-colors dark:text-white/40">输入注册邮箱和验证码，设置新密码</p>

            <div class="space-y-4">
              <BaseInput
                v-model="form.email"
                type="email"
                label="邮箱"
                placeholder="your@email.com"
              >
                <template #append>
                  <button
                    type="button"
                    @click="sendCode"
                    :disabled="codeSending || countdown > 0"
                    class="h-10 shrink-0 rounded-xl border px-4 text-xs font-medium text-gray-700 transition-all disabled:cursor-not-allowed disabled:opacity-50 dark:text-white/70"
                    :class="countdown > 0
                      ? 'border-gray-200 bg-gray-100 text-gray-400 dark:border-white/[0.05] dark:bg-white/[0.02] dark:text-white/30'
                      : 'border-gray-200 bg-white hover:bg-gray-50 hover:text-gray-900 dark:border-white/[0.08] dark:bg-white/[0.03] dark:hover:bg-white/[0.06] dark:hover:text-white/85'"
                  >
                    <i v-if="codeSending" class="fas fa-spinner fa-spin"></i>
                    <template v-else-if="countdown > 0">{{ countdown }}s</template>
                    <template v-else>发送验证码</template>
                  </button>
                </template>
              </BaseInput>

              <BaseInput
                v-model="form.code"
                label="验证码"
                inputmode="numeric"
                maxlength="6"
                placeholder="请输入验证码"
                autocomplete="one-time-code"
                inputClass="tracking-widest"
              />

              <BaseInput
                v-model="form.password"
                type="password"
                label="新密码"
                placeholder="请输入新密码（至少 6 位）"
              />

              <BaseInput
                v-model="form.confirm"
                type="password"
                label="确认密码"
                placeholder="再次输入新密码"
              />

              <p v-if="error" class="flex items-center gap-2 text-sm text-rose-500 transition-colors dark:text-rose-400">
                <i class="fas fa-circle-exclamation text-xs"></i>{{ error }}
              </p>

              <BaseButton variant="cta" class="w-full" :disabled="loading" @click="resetPassword">
                <i v-if="loading" class="fas fa-spinner fa-spin text-xs"></i>
                <span>{{ loading ? '重置中...' : '重置密码' }}</span>
              </BaseButton>
            </div>
          </template>

          <template v-else>
            <div class="py-4 text-center">
              <div class="mb-4 inline-flex size-12 items-center justify-center rounded-full bg-emerald-500/10 transition-colors">
                <i class="fas fa-check text-xl text-emerald-500 transition-colors dark:text-emerald-400"></i>
              </div>
              <h3 class="mb-2 text-xl font-bold text-gray-900 transition-colors dark:text-white">密码已重置</h3>
              <p class="mb-6 text-sm text-gray-500 transition-colors dark:text-white/40">请使用新密码登录</p>
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
.fp-backdrop {
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.fp-overlay-enter-active,
.fp-overlay-leave-active {
  transition:
    opacity 0.22s ease,
    backdrop-filter 0.22s ease,
    -webkit-backdrop-filter 0.22s ease;
}

.fp-overlay-enter-from,
.fp-overlay-leave-to {
  opacity: 0;
  backdrop-filter: blur(0px);
  -webkit-backdrop-filter: blur(0px);
}

.fp-content-enter-active,
.fp-content-leave-active {
  transition: opacity 0.22s ease, transform 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

.fp-content-enter-from,
.fp-content-leave-to {
  opacity: 0;
  transform: scale(0.96) translateY(8px);
}
</style>
