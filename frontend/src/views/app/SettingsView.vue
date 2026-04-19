<script setup>
import { computed, ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { fetchAppConfig, updateAppConfig, updateProfile, uploadProfileAvatar, deleteProfileAvatar } from '@/api.js'
import { genId } from '@/utils.js'
import { useAuth } from '@/composables/useAuth.js'
import { useToast } from '@/composables/useToast.js'
import { useSystemStatus } from '@/composables/useSystemStatus.js'
import ContentPanel from '@/components/workspace/ContentPanel.vue'
import ProviderDialog from '@/components/settings/ProviderDialog.vue'
import ProviderSection from '@/components/settings/ProviderSection.vue'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseInput from '@/components/base/BaseInput.vue'
import BaseListGroup from '@/components/base/BaseListGroup.vue'
import BaseListItem from '@/components/base/BaseListItem.vue'
import BaseModal from '@/components/base/BaseModal.vue'

const props = defineProps({
  section: { type: String, default: 'profile' },
})

const { currentUser, quota, setCurrentUser } = useAuth()
const { pushToast } = useToast()
const { doFetchStatus } = useSystemStatus()

const quotaResetText = computed(() => {
  const resetAt = quota.value?.reset_at
  if (!resetAt) return '每日凌晨自动重置免费体验次数'
  const date = new Date(resetAt)
  if (Number.isNaN(date.getTime())) return '每日凌晨自动重置免费体验次数'
  return `下次重置时间：${date.toLocaleString('zh-CN', { hour12: false })}`
})

const isProfileSection = computed(() => props.section === 'profile')
const isQuotaSection = computed(() => props.section === 'quota')
const isApiSection = computed(() => props.section === 'api')
const settingsPageTitle = computed(() => {
  if (isApiSection.value) return 'API 设置'
  if (isQuotaSection.value) return '免费额度'
  return '用户资料设置'
})
const settingsPageDescription = computed(() => {
  if (isApiSection.value) return '集中管理 AI 与 OCR provider 的接口配置。'
  if (isQuotaSection.value) return '查看系统托管 AI / OCR 服务的免费体验额度与每日重置时间。'
  return '配置显示名称、昵称与头像，侧边栏会立即同步展示。'
})
const pageTitle = computed(() => isApiSection.value ? 'API 设置' : '用户资料设置')
const pageDescription = computed(() => {
  return isApiSection.value
    ? '管理 AI 模型供应商与 OCR 服务连接参数，修改即时生效。'
    : '配置显示名称、昵称与头像，侧边栏会立即同步展示。'
})

const loading = ref(true)
const saving = ref(false)
const profileSaving = ref(false)
const profileUploading = ref(false)
const profileDeletingAvatar = ref(false)
const profileError = ref('')
const profileForm = ref({
  display_name: '',
  nickname: '',
})
const avatarInputRef = ref(null)
const selectedAvatarFile = ref(null)
const avatarPreviewUrl = ref('')
const avatarUploadXhr = ref(null)

// ---------- 修改邮箱弹窗逻辑 ----------
const isEmailDialogOpen = ref(false)
const isEmailCodeDialogOpen = ref(false)
const emailFormSaving = ref(false)
const emailFormError = ref('')
const emailCodeError = ref('')
const emailForm = ref({ newEmail: '', code: '' })
const emailCodeSending = ref(false)
const emailChecking = ref(false)
const emailCodeCooldown = ref(0)
let emailCodeTimer = null

const openEmailDialog = () => {
  emailForm.value.newEmail = ''
  emailForm.value.code = ''
  emailFormError.value = ''
  emailCodeError.value = ''
  isEmailDialogOpen.value = true
  isEmailCodeDialogOpen.value = false
}

const closeEmailDialog = () => {
  isEmailDialogOpen.value = false
}

const closeEmailCodeDialog = () => {
  isEmailCodeDialogOpen.value = false
}

const handleEmailNextStep = async () => {
  if (!emailForm.value.newEmail || emailChecking.value) return
  if (!emailForm.value.newEmail.includes('@')) {
    emailFormError.value = '请输入有效的邮箱地址'
    return
  }
  if (emailForm.value.newEmail === currentUser.value?.email) {
    emailFormError.value = '新邮箱不能与当前邮箱相同'
    return
  }
  
  emailChecking.value = true
  emailFormError.value = ''
  
  try {
    const resp = await fetch('/api/auth/check-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: emailForm.value.newEmail }),
    })
    const data = await resp.json().catch(() => null)
    if (!resp.ok || !data?.success) {
      throw new Error(data?.error || '邮箱校验失败')
    }
    
    // 校验通过，进入下一步
    emailFormError.value = ''
    isEmailDialogOpen.value = false
    isEmailCodeDialogOpen.value = true
    // 自动触发发送验证码
    sendVerificationCode()
  } catch (e) {
    emailFormError.value = e instanceof Error ? e.message : String(e)
  } finally {
    emailChecking.value = false
  }
}

