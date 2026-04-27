import { ref, computed, watch } from 'vue'
import * as api from '@/api.js'

// ── 安全的 localStorage 访问 ─────────────────────────────
const safeLocalStorage = {
  getItem(key, fallback = '') {
    try {
      return localStorage.getItem(key) || fallback
    } catch {
      return fallback
    }
  },
  setItem(key, value) {
    try {
      localStorage.setItem(key, value)
    } catch (e) {
      console.warn(`[useSystemStatus] localStorage.setItem failed for "${key}":`, e)
    }
  },
}

// ── 模块级单例状态 ──────────────────────────────────────
const statusLoading = ref(true)
const systemStatus = ref(null)
const statusError = ref('')
const selectedModel = ref('')

const modelOptionsLoading = ref(false)
const modelOptionsData = ref(null)
const selectedLlmOptionId = ref(safeLocalStorage.getItem('selected_llm_option_id', ''))

const providerOptions = computed(() => {
  const s = systemStatus.value
  return s && s.available_models ? s.available_models : []
})

const hasConfiguredModel = computed(() => providerOptions.value.some(p => p.configured))

const selectedProvider = computed(() => {
  for (const p of providerOptions.value) {
    if (p.models && p.models.includes(selectedModel.value)) return p.value
  }
  const configured = providerOptions.value.find(p => p.configured)
  return configured ? configured.value : (providerOptions.value[0]?.value ?? 'openai')
})

watch(systemStatus, (newVal) => {
  if (newVal && newVal.available_models) {
    const configured = newVal.available_models.find(m => m.configured)
    if (configured) selectedModel.value = configured.default_model
  }
})

const statusPills = computed(() => {
  if (statusLoading.value) return [
    { key: 'paddle', loading: true, label: 'PaddleOCR' },
    { key: 'ensexam', loading: true, label: 'EnsExam' },
    { key: 'langsmith', loading: true, label: 'LangSmith' },
  ]
  const s = systemStatus.value
  if (!s) return []
  const pills = []
  pills.push({ key: 'paddle', ok: !!s.paddleocr_configured, label: s.paddleocr_configured ? 'PaddleOCR' : 'PaddleOCR未配置' })
  if (s.ensexam_configured) {
    pills.push({ key: 'ensexam', ok: true, label: 'EnsExam' })
  }
  pills.push(s.langsmith_enabled
    ? { key: 'langsmith', ok: true, label: 'LangSmith追踪' }
    : { key: 'langsmith', ok: false, label: 'LangSmith', isPlaceholder: true }
  )
  return pills
})

const doFetchStatus = async () => {
  statusLoading.value = true
  statusError.value = ''
  try {
    systemStatus.value = await api.fetchStatus()
  } catch (e) {
    statusError.value = e instanceof Error ? e.message : String(e)
  } finally {
    statusLoading.value = false
  }
}

const doFetchModelOptions = async () => {
  modelOptionsLoading.value = true
  try {
    const data = await api.fetchModelOptions()
    modelOptionsData.value = data

    // 如果没有选中项，或者选中项不在当前可用列表中，则使用默认选项
    const options = data.options || []
    const isValidSelection = selectedLlmOptionId.value && options.some(o => o.option_id === selectedLlmOptionId.value && o.available)
    if (!isValidSelection) {
      selectedLlmOptionId.value = data.default_option_id || (options[0]?.option_id || '')
      if (selectedLlmOptionId.value) {
        try {
          safeLocalStorage.setItem('selected_llm_option_id', selectedLlmOptionId.value)
        } catch (e) {
          console.warn('[useSystemStatus] 保存选中模型失败:', e)
        }
      }
    }

    // 确保 selectedModel 也被初始化同步
    if (selectedLlmOption.value) {
      selectedModel.value = selectedLlmOption.value.model_name
    }
  } catch (e) {
    console.error('获取模型选项失败', e)
  } finally {
    modelOptionsLoading.value = false
  }
}

watch(selectedLlmOptionId, (newId) => {
  if (newId) {
    try {
      safeLocalStorage.setItem('selected_llm_option_id', newId)
    } catch (e) {
      console.warn('[useSystemStatus] 保存选中模型失败:', e)
    }

    // 同步更新旧的 selectedModel 状态，以兼容设置页等旧逻辑
    if (selectedLlmOption.value) {
      selectedModel.value = selectedLlmOption.value.model_name
    }
  }
})

const selectedLlmOption = computed(() => {
  if (!modelOptionsData.value || !modelOptionsData.value.options) return null
  return modelOptionsData.value.options.find(o => o.option_id === selectedLlmOptionId.value) || null
})

/**
 * useSystemStatus — 系统状态单例 composable
 * 任何组件调用都返回同一份响应式状态
 */
export function useSystemStatus() {
  return {
    statusLoading, systemStatus, statusError, selectedModel,
    providerOptions, hasConfiguredModel, selectedProvider, statusPills,
    modelOptionsLoading, modelOptionsData, selectedLlmOptionId, selectedLlmOption,
    doFetchStatus, doFetchModelOptions,
  }
}
