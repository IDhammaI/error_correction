<script setup>
/**
 * ProviderDialog.vue
 * API Provider 配置弹窗
 */
import { ref, computed, watch } from 'vue'
import { useToast } from '@/composables/useToast.js'
import BaseModal from '@/components/base/BaseModal.vue'
import BaseInput from '@/components/base/BaseInput.vue'
import BaseButton from '@/components/base/BaseButton.vue'
import providerOpenaiIcon from '@/assets/provider-openai.svg'
import providerAnthropicIcon from '@/assets/provider-anthropic.svg'
import providerPaddleocrIcon from '@/assets/provider-paddleocr.svg'

const { pushToast } = useToast()

const props = defineProps({
  open: { type: Boolean, default: false },
  type: { type: String, default: 'openai' }, // 'openai' | 'anthropic' | 'paddleocr'
  editData: { type: Object, default: null }, // null=新增, object=编辑
})

const emit = defineEmits(['close', 'confirm'])

const isEdit = computed(() => !!props.editData)

const PROVIDER_TYPE_CONFIGS = {
  openai: {
    titleAdd: '添加 OpenAI 兼容供应�?,
    titleEdit: '编辑 OpenAI 兼容供应�?,
    iconCls: 'fa-bolt text-slate-600 dark:text-slate-400',
    imgIcon: providerOpenaiIcon,
    btnCls: 'bg-slate-900 hover:bg-slate-800 text-white dark:bg-[#f7f8f8] dark:hover:bg-white dark:text-[#1b1b1d]',
    namePlaceholder: '例如：DeepSeek / Qwen / Moonshot',
    urlPlaceholder: '留空使用 OpenAI 官方，或填入 https://api.deepseek.com �?,
    modelPlaceholder: 'gpt-4o-mini',
    defaultName: 'OpenAI Provider',
    secretLabel: 'API Key',
    secretPlaceholder: '输入 API Key',
    urlLabel: 'Base URL',
  },
  anthropic: {
    titleAdd: '添加 Anthropic 供应�?,
    titleEdit: '编辑 Anthropic 供应�?,
    iconCls: 'fa-brain text-slate-600 dark:text-slate-400',
    imgIcon: providerAnthropicIcon,
    btnCls: 'bg-slate-900 hover:bg-slate-800 text-white dark:bg-[#f7f8f8] dark:hover:bg-white dark:text-[#1b1b1d]',
    namePlaceholder: '例如：Claude Official',
    urlPlaceholder: '留空使用 Anthropic 官方',
    modelPlaceholder: 'claude-sonnet-4-20250514',
    defaultName: 'Anthropic Provider',
    secretLabel: 'API Key',
    secretPlaceholder: '输入 API Key',
    urlLabel: 'Base URL',
  },
  paddleocr: {
    titleAdd: '添加 PaddleOCR 服务',
    titleEdit: '编辑 PaddleOCR 服务',
    iconCls: 'fa-eye text-slate-600 dark:text-slate-400',
    imgIcon: providerPaddleocrIcon,
    btnCls: 'bg-slate-900 hover:bg-slate-800 text-white dark:bg-[#f7f8f8] dark:hover:bg-white dark:text-[#1b1b1d]',
    namePlaceholder: '例如：PaddleOCR 官方',
    urlPlaceholder: 'https://paddleocr.aistudio-app.com/api/v2/ocr/jobs',
    modelPlaceholder: 'PaddleOCR-VL-1.5',
    defaultName: 'PaddleOCR',
    secretLabel: 'API Token',
    secretPlaceholder: '输入 API Token',
    urlLabel: 'API URL',
  },
}

const SHARED_ICON_BG = 'bg-gray-50 dark:bg-white/[0.04] border border-gray-100 dark:border-white/[0.08]'
const SHARED_BTN_CLS = 'bg-slate-900 hover:bg-slate-800 text-white dark:bg-[#f7f8f8] dark:hover:bg-white dark:text-[#1b1b1d]'

const typeConfig = computed(() => ({
  ...PROVIDER_TYPE_CONFIGS[props.type],
  title: isEdit.value ? PROVIDER_TYPE_CONFIGS[props.type].titleEdit : PROVIDER_TYPE_CONFIGS[props.type].titleAdd,
  iconBg: SHARED_ICON_BG,
  btnCls: SHARED_BTN_CLS,
}))