const sendVerificationCode = async () => {
  if (emailCodeSending.value || emailCodeCooldown.value > 0) return
  
  const currentEmail = currentUser.value?.email
  if (!currentEmail) {
    emailFormError.value = '未绑定原邮箱，无法发送验证码'
    return
  }

  emailCodeSending.value = true
  emailCodeError.value = ''
  
  try {
    const resp = await fetch('/api/auth/send-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: currentEmail, type: 'change_email' }),
    })
    const data = await resp.json().catch(() => null)
    if (!resp.ok || !data?.success) {
      throw new Error(data?.error || '发送失败，请重试')
    }
    
    pushToast('success', '验证码已发送至原邮箱')
    emailCodeCooldown.value = 60
    emailCodeTimer = setInterval(() => {
      emailCodeCooldown.value--
      if (emailCodeCooldown.value <= 0) {
        clearInterval(emailCodeTimer)
      }
    }, 1000)
  } catch (e) {
    emailCodeError.value = e instanceof Error ? e.message : String(e)
    pushToast('error', emailCodeError.value)
  } finally {
    emailCodeSending.value = false
  }
}

const submitEmailChange = async () => {
  if (emailFormSaving.value || !emailForm.value.newEmail || !emailForm.value.code) return
  
  // 简单的前端校验
  if (!emailForm.value.newEmail.includes('@')) {
    emailFormError.value = '请输入有效的邮箱地址'
    return
  }

  emailFormSaving.value = true
  emailCodeError.value = ''
  try {
    const user = await updateProfile({ 
      email: emailForm.value.newEmail,
      code: emailForm.value.code 
    })
    setCurrentUser(user)
    pushToast('success', '邮箱修改成功')
    closeEmailCodeDialog()
  } catch (e) {
    emailCodeError.value = e instanceof Error ? e.message : String(e)
    pushToast('error', emailCodeError.value)
  } finally {
    emailFormSaving.value = false
  }
}

const userPreviewName = computed(() => {
  return profileForm.value.display_name.trim()
    || profileForm.value.nickname.trim()
    || currentUser.value?.username
    || '未登录用户'
})

const userPreviewInitial = computed(() => {
  return userPreviewName.value?.trim()?.[0]?.toUpperCase() || '?'
})

const displayedAvatarUrl = computed(() => {
  return avatarPreviewUrl.value || currentUser.value?.avatar_url || ''
})

const clearAvatarPreview = () => {
  if (avatarPreviewUrl.value) {
    URL.revokeObjectURL(avatarPreviewUrl.value)
  }
  avatarPreviewUrl.value = ''
  selectedAvatarFile.value = null
  if (avatarInputRef.value) {
    avatarInputRef.value.value = ''
  }
}

const syncProfileForm = () => {
  profileForm.value = {
    display_name: currentUser.value?.display_name || '',
    nickname: currentUser.value?.nickname || '',
  }
}

watch(currentUser, syncProfileForm, { immediate: true })

const saveProfile = async () => {
  if (profileSaving.value) return
  profileSaving.value = true
  profileError.value = ''
  try {
    const user = await updateProfile({
      display_name: profileForm.value.display_name,
      nickname: profileForm.value.nickname,
    })
    setCurrentUser(user)
    pushToast('success', '个人资料已保存')
  } catch (e) {
    profileError.value = e instanceof Error ? e.message : String(e)
    pushToast('error', profileError.value)
  } finally {
    profileSaving.value = false
  }
}

const chooseAvatarFile = () => {
  if (profileUploading.value || profileDeletingAvatar.value) return
  avatarInputRef.value?.click()
}

const onAvatarFileChange = (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  clearAvatarPreview()
  selectedAvatarFile.value = file
  avatarPreviewUrl.value = URL.createObjectURL(file)
  profileError.value = ''
}

const submitAvatarUpload = () => {
  if (!selectedAvatarFile.value || profileUploading.value) return
  profileUploading.value = true
  profileError.value = ''
  avatarUploadXhr.value = uploadProfileAvatar(selectedAvatarFile.value, {
    onSuccess: (user) => {
      setCurrentUser(user)
      clearAvatarPreview()
      profileUploading.value = false
      avatarUploadXhr.value = null
      pushToast('success', '头像已更新')
    },
    onError: (error) => {
      profileError.value = error instanceof Error ? error.message : String(error)
      profileUploading.value = false
      avatarUploadXhr.value = null
      pushToast('error', profileError.value)
    },
    onAbort: () => {
      profileUploading.value = false
      avatarUploadXhr.value = null
    },
  })
}

