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
  api_key: '',
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
  api_key: '',
  base_url: data.base_url || '',
  model_name: data.model_name || '',
  api_key_set: data.api_key_set || false,
  api_key_hint: data.api_key_hint || '',
})

const makePaddleOCRProvider = (data = {}) => ({
  id: data.id || crypto.randomUUID(),
  name: data.name || '',
  api_key: '',
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
    pushToast('success', '配置已保存并生效')
    emit('saved')
    await loadConfig()
  } catch (e) {
    pushToast('error', '保存失败: ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    saving.value = false
  }
}

const removeOpenAIProvider = (idx) => {
  if (openaiProviders.value[idx]?.id === activeOpenaiId.value) activeOpenaiId.value = null
  openaiProviders.value.splice(idx, 1)
}

const removeAnthropicProvider = (idx) => {
  if (anthropicProviders.value[idx]?.id === activeAnthropicId.value) activeAnthropicId.value = null
  anthropicProviders.value.splice(idx, 1)
}

const removePaddleOCRProvider = (idx) => {
  if (paddleocrProviders.value[idx]?.id === activePaddleocrId.value) activePaddleocrId.value = null
  paddleocrProviders.value.splice(idx, 1)
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

const onDialogConfirm = (formData) => {
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
      const p = makePaddleOCRProvider({ name: formData.name, api_url: formData.base_url, model: formData.model_name, use_doc_orientation: formData.use_doc_orientation, use_doc_unwarping: formData.use_doc_unwarping, use_chart_recognition: formData.use_chart_recognition })
      paddleocrProviders.value.push(p)
      if (paddleocrProviders.value.length === 1) activePaddleocrId.value = p.id
    }
  }
  dialogOpen.value = false
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
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 dark:bg-emerald-500/10">
                <i class="fa-solid fa-bolt text-lg text-emerald-600 dark:text-emerald-400"></i>
              </div>
              <div>
                <h3 class="text-base font-bold text-slate-800 dark:text-slate-200">OpenAI 兼容 API</h3>
                <p class="text-xs text-slate-500 dark:text-slate-400">支持 OpenAI / DeepSeek / Qwen / Moonshot 等</p>
              </div>
            </div>
            <button
              @click="openAddDialog('openai')"
              class="inline-flex items-center gap-1.5 rounded-xl border border-dashed border-slate-300 px-3 py-1.5 text-xs font-bold text-slate-500 transition-all hover:border-emerald-400 hover:bg-emerald-50 hover:text-emerald-600 dark:border-white/10 dark:text-slate-400 dark:hover:border-emerald-500/40 dark:hover:bg-emerald-500/10 dark:hover:text-emerald-400"
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
              class="flex items-center gap-3 rounded-2xl border border-slate-200/60 bg-white/70 px-5 py-3.5 shadow-sm backdrop-blur-xl transition-all dark:border-white/10 dark:bg-white/[0.03]"
            >
              <!-- 激活单选 -->
              <button
                @click="toggleActive('openai', provider.id)"
                class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-all"
                :class="activeOpenaiId === provider.id
                  ? 'border-emerald-500 bg-emerald-500 dark:border-emerald-400 dark:bg-emerald-400'
                  : 'border-slate-300 hover:border-emerald-400 dark:border-slate-600 dark:hover:border-emerald-500'"
                :title="activeOpenaiId === provider.id ? '当前已启用' : '点击启用'"
              >
                <i v-if="activeOpenaiId === provider.id" class="fa-solid fa-check text-[9px] text-white"></i>
              </button>

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
                @click="openEditDialog('openai', provider, idx)"
                class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-slate-300"
                title="设置"
              >
                <i class="fa-solid fa-gear text-xs"></i>
              </button>
              <button
                @click="removeOpenAIProvider(idx)"
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
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-50 dark:bg-orange-500/10">
                <i class="fa-solid fa-brain text-lg text-orange-600 dark:text-orange-400"></i>
              </div>
              <div>
                <h3 class="text-base font-bold text-slate-800 dark:text-slate-200">Anthropic API</h3>
                <p class="text-xs text-slate-500 dark:text-slate-400">Claude 系列模型</p>
              </div>
            </div>
            <button
              @click="openAddDialog('anthropic')"
              class="inline-flex items-center gap-1.5 rounded-xl border border-dashed border-slate-300 px-3 py-1.5 text-xs font-bold text-slate-500 transition-all hover:border-orange-400 hover:bg-orange-50 hover:text-orange-600 dark:border-white/10 dark:text-slate-400 dark:hover:border-orange-500/40 dark:hover:bg-orange-500/10 dark:hover:text-orange-400"
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
              class="flex items-center gap-3 rounded-2xl border border-slate-200/60 bg-white/70 px-5 py-3.5 shadow-sm backdrop-blur-xl transition-all dark:border-white/10 dark:bg-white/[0.03]"
            >
              <button
                @click="toggleActive('anthropic', provider.id)"
                class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-all"
                :class="activeAnthropicId === provider.id
                  ? 'border-orange-500 bg-orange-500 dark:border-orange-400 dark:bg-orange-400'
                  : 'border-slate-300 hover:border-orange-400 dark:border-slate-600 dark:hover:border-orange-500'"
                :title="activeAnthropicId === provider.id ? '当前已启用' : '点击启用'"
              >
                <i v-if="activeAnthropicId === provider.id" class="fa-solid fa-check text-[9px] text-white"></i>
              </button>

              <div class="flex min-w-0 flex-1 items-center gap-2">
                <span class="truncate text-sm font-bold text-slate-800 dark:text-slate-200">{{ provider.name || '未命名' }}</span>
                <span v-if="activeAnthropicId === provider.id" class="shrink-0 rounded-full bg-orange-100 px-2 py-0.5 text-[10px] font-bold text-orange-600 dark:bg-orange-500/15 dark:text-orange-400">
                  使用中
                </span>
                <span v-else-if="provider.api_key_set" class="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-500 dark:bg-white/5 dark:text-slate-400">
                  已配置
                </span>
              </div>

              <button
                @click="openEditDialog('anthropic', provider, idx)"
                class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-slate-300"
                title="设置"
              >
                <i class="fa-solid fa-gear text-xs"></i>
              </button>
              <button
                @click="removeAnthropicProvider(idx)"
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
              class="flex items-center gap-3 rounded-2xl border border-slate-200/60 bg-white/70 px-5 py-3.5 shadow-sm backdrop-blur-xl transition-all dark:border-white/10 dark:bg-white/[0.03]"
            >
              <button
                @click="toggleActive('paddleocr', provider.id)"
                class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-all"
                :class="activePaddleocrId === provider.id
                  ? 'border-blue-500 bg-blue-500 dark:border-blue-400 dark:bg-blue-400'
                  : 'border-slate-300 hover:border-blue-400 dark:border-slate-600 dark:hover:border-blue-500'"
                :title="activePaddleocrId === provider.id ? '当前已启用' : '点击启用'"
              >
                <i v-if="activePaddleocrId === provider.id" class="fa-solid fa-check text-[9px] text-white"></i>
              </button>

              <div class="flex min-w-0 flex-1 items-center gap-2">
                <span class="truncate text-sm font-bold text-slate-800 dark:text-slate-200">{{ provider.name || '未命名' }}</span>
                <span v-if="activePaddleocrId === provider.id" class="shrink-0 rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-600 dark:bg-blue-500/15 dark:text-blue-400">
                  使用中
                </span>
                <span v-else-if="provider.api_key_set" class="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-500 dark:bg-white/5 dark:text-slate-400">
                  已配置
                </span>
              </div>

              <button
                @click="openEditDialog('paddleocr', provider, idx)"
                class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-slate-300"
                title="设置"
              >
                <i class="fa-solid fa-gear text-xs"></i>
              </button>
              <button
                @click="removePaddleOCRProvider(idx)"
                class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-rose-50 hover:text-rose-500 dark:hover:bg-rose-500/10"
                title="删除"
              >
                <i class="fa-solid fa-trash-can text-xs"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- 操作栏 -->
        <div class="flex items-center justify-end gap-3 pb-8">
          <button
            @click="loadConfig"
            :disabled="saving"
            class="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200/60 bg-white/60 px-5 py-2.5 text-sm font-bold text-slate-700 transition-all hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/10 dark:bg-slate-800/60 dark:text-slate-300 dark:hover:bg-slate-700"
          >
            <i class="fa-solid fa-rotate-right"></i>
            重置
          </button>
          <button
            @click="saveConfig"
            :disabled="saving"
            class="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-2.5 text-sm font-bold text-white shadow-md transition-all hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-indigo-500 dark:hover:bg-indigo-600"
          >
            <i class="fa-solid" :class="saving ? 'fa-circle-notch fa-spin' : 'fa-check'"></i>
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
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
