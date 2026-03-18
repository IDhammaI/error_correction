<script setup>
import { ref, inject, onMounted, watch } from 'vue'
import { fetchAppConfig, updateAppConfig } from '../api.js'
import ProviderDialog from './ProviderDialog.vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
})

const emit = defineEmits(['saved'])

const pushToast = inject('pushToast', (type, msg) => { console.warn(`[${type}] ${msg}`) })

const loading = ref(true)
const saving = ref(false)

// ---------- 多 Provider 数据结构 ----------

const makeOpenAIProvider = (data = {}) => ({
  id: data.id || crypto.randomUUID(),
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
  id: data.id || crypto.randomUUID(),
  name: data.name || '',
  api_key: data.api_key || '',
  base_url: data.base_url || '',
  model_name: data.model_name || '',
  api_key_set: data.api_key_set || false,
  api_key_hint: data.api_key_hint || '',
})

const makePaddleOCRProvider = (data = {}) => ({
  id: data.id || crypto.randomUUID(),
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
    // nextTick 后再启用自动保存，避免赋值触发 watcher
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
    emit('saved')
  } catch (e) {
    pushToast('error', '保存失败: ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    saving.value = false
  }
}

// ---------- 自动保存（防抖） ----------
let autoSaveTimer = null
const configLoaded = ref(false)  // 防止 loadConfig 触发自动保存

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
const dialogEditData = ref(null)  // null=新增, object=编辑
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
    // 编辑模式：更新已有 provider
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
    // 新增模式
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

  // 立即保存并提示
  clearTimeout(autoSaveTimer)
  try {
    await saveConfig()
    pushToast('success', isEdit ? '配置已更新' : '供应商已添加')
  } catch { /* saveConfig 内部已 toast error */ }
}

onMounted(() => { if (props.visible) loadConfig() })
watch(() => props.visible, (v) => { if (v) loadConfig() })
</script>