const removeAvatar = async () => {
  if (profileDeletingAvatar.value || profileUploading.value) return
  profileDeletingAvatar.value = true
  profileError.value = ''
  try {
    const user = await deleteProfileAvatar()
    setCurrentUser(user)
    clearAvatarPreview()
    pushToast('success', '头像已删除')
  } catch (e) {
    profileError.value = e instanceof Error ? e.message : String(e)
    pushToast('error', profileError.value)
  } finally {
    profileDeletingAvatar.value = false
  }
}

onBeforeUnmount(() => {
  if (avatarUploadXhr.value) avatarUploadXhr.value.abort()
  clearAvatarPreview()
})

// ---------- 多 Provider 数据结构 ----------

const makeOpenAIProvider = (data = {}) => ({
  id: data.id || genId(),
  name: data.name || '',
  api_key: data.api_key || '',
  base_url: data.base_url || '',
  model_name: data.model_name || '',
  light_model_name: data.light_model_name || '',
  supports_function_calling: data.supports_function_calling ?? true,
  api_key_set: data.api_key_set || false,
  api_key_hint: data.api_key_hint || '',
})

const makeAnthropicProvider = (data = {}) => ({
  id: data.id || genId(),
  name: data.name || '',
  api_key: data.api_key || '',
  base_url: data.base_url || '',
  model_name: data.model_name || '',
  api_key_set: data.api_key_set || false,
  api_key_hint: data.api_key_hint || '',
})

const makePaddleOCRProvider = (data = {}) => ({
  id: data.id || genId(),
  name: data.name || '',
  api_key: data.api_key || '',
  base_url: data.base_url || data.api_url || '',
  model_name: data.model_name || data.model || '',
  use_doc_orientation: data.use_doc_orientation || false,
  use_doc_unwarping: data.use_doc_unwarping || false,
  use_chart_recognition: data.use_chart_recognition || false,
  api_key_set: data.api_key_set || data.api_token_set || false,
  api_key_hint: data.api_key_hint || data.api_token_hint || '',
})

const openaiProviders = ref([])
const anthropicProviders = ref([])
const paddleocrProviders = ref([])

// 当前激活的 provider ID（每类只能激活一个）
const activeOpenaiId = ref(null)
const activeAnthropicId = ref(null)
const activePaddleocrId = ref(null)

const toggleActive = (type, id) => {
  const refMap = { openai: activeOpenaiId, anthropic: activeAnthropicId, paddleocr: activePaddleocrId }
  const target = refMap[type]
  target.value = target.value === id ? null : id
}

// ---------- 加载 / 保存 ----------