const defaultForm = () => ({
  name: '',
  api_key: '',
  base_url: '',
  model_name: '',
  light_model_name: '',
  supports_function_calling: true,
  // PaddleOCR 专用
  use_doc_orientation: false,
  use_doc_unwarping: false,
  use_chart_recognition: false,
})

const form = ref(defaultForm())

// 模型列表相关
const modelList = ref([])
const fetchingModels = ref(false)
const fetchModelError = ref('')

const canFetchModels = computed(() => {
  if (props.type === 'paddleocr') return false
  // 需要有 API Key（新输入或已设置�?
  const hasKey = form.value.api_key || (props.editData?.api_key_set)
  return !!hasKey
})

const fetchModels = async () => {
  if (fetchingModels.value) return
  fetchingModels.value = true
  fetchModelError.value = ''
  modelList.value = []
  try {
    const res = await fetch('/api/models/list', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: props.type,
        api_key: form.value.api_key || undefined,
        base_url: form.value.base_url || undefined,
        provider_id: props.editData?.id || undefined,
      }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.error || `HTTP ${res.status}`)
    }
    const data = await res.json()
    const apiModels = data.models || []
    const modelSet = new Set(apiModels)
    // 将当前表单中的模型名也加入列表（兼容废弃模型�?deepseek-chat / deepseek-reasoner�?
    const currentModel = form.value.model_name || ''
    const currentLightModel = form.value.light_model_name || ''
    if (currentModel && !modelSet.has(currentModel)) { modelSet.add(currentModel); apiModels.push(currentModel) }
    if (currentLightModel && !modelSet.has(currentLightModel)) { modelSet.add(currentLightModel); apiModels.push(currentLightModel) }
    modelList.value = apiModels
    if (modelList.value.length === 0) {
      pushToast('error', '未获取到可用模型')
    } else {
      pushToast('success', `获取�?${modelList.value.length} 个可用模型`)
    }
  } catch (e) {
    pushToast('error', e.message || '获取模型列表失败')
  } finally {
    fetchingModels.value = false
  }
}

// 每次打开时重置或回填表单
watch(() => props.open, (v) => {
  if (!v) return
  modelList.value = []
  fetchModelError.value = ''
  openDropdown.value = null
  testResult.value = null
  if (props.editData) {
    form.value = {
      ...defaultForm(),
      name: props.editData.name || '',
      api_key: '',
      base_url: props.editData.base_url || '',
      model_name: props.editData.model_name || '',
      light_model_name: props.editData.light_model_name || '',
      supports_function_calling: props.editData.supports_function_calling ?? true,
      use_doc_orientation: props.editData.use_doc_orientation || false,
      use_doc_unwarping: props.editData.use_doc_unwarping || false,
      use_chart_recognition: props.editData.use_chart_recognition || false,
    }
  } else {
    form.value = defaultForm()
  }
})

// PaddleOCR 连接测试
const testingConnection = ref(false)
const testResult = ref(null) // { success: boolean, message: string } | null

const canTestConnection = computed(() => {
  const hasToken = form.value.api_key || (props.editData?.api_key_set)
  const hasUrl = form.value.base_url
  return !!hasToken && !!hasUrl
})

