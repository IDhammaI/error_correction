import { ref, computed, watch } from 'vue'
import * as api from '@/api.js'

// ── 模块级单例状态 ──────────────────────────────────────
const statusLoading = ref(true)
const systemStatus = ref(null)
const statusError = ref('')
const selectedModel = ref('')

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

/**
 * useSystemStatus — 系统状态单例 composable
 * 任何组件调用都返回同一份响应式状态
 */
export function useSystemStatus() {
  return {
    statusLoading, systemStatus, statusError, selectedModel,
    providerOptions, hasConfiguredModel, selectedProvider, statusPills,
    doFetchStatus,
  }
}