const loadConfig = async () => {
  configLoaded.value = false
  loading.value = true
  try {
    const cfg = await fetchAppConfig()

    if (cfg.openai_providers && cfg.openai_providers.length > 0) {
      openaiProviders.value = cfg.openai_providers.map(p => makeOpenAIProvider(p))
    } else if (cfg.openai) {
      openaiProviders.value = [makeOpenAIProvider({ name: 'Default', ...cfg.openai })]
    } else {
      openaiProviders.value = []
    }
    activeOpenaiId.value = cfg.active_openai_id || openaiProviders.value[0]?.id || null

    if (cfg.anthropic_providers && cfg.anthropic_providers.length > 0) {
      anthropicProviders.value = cfg.anthropic_providers.map(p => makeAnthropicProvider(p))
    } else if (cfg.anthropic) {
      anthropicProviders.value = [makeAnthropicProvider({ name: 'Default', ...cfg.anthropic })]
    } else {
      anthropicProviders.value = []
    }
    activeAnthropicId.value = cfg.active_anthropic_id || anthropicProviders.value[0]?.id || null

    if (cfg.paddleocr_providers && cfg.paddleocr_providers.length > 0) {
      paddleocrProviders.value = cfg.paddleocr_providers.map(p => makePaddleOCRProvider(p))
    } else if (cfg.paddleocr) {
      paddleocrProviders.value = [makePaddleOCRProvider({ name: 'Default', ...cfg.paddleocr })]
    } else {
      paddleocrProviders.value = []
    }
    activePaddleocrId.value = cfg.active_paddleocr_id || paddleocrProviders.value[0]?.id || null
  } catch (e) {
    pushToast('error', '加载配置失败: ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    loading.value = false
    setTimeout(() => { configLoaded.value = true }, 0)
  }
}

const saveConfig = async () => {
  if (saving.value) return
  saving.value = true
  try {
    const payload = {}

    payload.openai_providers = openaiProviders.value.map(p => {
      const item = { id: p.id, name: p.name, base_url: p.base_url, model_name: p.model_name, light_model_name: p.light_model_name, supports_function_calling: p.supports_function_calling }
      if (p.api_key) item.api_key = p.api_key
      return item
    })

    payload.anthropic_providers = anthropicProviders.value.map(p => {
      const item = { id: p.id, name: p.name, base_url: p.base_url, model_name: p.model_name }
      if (p.api_key) item.api_key = p.api_key
      return item
    })

    payload.paddleocr_providers = paddleocrProviders.value.map(p => {
      const item = { id: p.id, name: p.name, api_url: p.base_url, model: p.model_name, use_doc_orientation: p.use_doc_orientation, use_doc_unwarping: p.use_doc_unwarping, use_chart_recognition: p.use_chart_recognition }
      if (p.api_key) item.api_token = p.api_key
      return item
    })

    payload.active_openai_id = activeOpenaiId.value
    payload.active_anthropic_id = activeAnthropicId.value
    payload.active_paddleocr_id = activePaddleocrId.value

    await updateAppConfig(payload)
    doFetchStatus()
  } catch (e) {
    pushToast('error', '保存失败: ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    saving.value = false
  }
}

// ---------- 自动保存（防抖） ----------
let autoSaveTimer = null
const configLoaded = ref(false)

watch(
  [openaiProviders, anthropicProviders, paddleocrProviders, activeOpenaiId, activeAnthropicId, activePaddleocrId],
  () => {
    if (!configLoaded.value) return
    clearTimeout(autoSaveTimer)
    autoSaveTimer = setTimeout(() => saveConfig(), 600)
  },
  { deep: true },
)

const removeProvider = async (type, idx) => {
  const listMap = { openai: openaiProviders, anthropic: anthropicProviders, paddleocr: paddleocrProviders }
  const activeMap = { openai: activeOpenaiId, anthropic: activeAnthropicId, paddleocr: activePaddleocrId }
  const list = listMap[type]
  if (list.value[idx]?.id === activeMap[type].value) activeMap[type].value = null
  list.value.splice(idx, 1)
  clearTimeout(autoSaveTimer)
  try {
    await saveConfig()
    pushToast('success', '已删除')
  } catch { /* saveConfig 内部已 toast error */ }
}

// ---------- 弹窗控制 ----------
const dialogOpen = ref(false)
const dialogType = ref('openai')
const dialogEditData = ref(null)
const dialogEditIndex = ref(-1)

const openAddDialog = (type) => {
  dialogType.value = type
  dialogEditData.value = null
  dialogEditIndex.value = -1
  dialogOpen.value = true
}

const openEditDialog = (type, provider, idx) => {
  dialogType.value = type
  dialogEditData.value = { ...provider }
  dialogEditIndex.value = idx
  dialogOpen.value = true
}

const onDialogConfirm = async (formData) => {
  if (dialogEditIndex.value >= 0) {
    const listMap = { openai: openaiProviders, anthropic: anthropicProviders, paddleocr: paddleocrProviders }
    const list = listMap[dialogType.value]
    const existing = list.value[dialogEditIndex.value]
    if (existing) {
      Object.assign(existing, formData)
      if (dialogType.value === 'paddleocr') {
        existing.base_url = formData.base_url
        existing.model_name = formData.model_name
      }
    }
  } else {
    if (dialogType.value === 'openai') {
      const p = makeOpenAIProvider(formData)
      openaiProviders.value.push(p)
      if (openaiProviders.value.length === 1) activeOpenaiId.value = p.id
    } else if (dialogType.value === 'anthropic') {
      const p = makeAnthropicProvider(formData)
      anthropicProviders.value.push(p)
      if (anthropicProviders.value.length === 1) activeAnthropicId.value = p.id
    } else {
      const p = makePaddleOCRProvider({ name: formData.name, api_key: formData.api_key, api_url: formData.base_url, model: formData.model_name, use_doc_orientation: formData.use_doc_orientation, use_doc_unwarping: formData.use_doc_unwarping, use_chart_recognition: formData.use_chart_recognition })
      paddleocrProviders.value.push(p)
      if (paddleocrProviders.value.length === 1) activePaddleocrId.value = p.id
    }
  }
  const isEdit = dialogEditIndex.value >= 0
  dialogOpen.value = false

  clearTimeout(autoSaveTimer)
  try {
    await saveConfig()
    pushToast('success', isEdit ? '配置已更新' : '供应商已添加')
  } catch { /* saveConfig 内部已 toast error */ }
}

onMounted(() => { loadConfig() })
</script>

<template>
  <ContentPanel :title="settingsPageTitle">
    <div class="relative h-full overflow-y-auto">
      <div class="container relative z-10 mx-auto max-w-3xl pt-6">

        <div v-if="loading && isProfileSection" class="mx-auto max-w-2xl animate-pulse">
          <!-- 骨架屏：头像区域 -->
          <div class="mb-8 mt-4 flex flex-col items-center justify-center">
            <div class="h-24 w-24 rounded-full bg-gray-200 dark:bg-white/[0.08]"></div>
          </div>
          
          <!-- 骨架屏：列表分组 -->
          <BaseListGroup>
            <template #header>
              <div class="mb-3 ml-1 h-5 w-20 rounded bg-gray-200 dark:bg-white/[0.08]"></div>
            </template>
            
            <BaseListItem skeleton />
            <BaseListItem skeleton>
              <template #skeleton-right>
                <div class="flex items-center justify-end gap-3 w-full">
                  <div class="h-4 w-32 rounded bg-gray-200 dark:bg-white/[0.08]"></div>
                  <div class="h-6 w-6 shrink-0 rounded-full bg-gray-200 dark:bg-white/[0.08]"></div>
                </div>
              </template>
            </BaseListItem>
            <BaseListItem skeleton>
              <template #skeleton-right>
                <div class="h-9 w-full rounded-lg bg-gray-200 dark:bg-white/[0.08]"></div>
              </template>
            </BaseListItem>
            <BaseListItem skeleton>
              <template #skeleton-right>
                <div class="h-9 w-full rounded-lg bg-gray-200 dark:bg-white/[0.08]"></div>
              </template>
            </BaseListItem>
          </BaseListGroup>
          
          <!-- 骨架屏：保存按钮 -->
          <div class="mt-6 flex justify-center">
            <div class="h-12 w-full max-w-xs rounded-xl bg-gray-200 dark:bg-white/[0.08]"></div>
          </div>
        </div>

        <div v-else-if="loading && isQuotaSection" class="space-y-6 animate-pulse">
          <div class="h-48 w-full rounded-2xl bg-gray-200 dark:bg-white/[0.08]"></div>
        </div>

        <div v-else-if="loading && isApiSection" class="space-y-6 animate-pulse">
          <div class="h-32 w-full rounded-2xl bg-gray-200 dark:bg-white/[0.08]"></div>
          <div class="h-32 w-full rounded-2xl bg-gray-200 dark:bg-white/[0.08]"></div>
          <div class="h-32 w-full rounded-2xl bg-gray-200 dark:bg-white/[0.08]"></div>
        </div>

        <div v-else-if="isProfileSection || isQuotaSection" class="space-y-6">
          <section v-if="isQuotaSection" class="rounded-2xl border border-white/[0.06] border-t-white/[0.15] border-b-white/[0.03] bg-white/[0.02] p-6 backdrop-blur-xl">
            <div class="mb-4 flex items-start justify-between gap-4">
              <div>
                <h2 class="text-xl font-semibold text-slate-900 dark:text-white">免费体验额度</h2>
                <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">使用平台托管的 AI / OCR 服务时会消耗每日免费次数；使用你自己的已配置 provider 不会扣减。</p>
              </div>
              <div class="rounded-full border border-[rgb(145,132,235)]/20 bg-[rgb(145,132,235)]/10 px-3 py-1 text-xs font-medium text-[rgb(145,132,235)]">
                {{ quota?.remaining ?? '--' }} / {{ quota?.daily_free_quota ?? '--' }}
              </div>
            </div>

            <div class="grid gap-4 md:grid-cols-3">
              <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                <p class="text-xs text-slate-500 dark:text-slate-400">每日额度</p>
                <p class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">{{ quota?.daily_free_quota ?? '--' }}</p>
              </div>
              <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                <p class="text-xs text-slate-500 dark:text-slate-400">今日已用</p>
                <p class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">{{ quota?.daily_free_used ?? '--' }}</p>
              </div>
              <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                <p class="text-xs text-slate-500 dark:text-slate-400">今日剩余</p>
                <p class="mt-2 text-2xl font-semibold text-[rgb(145,132,235)]">{{ quota?.remaining ?? '--' }}</p>
              </div>
            </div>

            <p class="mt-4 text-sm text-slate-500 dark:text-slate-400">{{ quotaResetText }}</p>
          </section>

          <section v-if="isProfileSection" class="mx-auto max-w-2xl pb-12">
            <!-- 头像区域 (类 Linear 顶部居中大图) -->
            <div class="mb-8 mt-4 flex flex-col items-center justify-center">
              <div class="relative group h-24 w-24 overflow-hidden rounded-full border border-gray-200 bg-gray-50 shadow-sm dark:border-white/[0.08] dark:bg-white/[0.03]">
                <img
                  v-if="displayedAvatarUrl"
                  :src="displayedAvatarUrl"
                  alt="头像预览"
                  class="h-full w-full object-cover transition-opacity group-hover:opacity-80"
                />
                <div
                  v-else
                  class="relative flex h-full w-full items-center justify-center text-3xl font-bold text-white transition-opacity group-hover:opacity-80"
                  style="background: linear-gradient(to bottom, rgba(129,115,223,0.9), rgba(99,87,199,0.9));"
                >
                  <span class="absolute inset-0 pointer-events-none" style="background-image: linear-gradient(to right, rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.06) 1px, transparent 1px); background-size: 8px 8px; mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%); -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);"></span>
                  <span class="relative z-10">{{ userPreviewInitial }}</span>
                </div>
                
                <!-- 悬浮遮罩提示 -->
                <div 
                  class="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition-opacity group-hover:opacity-100 cursor-pointer"
                  @click="chooseAvatarFile"
                >
                  <i class="fas fa-camera text-white"></i>
                </div>
              </div>
              <input
                ref="avatarInputRef"
                type="file"
                accept=".png,.jpg,.jpeg,.webp,.bmp,image/png,image/jpeg,image/webp,image/bmp"
                class="hidden"
                @change="onAvatarFileChange"
              />

              <!-- 头像操作按钮组 -->
              <div v-if="selectedAvatarFile" class="mt-4 flex gap-2">
                <BaseButton variant="primary" :disabled="profileUploading" @click="submitAvatarUpload" class="!px-3 !py-1 !text-xs !rounded-full">
                  <i v-if="profileUploading" class="fas fa-spinner fa-spin"></i>
                  <i v-else class="fas fa-check"></i> 保存头像
                </BaseButton>
                <BaseButton variant="secondary" :disabled="profileUploading" @click="clearAvatarPreview" class="!px-3 !py-1 !text-xs !rounded-full">
                  取消
                </BaseButton>
              </div>
              <div v-else-if="currentUser?.avatar_url" class="mt-4">
                <button 
                  @click="removeAvatar"
                  :disabled="profileDeletingAvatar"
                  class="text-xs text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300"
                >
                  <i v-if="profileDeletingAvatar" class="fas fa-spinner fa-spin mr-1"></i>移除头像
                </button>
              </div>
            </div>

            <!-- Linear 风格设置列表 -->
            <BaseListGroup title="账户信息">
              <!-- 用户名行 -->
              <BaseListItem 
                label="用户名" 
                description="您的唯一登录凭证"
              >
                <div class="flex items-center justify-end gap-2 px-3 py-2">
                  <span class="text-sm text-gray-900 dark:text-[#f7f8f8]">
                    {{ '@' + (currentUser?.username || 'guest') }}
                  </span>
                </div>
              </BaseListItem>
              
              <!-- 邮箱行 -->
              <BaseListItem 
                label="注册邮箱" 
              >
                <div class="flex items-center justify-end gap-3 px-3 py-2">
                  <span class="text-[13px] font-medium text-gray-900 dark:text-[#f7f8f8]">
                    {{ currentUser?.email || '未绑定邮箱' }}
                  </span>
                  <!-- 修改邮箱的图标按钮 -->
                  <button 
                    type="button" 
                    class="flex h-6 w-6 shrink-0 items-center justify-center !rounded-full bg-white shadow-[0_0_0_1px_rgba(0,0,0,0.08),0_1px_2px_rgba(0,0,0,0.05)] text-[#6B6F76] hover:bg-[#F2F3F5] hover:text-[#111318] dark:bg-white/[0.04] dark:shadow-[0_0_0_1px_rgba(255,255,255,0.08)] dark:text-[#8A8F98] dark:hover:bg-white/[0.08] dark:hover:text-[#f7f8f8] transition-colors"
                    title="修改邮箱"
                    @click="openEmailDialog"
                  >
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                      <path d="M10.1805 3.34195L4.14166 9.416C5.32948 9.77021 6.29238 10.6629 6.74008 11.8184L12.6877 5.8425C11.6642 5.22123 10.8043 4.36352 10.1805 3.34195Z"></path>
                      <path d="M13.7391 4.71631C14.1575 4.02948 14.0727 3.11738 13.4846 2.5219C12.8908 1.92072 11.9784 1.83892 11.298 2.27649C11.8547 3.31132 12.7037 4.15999 13.7391 4.71631Z"></path>
                      <path d="M3.03104 10.7502C4.30296 10.7658 5.36645 11.7423 5.49783 13.0114C4.83268 13.426 3.40197 13.7922 2.53114 13.9886C2.2001 14.0632 1.92026 13.7602 2.02075 13.4373C2.25326 12.6902 2.64592 11.5136 3.03104 10.7502Z"></path>
                    </svg>
                  </button>
                </div>
              </BaseListItem>
              
              <!-- 显示名称行 -->
              <BaseListItem 
                label="显示名称" 
                description="用于在应用中展示的主要名称"
              >
                <BaseInput 
                  v-model="profileForm.display_name" 
                  placeholder="例如：小哲"
                  maxlength="50"
                  inputClass="!h-9 !py-1.5 shadow-sm no-underline"
                />
              </BaseListItem>
              
              <!-- 昵称行 -->
              <BaseListItem 
                label="当前昵称" 
                description="可选的个性化称呼"
              >
                <BaseInput 
                  v-model="profileForm.nickname" 
                  placeholder="例如：数学冲刺版"
                  maxlength="50"
                  inputClass="!h-9 !py-1.5 shadow-sm no-underline"
                />
              </BaseListItem>
            </BaseListGroup>

            <!-- 错误提示 -->
            <p v-if="profileError" class="mb-4 flex items-center gap-2 text-sm text-rose-400 justify-center">
              <i class="fas fa-circle-exclamation text-xs"></i>
              <span>{{ profileError }}</span>
            </p>

            <!-- 保存按钮 -->
            <div class="flex justify-center mt-6">
              <BaseButton 
                variant="primary" 
                :disabled="profileSaving || profileUploading || profileDeletingAvatar" 
                @click="saveProfile"
                class="!w-full max-w-xs !h-12 !rounded-xl !text-base"
              >
                <i v-if="profileSaving" class="fas fa-spinner fa-spin mr-2"></i>
                {{ profileSaving ? '保存中...' : '保存更改' }}
              </BaseButton>
            </div>
          </section>
        </div>

        <div v-else class="space-y-6">
          <ProviderSection
            icon="fa-solid fa-bolt"
            title="OpenAI 兼容 API"
            subtitle="支持 OpenAI / DeepSeek / Qwen / Moonshot 等"
            :providers="openaiProviders"
            :active-id="activeOpenaiId"
            @add="openAddDialog('openai')"
            @toggle-active="(id) => toggleActive('openai', id)"
            @edit="(p, idx) => openEditDialog('openai', p, idx)"
            @remove="(idx) => removeProvider('openai', idx)"
          />

          <ProviderSection
            icon="fa-solid fa-brain"
            title="Anthropic API"
            subtitle="Claude 系列模型"
            :providers="anthropicProviders"
            :active-id="activeAnthropicId"
            @add="openAddDialog('anthropic')"
            @toggle-active="(id) => toggleActive('anthropic', id)"
            @edit="(p, idx) => openEditDialog('anthropic', p, idx)"
            @remove="(idx) => removeProvider('anthropic', idx)"
          />

          <ProviderSection
            icon="fa-solid fa-eye"
            title="PaddleOCR"
            subtitle="文档 OCR 识别服务"
            :providers="paddleocrProviders"
            :active-id="activePaddleocrId"
            @add="openAddDialog('paddleocr')"
            @toggle-active="(id) => toggleActive('paddleocr', id)"
            @edit="(p, idx) => openEditDialog('paddleocr', p, idx)"
            @remove="(idx) => removeProvider('paddleocr', idx)"
          />
        </div>
      </div>

      <ProviderDialog
        :open="dialogOpen"
        :type="dialogType"
        :edit-data="dialogEditData"
        @close="dialogOpen = false"
        @confirm="onDialogConfirm"
      />
    </div>

    <!-- 修改邮箱第一步：输入新邮箱 -->
    <BaseModal
      :open="isEmailDialogOpen"
      title="修改邮箱"
      maxWidth="max-w-[30rem]"
      bodyClass="px-6 pb-2"
      @close="closeEmailDialog"
    >
      <form id="email-step1-form" autocomplete="off" class="space-y-6" @submit.prevent="handleEmailNextStep">
        <div class="space-y-6">
          <div class="space-y-3 text-[15px] leading-[1.6] text-slate-600 dark:text-slate-300">
            <p>如果您想更改当前账号的邮箱地址，我们需要向您的原邮箱发送一封验证邮件。此更改将应用于您所在的所有工作区。</p>
            <p>在继续操作之前，请确保新邮箱地址尚未绑定至现有账号。</p>
          </div>

          <div>
            <label class="mb-2 block text-[13px] font-semibold text-slate-700 dark:text-slate-300">输入您希望绑定的新邮箱地址</label>
            <BaseInput
              v-model="emailForm.newEmail"
              type="email"
              placeholder="新邮箱地址"
              inputClass="h-10 text-[15px] shadow-sm"
              required
            />
          </div>
        </div>

        <div v-if="emailFormError" class="text-sm text-rose-500 flex items-center gap-1.5">
          <i class="fas fa-circle-exclamation"></i>
          <span>{{ emailFormError }}</span>
        </div>
      </form>
      <template #footer>
        <BaseButton variant="secondary" class="!font-semibold !text-[13px] !h-9 !px-4 !rounded-lg" @click="closeEmailDialog">取消</BaseButton>
        <BaseButton
          type="submit"
          form="email-step1-form"
          class="!font-semibold !text-[13px] !h-9 !px-4 !rounded-lg"
          :disabled="emailChecking || !emailForm.newEmail"
        >
          <i v-if="emailChecking" class="fa-solid fa-circle-notch fa-spin mr-1.5 text-[10px]"></i>
          {{ emailChecking ? '验证中...' : '验证现有账号' }}
        </BaseButton>
      </template>
    </BaseModal>

    <!-- 修改邮箱第二步：身份验证 -->
    <BaseModal
      :open="isEmailCodeDialogOpen"
      title="修改邮箱"
      maxWidth="max-w-[30rem]"
      bodyClass="px-6 pb-2"
      @close="closeEmailCodeDialog"
    >
      <form id="email-step2-form" autocomplete="off" class="space-y-6" @submit.prevent="submitEmailChange">
        <div class="space-y-6">
          <div class="space-y-3 text-[15px] leading-[1.6] text-slate-600 dark:text-slate-300">
            <p>我们没有找到与 <strong class="font-medium text-slate-900 dark:text-[#f7f8f8]">{{ emailForm.newEmail }}</strong> 关联的现有账号。您可以安全地继续修改邮箱。</p>
            <p>为了验证您的身份，我们需要向您当前的邮箱 <strong class="font-medium text-slate-900 dark:text-[#f7f8f8]">{{ currentUser?.email }}</strong> 发送验证码。</p>
          </div>

          <div>
            <label class="mb-2 block text-[13px] font-semibold text-slate-700 dark:text-slate-300">原邮箱验证码</label>
            <div class="flex gap-3">
              <BaseInput
                v-model="emailForm.code"
                type="text"
                placeholder="6位数字验证码"
                maxlength="6"
                required
                class="flex-1"
                inputClass="h-10 text-[15px] shadow-sm"
              />
              <BaseButton 
                type="button" 
                variant="secondary" 
                class="w-36 shrink-0 !font-semibold !text-[13px] !h-10 !px-4 !rounded-xl" 
                :disabled="emailCodeCooldown > 0 || emailCodeSending"
                @click="sendVerificationCode"
              >
                <i v-if="emailCodeSending" class="fa-solid fa-circle-notch fa-spin text-xs mr-1.5"></i>
                <span v-else>{{ emailCodeCooldown > 0 ? `${emailCodeCooldown}秒后重发` : '获取验证码' }}</span>
              </BaseButton>
            </div>
          </div>
        </div>

        <div v-if="emailCodeError" class="text-sm text-rose-500 flex items-center gap-1.5">
          <i class="fas fa-circle-exclamation"></i>
          <span>{{ emailCodeError }}</span>
        </div>
      </form>
      <template #footer>
        <BaseButton variant="secondary" class="!font-semibold !text-[13px] !h-9 !px-4 !rounded-lg" @click="closeEmailCodeDialog">取消</BaseButton>
        <BaseButton
          type="submit"
          form="email-step2-form"
          class="!font-semibold !text-[13px] !h-9 !px-4 !rounded-lg"
          :disabled="emailFormSaving || !emailForm.code || emailForm.code.length !== 6"
        >
          <i v-if="emailFormSaving" class="fa-solid fa-circle-notch fa-spin mr-1.5 text-[10px]"></i>
          {{ emailFormSaving ? '发送中...' : '发送验证链接' }}
        </BaseButton>
      </template>
    </BaseModal>
  </ContentPanel>
</template>