const testConnection = async () => {
  if (testingConnection.value) return
  testingConnection.value = true
  testResult.value = null
  try {
    const payload = {
      api_token: form.value.api_key || undefined,
      api_url: form.value.base_url || undefined,
      provider_id: props.editData?.id || undefined,
    }
    const res = await fetch('/api/paddleocr/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const data = await res.json()
    testResult.value = {
      success: data.success,
      message: data.success ? data.message : data.error,
    }
  } catch (e) {
    testResult.value = { success: false, message: e.message || '请求失败' }
  } finally {
    testingConnection.value = false
  }
}

const confirm = () => {
  if (!form.value.name.trim()) {
    form.value.name = typeConfig.value.defaultName
  }
  emit('confirm', { ...form.value })
}

// 自定义下�?
const openDropdown = ref(null) // 'model_name' | 'light_model_name' | null
const toggleDropdown = (field) => {
  openDropdown.value = openDropdown.value === field ? null : field
}
const selectOption = (field, value) => {
  form.value[field] = value
  openDropdown.value = null
}
</script>

<template>
  <BaseModal :open="open" :title="typeConfig.title" :iconBg="typeConfig.iconBg" maxWidth="max-w-lg sm:w-[32rem]"
    :blurBackdrop="false" @close="emit('close')">
    <template #icon>
      <img v-if="typeConfig.imgIcon" :src="typeConfig.imgIcon" class="h-5 w-5 object-contain"
        :class="{ 'dark:invert': type === 'openai' }" alt="icon" />
      <i v-else class="fa-solid text-base" :class="typeConfig.iconCls"></i>
    </template>

    <form autocomplete="off" class="space-y-4" @submit.prevent="confirm" @click="openDropdown = null">
      <div>
        <label class="mb-1.5 block text-xs font-bold text-slate-600 dark:text-slate-400">{{ type === 'paddleocr' ?
          '服务名称' :
          '供应商名�? }}</label>
        <BaseInput v-model="form.name" type="text" autocomplete="one-time-code"
          :placeholder="typeConfig.namePlaceholder" inputClass="h-10" autofocus />
      </div>

      <div>
        <label class="mb-1.5 block text-xs font-bold text-slate-600 dark:text-slate-400">{{ typeConfig.secretLabel
          }}</label>
        <BaseInput v-model="form.api_key" type="password" autocomplete="new-password"
          :placeholder="isEdit && editData?.api_key_set ? `已设�?(${editData.api_key_hint})，留空则不修改` : typeConfig.secretPlaceholder"
          inputClass="h-10" />
      </div>

      <div>
        <label class="mb-1.5 block text-xs font-bold text-slate-600 dark:text-slate-400">{{ typeConfig.urlLabel
          }}</label>
        <BaseInput v-model="form.base_url" type="text" autocomplete="one-time-code"
          :placeholder="typeConfig.urlPlaceholder" inputClass="h-10" />
      </div>

      <!-- 获取模型列表按钮（仅 OpenAI / Anthropic�?-->
      <div v-if="type !== 'paddleocr'" class="flex items-center gap-3">
        <BaseButton variant="secondary" @click="fetchModels" :disabled="!canFetchModels || fetchingModels"
          class="!h-8 !px-3 !text-[11px] !rounded-lg">
          <i class="fa-solid text-[10px]" :class="fetchingModels ? 'fa-circle-notch fa-spin' : 'fa-arrows-rotate'"></i>
          <span class="inline-block w-[4.5rem] text-center">{{ fetchingModels ? '获取�?..' : '获取模型列表' }}</span>
        </BaseButton>
        <span v-if="!canFetchModels" class="text-xs text-slate-400 dark:text-slate-500">请先填写 API Key</span>
      </div>

      <div class="grid gap-4" :class="type === 'openai' ? 'sm:grid-cols-2' : ''">
        <div>
          <label class="mb-1.5 flex items-center gap-1.5 text-xs font-bold text-slate-600 dark:text-slate-400">
            {{ type === 'paddleocr' ? 'OCR 模型' : '模型' }}
            <span v-if="type !== 'paddleocr'" class="group relative">
              <i
                class="fa-solid fa-circle-info cursor-help text-slate-400 transition-colors hover:text-blue-500 dark:text-slate-500"></i>
              <span
                class="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg border border-slate-200/60 bg-white/90 px-3 py-1.5 text-xs font-normal text-slate-600 opacity-0 shadow-lg transition-opacity group-hover:opacity-100 dark:border-white/10 dark:bg-[#0A0A0F]/90 dark:text-slate-300">
                用于题目分割、纠错等核心任务
              </span>
            </span>
          </label>
          <!-- 有模型列表时用自定义下拉 -->
          <div v-if="modelList.length > 0 && type !== 'paddleocr'" class="relative">
            <button type="button" @click.stop="toggleDropdown('model_name')"
              class="flex w-full items-center justify-between rounded-xl border border-slate-200/80 bg-white/70 px-4 py-2.5 text-left text-sm transition-colors dark:border-white/10 dark:bg-slate-800/60"
              :class="form.model_name ? 'text-slate-800 dark:text-slate-200' : 'text-slate-400 dark:text-slate-500'">
              <span class="truncate">{{ form.model_name || '请选择模型' }}</span>
              <i class="fa-solid fa-chevron-down ml-2 text-[10px] text-slate-400 transition-transform"
                :class="openDropdown === 'model_name' ? 'rotate-180' : ''"></i>
            </button>
            <Transition name="dropdown">
              <div v-if="openDropdown === 'model_name'"
                class="absolute z-50 mt-1.5 max-h-48 w-full overflow-y-auto rounded-xl border border-slate-200/60 bg-white py-1 shadow-xl dark:border-white/10 dark:bg-[#0A0A0F]">
                <button v-for="m in modelList" :key="m" type="button" @click.stop="selectOption('model_name', m)"
                  class="flex w-full items-center gap-2 px-4 py-2 text-left text-sm transition-colors hover:bg-gray-50 dark:hover:bg-white/5"
                  :class="form.model_name === m ? 'font-bold text-slate-900 dark:text-[#f7f8f8]' : 'text-slate-600 dark:text-slate-400'">
                  <i v-if="form.model_name === m"
                    class="fa-solid fa-check text-[10px] text-slate-900 dark:text-[#f7f8f8]"></i>
                  <span :class="form.model_name !== m ? 'pl-[18px]' : ''">{{ m }}</span>
                </button>
              </div>
            </Transition>
          </div>
          <!-- 无模型列表时�?input -->
          <BaseInput v-else v-model="form.model_name" type="text"
            :placeholder="type === 'paddleocr' ? 'e.g. PaddleOCR-VL-1.5' : 'e.g. gpt-4o, deepseek-chat'"
            inputClass="h-10" />
        </div>
        <div v-if="type === 'openai'">
          <label class="mb-1.5 flex items-center gap-1.5 text-xs font-bold text-slate-600 dark:text-slate-400">
            辅助模型
            <span class="font-normal text-slate-400">（可选）</span>
            <span class="group relative">
              <i
                class="fa-solid fa-circle-info cursor-help text-slate-400 transition-colors hover:text-blue-500 dark:text-slate-500"></i>
              <span
                class="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg border border-slate-200/60 bg-white/90 px-3 py-1.5 text-xs font-normal text-slate-600 opacity-0 shadow-lg transition-opacity group-hover:opacity-100 dark:border-white/10 dark:bg-[#0A0A0F]/90 dark:text-slate-300">
                用于科目识别等简单任务，更快更省 Token
              </span>
            </span>
          </label>
          <div v-if="modelList.length > 0" class="relative">
            <button type="button" @click.stop="toggleDropdown('light_model_name')"
              class="flex w-full items-center justify-between rounded-xl border border-slate-200/80 bg-white/70 px-4 py-2.5 text-left text-sm transition-colors dark:border-white/10 dark:bg-slate-800/60"
              :class="form.light_model_name ? 'text-slate-800 dark:text-slate-200' : 'text-slate-400 dark:text-slate-500'">
              <span class="truncate">{{ form.light_model_name || '不使�? }}</span>
              <i class="fa-solid fa-chevron-down ml-2 text-[10px] text-slate-400 transition-transform"
                :class="openDropdown === 'light_model_name' ? 'rotate-180' : ''"></i>
            </button>
            <Transition name="dropdown">
              <div v-if="openDropdown === 'light_model_name'"
                class="absolute z-50 mt-1.5 max-h-48 w-full overflow-y-auto rounded-xl border border-slate-200/60 bg-white py-1 shadow-xl dark:border-white/10 dark:bg-[#0A0A0F]">
                <button type="button" @click.stop="selectOption('light_model_name', '')"
                  class="flex w-full items-center gap-2 px-4 py-2 text-left text-sm transition-colors hover:bg-gray-50 dark:hover:bg-white/5"
                  :class="!form.light_model_name ? 'font-bold text-slate-900 dark:text-[#f7f8f8]' : 'text-slate-600 dark:text-slate-400'">
                  <i v-if="!form.light_model_name"
                    class="fa-solid fa-check text-[10px] text-slate-900 dark:text-[#f7f8f8]"></i>
                  <span :class="form.light_model_name ? 'pl-[18px]' : ''">不使�?/span>
                </button>
                <button v-for="m in modelList" :key="m" type="button" @click.stop="selectOption('light_model_name', m)"
                  class="flex w-full items-center gap-2 px-4 py-2 text-left text-sm transition-colors hover:bg-gray-50 dark:hover:bg-white/5"
                  :class="form.light_model_name === m ? 'font-bold text-slate-900 dark:text-[#f7f8f8]' : 'text-slate-600 dark:text-slate-400'">
                  <i v-if="form.light_model_name === m"
                    class="fa-solid fa-check text-[10px] text-slate-900 dark:text-[#f7f8f8]"></i>
                  <span :class="form.light_model_name !== m ? 'pl-[18px]' : ''">{{ m }}</span>
                </button>
              </div>
            </Transition>
          </div>
          <BaseInput v-else v-model="form.light_model_name" type="text" placeholder="科目识别等轻量任务使�? inputClass="h-10" />
        </div>
      </div>

      <!-- Function Calling 开关（�?OpenAI�?-->
      <div v-if="type === 'openai'" class="border-t border-slate-100 pt-4 dark:border-white/5">
        <label class="flex cursor-pointer items-center justify-between">
          <div>
            <span class="text-sm font-medium text-slate-700 dark:text-slate-300">支持 Function Calling</span>
            <p class="mt-0.5 text-xs text-slate-400 dark:text-slate-500">文心一言、通义千问等不支持时需关闭</p>
          </div>
          <button type="button" @click="form.supports_function_calling = !form.supports_function_calling"
            class="relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
            :class="form.supports_function_calling ? 'bg-slate-900 dark:bg-[#f7f8f8]' : 'bg-slate-200 dark:bg-white/10'">
            <span
              class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out dark:bg-[#0A0A0F]"
              :class="form.supports_function_calling ? 'translate-x-5' : 'translate-x-0'"></span>
          </button>
        </label>
      </div>

      <!-- PaddleOCR 测试连接 -->
      <div v-if="type === 'paddleocr'" class="flex items-center gap-3">
        <BaseButton variant="secondary" @click="testConnection" :disabled="!canTestConnection || testingConnection"
          class="!h-8 !px-3 !text-[11px] !rounded-lg">
          <i class="fa-solid text-[10px]"
            :class="testingConnection ? 'fa-circle-notch fa-spin' : 'fa-plug-circle-check'"></i>
          {{ testingConnection ? '检测中...' : '测试连接' }}
        </BaseButton>
        <span v-if="testResult?.success" class="text-xs font-medium text-emerald-600 dark:text-emerald-400">
          <i class="fa-solid fa-circle-check mr-1"></i>{{ testResult.message }}
        </span>
        <span v-else-if="testResult && !testResult.success"
          class="text-xs font-medium text-rose-500 dark:text-rose-400">
          <i class="fa-solid fa-circle-xmark mr-1"></i>{{ testResult.message }}
        </span>
        <span v-else-if="!canTestConnection" class="text-xs text-slate-400 dark:text-slate-500">请先填写 API Token �?
          URL</span>
      </div>

      <!-- PaddleOCR 功能开�?-->
      <div v-if="type === 'paddleocr'" class="border-t border-slate-100 pt-4 dark:border-white/5">
        <p class="mb-3 text-xs font-bold text-slate-600 dark:text-slate-400">功能开�?/p>
        <div class="space-y-3">
          <label v-for="toggle in [
            { key: 'use_doc_orientation', label: '文档方向检�? },
            { key: 'use_doc_unwarping', label: '文档去畸�? },
            { key: 'use_chart_recognition', label: '图表识别' },
          ]" :key="toggle.key" class="flex cursor-pointer items-center justify-between">
            <span class="text-sm font-medium text-slate-700 dark:text-slate-300">{{ toggle.label }}</span>
            <button type="button" @click="form[toggle.key] = !form[toggle.key]"
              class="relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
              :class="form[toggle.key] ? 'bg-slate-900 dark:bg-[#f7f8f8]' : 'bg-slate-200 dark:bg-white/10'">
              <span
                class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out dark:bg-[#0A0A0F]"
                :class="form[toggle.key] ? 'translate-x-5' : 'translate-x-0'"></span>
            </button>
          </label>
        </div>
      </div>
    </form>

    <template #footer>
      <BaseButton variant="secondary" @click="emit('close')" class="!h-9 !px-4 !text-[13px] !font-bold !rounded-lg">
        取消
      </BaseButton>
      <BaseButton variant="primary" @click="confirm" class="!h-9 !px-4 !text-[13px] !font-bold !rounded-lg">
        确认保存
      </BaseButton>
    </template>
  </BaseModal>
</template>

<style scoped>
.dropdown-enter-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-leave-active {
  transition: opacity 0.1s ease, transform 0.1s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