<template>
  <div class="relative h-full overflow-y-auto">
    <div class="container relative z-10 mx-auto max-w-3xl px-4 py-8 sm:px-8">
      <!-- 页面标题 -->
      <div class="mb-8 pl-2 sm:pl-0">
        <h2 class="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl dark:text-white">
          系统设置
        </h2>
        <p class="mt-2 text-sm font-medium text-slate-500 dark:text-slate-400">配置 AI 模型供应商和 OCR 服务连接参数，修改即时生效。</p>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <i class="fa-solid fa-circle-notch fa-spin mr-3 text-2xl text-blue-500"></i>
        <span class="text-sm font-semibold text-slate-500 dark:text-slate-400">加载配置中...</span>
      </div>

      <div v-else class="space-y-6">

        <!-- ====== OpenAI 兼容 API ====== -->
        <div>
          <div class="mb-3 flex items-center justify-between pl-1">
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 dark:bg-blue-500/10">
                <i class="fa-solid fa-bolt text-lg text-blue-600 dark:text-blue-400"></i>
              </div>
              <div>
                <h3 class="text-base font-bold text-slate-800 dark:text-slate-200">OpenAI 兼容 API</h3>
                <p class="text-xs text-slate-500 dark:text-slate-400">支持 OpenAI / DeepSeek / Qwen / Moonshot 等</p>
              </div>
            </div>
            <button
              @click="openAddDialog('openai')"
              class="inline-flex items-center gap-1.5 rounded-xl border border-dashed border-slate-300 px-3 py-1.5 text-xs font-bold text-slate-500 transition-all hover:border-blue-400 hover:bg-blue-50 hover:text-blue-600 dark:border-white/10 dark:text-slate-400 dark:hover:border-blue-500/40 dark:hover:bg-blue-500/10 dark:hover:text-blue-400"
            >
              <i class="fa-solid fa-plus text-[10px]"></i>
              添加
            </button>
          </div>

          <div v-if="openaiProviders.length === 0" class="rounded-2xl border border-dashed border-slate-200/60 py-10 text-center dark:border-white/10">
            <i class="fa-solid fa-plug text-3xl text-slate-300 dark:text-slate-600"></i>
            <p class="mt-3 text-sm font-medium text-slate-400 dark:text-slate-500">尚未配置，点击上方"添加"按钮</p>
          </div>

          <div class="space-y-2">
            <div
              v-for="(provider, idx) in openaiProviders" :key="provider.id"
              class="flex cursor-pointer items-center gap-3 rounded-2xl border border-slate-200/60 bg-white/70 px-5 py-3.5 shadow-sm backdrop-blur-xl transition-all hover:border-blue-300 dark:border-white/10 dark:bg-white/[0.03] dark:hover:border-blue-500/30"
              @click="toggleActive('openai', provider.id)"
            >
              <!-- 激活单选 -->
              <div
                class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-all"
                :class="activeOpenaiId === provider.id
                  ? 'border-emerald-500 bg-emerald-500 dark:border-emerald-400 dark:bg-emerald-400'
                  : 'border-slate-300 dark:border-slate-600'"
              >
                <i v-if="activeOpenaiId === provider.id" class="fa-solid fa-check text-[9px] text-white"></i>
              </div>

              <!-- 名称 + 状态 -->
              <div class="flex min-w-0 flex-1 items-center gap-2">
                <span class="truncate text-sm font-bold text-slate-800 dark:text-slate-200">{{ provider.name || '未命名' }}</span>
                <span v-if="activeOpenaiId === provider.id" class="shrink-0 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400">
                  使用中
                </span>
                <span v-else-if="provider.api_key_set" class="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-500 dark:bg-white/5 dark:text-slate-400">
                  已配置
                </span>
              </div>

              <!-- 设置 + 删除 -->
              <button
                @click.stop="openEditDialog('openai', provider, idx)"
                class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-slate-300"
                title="设置"
              >
                <i class="fa-solid fa-gear text-xs"></i>
              </button>
              <button
                @click.stop="removeProvider('openai', idx)"
                class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-rose-50 hover:text-rose-500 dark:hover:bg-rose-500/10"
                title="删除"
              >
                <i class="fa-solid fa-trash-can text-xs"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- ====== Anthropic API ====== -->
        <div>
          <div class="mb-3 flex items-center justify-between pl-1">
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 dark:bg-blue-500/10">
                <i class="fa-solid fa-brain text-lg text-blue-600 dark:text-blue-400"></i>
              </div>
              <div>
                <h3 class="text-base font-bold text-slate-800 dark:text-slate-200">Anthropic API</h3>
                <p class="text-xs text-slate-500 dark:text-slate-400">Claude 系列模型</p>
              </div>
            </div>
            <button
              @click="openAddDialog('anthropic')"
              class="inline-flex items-center gap-1.5 rounded-xl border border-dashed border-slate-300 px-3 py-1.5 text-xs font-bold text-slate-500 transition-all hover:border-blue-400 hover:bg-blue-50 hover:text-blue-600 dark:border-white/10 dark:text-slate-400 dark:hover:border-blue-500/40 dark:hover:bg-blue-500/10 dark:hover:text-blue-400"
            >
              <i class="fa-solid fa-plus text-[10px]"></i>
              添加
            </button>
          </div>

          <div v-if="anthropicProviders.length === 0" class="rounded-2xl border border-dashed border-slate-200/60 py-10 text-center dark:border-white/10">
            <i class="fa-solid fa-plug text-3xl text-slate-300 dark:text-slate-600"></i>
            <p class="mt-3 text-sm font-medium text-slate-400 dark:text-slate-500">尚未配置，点击上方"添加"按钮</p>
          </div>

          <div class="space-y-2">
            <div
              v-for="(provider, idx) in anthropicProviders" :key="provider.id"
              class="flex cursor-pointer items-center gap-3 rounded-2xl border border-slate-200/60 bg-white/70 px-5 py-3.5 shadow-sm backdrop-blur-xl transition-all hover:border-blue-300 dark:border-white/10 dark:bg-white/[0.03] dark:hover:border-blue-500/30"
              @click="toggleActive('anthropic', provider.id)"
            >
              <div
                class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-all"
                :class="activeAnthropicId === provider.id
                  ? 'border-emerald-500 bg-emerald-500 dark:border-emerald-400 dark:bg-emerald-400'
                  : 'border-slate-300 dark:border-slate-600'"
              >
                <i v-if="activeAnthropicId === provider.id" class="fa-solid fa-check text-[9px] text-white"></i>
              </div>

              <div class="flex min-w-0 flex-1 items-center gap-2">
                <span class="truncate text-sm font-bold text-slate-800 dark:text-slate-200">{{ provider.name || '未命名' }}</span>
                <span v-if="activeAnthropicId === provider.id" class="shrink-0 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400">
                  使用中
                </span>
                <span v-else-if="provider.api_key_set" class="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-500 dark:bg-white/5 dark:text-slate-400">
                  已配置
                </span>
              </div>

              <button
                @click.stop="openEditDialog('anthropic', provider, idx)"
                class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-slate-300"
                title="设置"
              >
                <i class="fa-solid fa-gear text-xs"></i>
              </button>
              <button
                @click.stop="removeProvider('anthropic', idx)"
                class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-rose-50 hover:text-rose-500 dark:hover:bg-rose-500/10"
                title="删除"
              >
                <i class="fa-solid fa-trash-can text-xs"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- ====== PaddleOCR ====== -->
        <div>
          <div class="mb-3 flex items-center justify-between pl-1">
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 dark:bg-blue-500/10">
                <i class="fa-solid fa-eye text-lg text-blue-600 dark:text-blue-400"></i>
              </div>
              <div>
                <h3 class="text-base font-bold text-slate-800 dark:text-slate-200">PaddleOCR</h3>
                <p class="text-xs text-slate-500 dark:text-slate-400">文档 OCR 识别服务</p>
              </div>
            </div>
            <button
              @click="openAddDialog('paddleocr')"
              class="inline-flex items-center gap-1.5 rounded-xl border border-dashed border-slate-300 px-3 py-1.5 text-xs font-bold text-slate-500 transition-all hover:border-blue-400 hover:bg-blue-50 hover:text-blue-600 dark:border-white/10 dark:text-slate-400 dark:hover:border-blue-500/40 dark:hover:bg-blue-500/10 dark:hover:text-blue-400"
            >
              <i class="fa-solid fa-plus text-[10px]"></i>
              添加
            </button>
          </div>

          <div v-if="paddleocrProviders.length === 0" class="rounded-2xl border border-dashed border-slate-200/60 py-10 text-center dark:border-white/10">
            <i class="fa-solid fa-plug text-3xl text-slate-300 dark:text-slate-600"></i>
            <p class="mt-3 text-sm font-medium text-slate-400 dark:text-slate-500">尚未配置，点击上方"添加"按钮</p>
          </div>

          <div class="space-y-2">
            <div
              v-for="(provider, idx) in paddleocrProviders" :key="provider.id"
              class="flex cursor-pointer items-center gap-3 rounded-2xl border border-slate-200/60 bg-white/70 px-5 py-3.5 shadow-sm backdrop-blur-xl transition-all hover:border-blue-300 dark:border-white/10 dark:bg-white/[0.03] dark:hover:border-blue-500/30"
              @click="toggleActive('paddleocr', provider.id)"
            >
              <div
                class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-all"
                :class="activePaddleocrId === provider.id
                  ? 'border-emerald-500 bg-emerald-500 dark:border-emerald-400 dark:bg-emerald-400'
                  : 'border-slate-300 dark:border-slate-600'"
              >
                <i v-if="activePaddleocrId === provider.id" class="fa-solid fa-check text-[9px] text-white"></i>
              </div>

              <div class="flex min-w-0 flex-1 items-center gap-2">
                <span class="truncate text-sm font-bold text-slate-800 dark:text-slate-200">{{ provider.name || '未命名' }}</span>
                <span v-if="activePaddleocrId === provider.id" class="shrink-0 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400">
                  使用中
                </span>
                <span v-else-if="provider.api_key_set" class="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-500 dark:bg-white/5 dark:text-slate-400">
                  已配置
                </span>
              </div>

              <button
                @click.stop="openEditDialog('paddleocr', provider, idx)"
                class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-slate-300"
                title="设置"
              >
                <i class="fa-solid fa-gear text-xs"></i>
              </button>
              <button
                @click.stop="removeProvider('paddleocr', idx)"
                class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-rose-50 hover:text-rose-500 dark:hover:bg-rose-500/10"
                title="删除"
              >
                <i class="fa-solid fa-trash-can text-xs"></i>
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- 添加/编辑供应商弹窗 -->
    <ProviderDialog
      :open="dialogOpen"
      :type="dialogType"
      :edit-data="dialogEditData"
      @close="dialogOpen = false"
      @confirm="onDialogConfirm"
    />
  </div>
</template>
