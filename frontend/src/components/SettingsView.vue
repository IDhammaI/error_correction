<script setup>
import { ref, inject, onMounted, watch } from 'vue'
import { fetchAppConfig, updateAppConfig } from '../api.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
})

const emit = defineEmits(['saved'])

const pushToast = inject('pushToast', (type, msg) => { console.warn(`[${type}] ${msg}`) })

const loading = ref(true)
const saving = ref(false)

// 表单数据
const form = ref({
  openai: { api_key: '', base_url: '', model_name: '', light_model_name: '', supports_function_calling: true },
  anthropic: { api_key: '', base_url: '', model_name: '' },
  paddleocr: { api_url: '', api_token: '', model: '', use_doc_orientation: false, use_doc_unwarping: false, use_chart_recognition: false },
})

// 用于显示占位提示
const hints = ref({
  openai: { api_key_set: false, api_key_hint: '' },
  anthropic: { api_key_set: false, api_key_hint: '' },
  paddleocr: { api_token_set: false, api_token_hint: '' },
})

const loadConfig = async () => {
  loading.value = true
  try {
    const cfg = await fetchAppConfig()
    // 填充表单（密钥字段留空，用户不修改则不提交）
    form.value.openai.base_url = cfg.openai?.base_url || ''
    form.value.openai.model_name = cfg.openai?.model_name || ''
    form.value.openai.light_model_name = cfg.openai?.light_model_name || ''
    form.value.openai.supports_function_calling = cfg.openai?.supports_function_calling ?? true
    form.value.openai.api_key = ''

    form.value.anthropic.base_url = cfg.anthropic?.base_url || ''
    form.value.anthropic.model_name = cfg.anthropic?.model_name || ''
    form.value.anthropic.api_key = ''

    form.value.paddleocr.api_url = cfg.paddleocr?.api_url || ''
    form.value.paddleocr.model = cfg.paddleocr?.model || ''
    form.value.paddleocr.api_token = ''
    form.value.paddleocr.use_doc_orientation = cfg.paddleocr?.use_doc_orientation || false
    form.value.paddleocr.use_doc_unwarping = cfg.paddleocr?.use_doc_unwarping || false
    form.value.paddleocr.use_chart_recognition = cfg.paddleocr?.use_chart_recognition || false

    hints.value.openai = { api_key_set: cfg.openai?.api_key_set, api_key_hint: cfg.openai?.api_key_hint || '' }
    hints.value.anthropic = { api_key_set: cfg.anthropic?.api_key_set, api_key_hint: cfg.anthropic?.api_key_hint || '' }
    hints.value.paddleocr = { api_token_set: cfg.paddleocr?.api_token_set, api_token_hint: cfg.paddleocr?.api_token_hint || '' }
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

    // OpenAI
    const oa = {}
    if (form.value.openai.api_key) oa.api_key = form.value.openai.api_key
    oa.base_url = form.value.openai.base_url
    oa.model_name = form.value.openai.model_name
    oa.light_model_name = form.value.openai.light_model_name
    oa.supports_function_calling = form.value.openai.supports_function_calling
    payload.openai = oa

    // Anthropic
    const an = {}
    if (form.value.anthropic.api_key) an.api_key = form.value.anthropic.api_key
    an.base_url = form.value.anthropic.base_url
    an.model_name = form.value.anthropic.model_name
    payload.anthropic = an

    // PaddleOCR
    const po = {}
    if (form.value.paddleocr.api_token) po.api_token = form.value.paddleocr.api_token
    po.api_url = form.value.paddleocr.api_url
    po.model = form.value.paddleocr.model
    po.use_doc_orientation = form.value.paddleocr.use_doc_orientation
    po.use_doc_unwarping = form.value.paddleocr.use_doc_unwarping
    po.use_chart_recognition = form.value.paddleocr.use_chart_recognition
    payload.paddleocr = po

    await updateAppConfig(payload)
    pushToast('success', '配置已保存并生效')
    emit('saved')
    // 重新加载以更新 hints
    await loadConfig()
  } catch (e) {
    pushToast('error', '保存失败: ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    saving.value = false
  }
}

onMounted(() => { if (props.visible) loadConfig() })
watch(() => props.visible, (v) => { if (v) loadConfig() })
</script>

<template>
  <div class="relative min-h-full">
    <!-- 背景光晕 -->
    <div class="pointer-events-none absolute inset-0 z-0 overflow-hidden">
      <div class="absolute -top-[10%] right-[-10%] h-[40vw] w-[40vw] rounded-full bg-violet-300/10 mix-blend-multiply blur-[100px] transition-colors duration-1000 dark:bg-violet-600/10 dark:mix-blend-screen"></div>
      <div class="absolute -bottom-[10%] left-[-10%] h-[30vw] w-[30vw] rounded-full bg-blue-200/20 mix-blend-multiply blur-[80px] transition-colors duration-1000 dark:bg-blue-600/10 dark:mix-blend-screen"></div>
    </div>

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
        <div class="rounded-2xl border border-slate-200/60 bg-white/70 p-6 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-[#0A0A0F]/60">
          <div class="mb-5 flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 dark:bg-emerald-500/10">
              <i class="fa-solid fa-bolt text-lg text-emerald-600 dark:text-emerald-400"></i>
            </div>
            <div>
              <h3 class="text-base font-bold text-slate-800 dark:text-slate-200">OpenAI 兼容 API</h3>
              <p class="text-xs text-slate-500 dark:text-slate-400">支持 OpenAI / DeepSeek / Qwen / Moonshot 等，通过 Base URL 切换</p>
            </div>
          </div>
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="sm:col-span-2">
              <label class="mb-1.5 block text-xs font-bold text-slate-600 dark:text-slate-400">API Key</label>
              <input
                v-model="form.openai.api_key"
                type="password"
                :placeholder="hints.openai.api_key_set ? `已设置 (${hints.openai.api_key_hint})` : '输入 API Key'"
                class="w-full rounded-xl border border-slate-200/80 bg-white px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 transition-colors focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-white/10 dark:bg-slate-800/80 dark:text-slate-200 dark:placeholder-slate-500"
              />
            </div>
            <div class="sm:col-span-2">
              <label class="mb-1.5 block text-xs font-bold text-slate-600 dark:text-slate-400">Base URL</label>
              <input
                v-model="form.openai.base_url"
                type="text"
                placeholder="留空使用 OpenAI 官方，或填入 https://api.deepseek.com 等"
                class="w-full rounded-xl border border-slate-200/80 bg-white px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 transition-colors focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-white/10 dark:bg-slate-800/80 dark:text-slate-200 dark:placeholder-slate-500"
              />
            </div>
            <div>
              <label class="mb-1.5 block text-xs font-bold text-slate-600 dark:text-slate-400">默认模型</label>
              <input
                v-model="form.openai.model_name"
                type="text"
                placeholder="gpt-4o-mini"
                class="w-full rounded-xl border border-slate-200/80 bg-white px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 transition-colors focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-white/10 dark:bg-slate-800/80 dark:text-slate-200 dark:placeholder-slate-500"
              />
            </div>
            <div>
              <label class="mb-1.5 block text-xs font-bold text-slate-600 dark:text-slate-400">轻量模型 <span class="font-normal text-slate-400">（可选）</span></label>
              <input
                v-model="form.openai.light_model_name"
                type="text"
                placeholder="科目识别等轻量任务使用"
                class="w-full rounded-xl border border-slate-200/80 bg-white px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 transition-colors focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-white/10 dark:bg-slate-800/80 dark:text-slate-200 dark:placeholder-slate-500"
              />
            </div>
          </div>
          <!-- 能力开关 -->
          <div class="mt-5 border-t border-slate-100 pt-5 dark:border-white/5">
            <p class="mb-3 text-xs font-bold text-slate-600 dark:text-slate-400">能力开关</p>
            <div class="space-y-3">
              <label
                v-for="toggle in [
                  { key: 'supports_function_calling', label: '支持 Function Calling', description: '文心一言、通义千问等不支持时需关闭，否则会陷入无限循环' },
                ]"
                :key="toggle.key"
                class="flex cursor-pointer items-center justify-between"
              >
                <div>
                  <span class="text-sm font-medium text-slate-700 dark:text-slate-300">{{ toggle.label }}</span>
                  <p v-if="toggle.description" class="mt-0.5 text-xs text-slate-400 dark:text-slate-500">{{ toggle.description }}</p>
                </div>
                <button
                  type="button"
                  @click="form.openai[toggle.key] = !form.openai[toggle.key]"
                  class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  :class="form.openai[toggle.key] ? 'bg-blue-600 dark:bg-indigo-500' : 'bg-slate-200 dark:bg-slate-700'"
                >
                  <span
                    class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out"
                    :class="form.openai[toggle.key] ? 'translate-x-5' : 'translate-x-0'"
                  ></span>
                </button>
              </label>
            </div>
          </div>
        </div>

        <!-- ====== Anthropic API ====== -->
        <div class="rounded-2xl border border-slate-200/60 bg-white/70 p-6 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-[#0A0A0F]/60">
          <div class="mb-5 flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-50 dark:bg-orange-500/10">
              <i class="fa-solid fa-brain text-lg text-orange-600 dark:text-orange-400"></i>
            </div>
            <div>
              <h3 class="text-base font-bold text-slate-800 dark:text-slate-200">Anthropic API</h3>
              <p class="text-xs text-slate-500 dark:text-slate-400">Claude 系列模型</p>
            </div>
          </div>
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="sm:col-span-2">
              <label class="mb-1.5 block text-xs font-bold text-slate-600 dark:text-slate-400">API Key</label>
              <input
                v-model="form.anthropic.api_key"
                type="password"
                :placeholder="hints.anthropic.api_key_set ? `已设置 (${hints.anthropic.api_key_hint})` : '输入 API Key'"
                class="w-full rounded-xl border border-slate-200/80 bg-white px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 transition-colors focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-white/10 dark:bg-slate-800/80 dark:text-slate-200 dark:placeholder-slate-500"
              />
            </div>
            <div class="sm:col-span-2">
              <label class="mb-1.5 block text-xs font-bold text-slate-600 dark:text-slate-400">Base URL</label>
              <input
                v-model="form.anthropic.base_url"
                type="text"
                placeholder="留空使用 Anthropic 官方"
                class="w-full rounded-xl border border-slate-200/80 bg-white px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 transition-colors focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-white/10 dark:bg-slate-800/80 dark:text-slate-200 dark:placeholder-slate-500"
              />
            </div>
            <div>
              <label class="mb-1.5 block text-xs font-bold text-slate-600 dark:text-slate-400">默认模型</label>
              <input
                v-model="form.anthropic.model_name"
                type="text"
                placeholder="claude-sonnet-4-20250514"
                class="w-full rounded-xl border border-slate-200/80 bg-white px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 transition-colors focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-white/10 dark:bg-slate-800/80 dark:text-slate-200 dark:placeholder-slate-500"
              />
            </div>
          </div>
        </div>

        <!-- ====== PaddleOCR ====== -->
        <div class="rounded-2xl border border-slate-200/60 bg-white/70 p-6 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-[#0A0A0F]/60">
          <div class="mb-5 flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 dark:bg-blue-500/10">
              <i class="fa-solid fa-eye text-lg text-blue-600 dark:text-blue-400"></i>
            </div>
            <div>
              <h3 class="text-base font-bold text-slate-800 dark:text-slate-200">PaddleOCR</h3>
              <p class="text-xs text-slate-500 dark:text-slate-400">文档 OCR 识别服务</p>
            </div>
          </div>
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="sm:col-span-2">
              <label class="mb-1.5 block text-xs font-bold text-slate-600 dark:text-slate-400">API URL</label>
              <input
                v-model="form.paddleocr.api_url"
                type="text"
                placeholder="https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
                class="w-full rounded-xl border border-slate-200/80 bg-white px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 transition-colors focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-white/10 dark:bg-slate-800/80 dark:text-slate-200 dark:placeholder-slate-500"
              />
            </div>
            <div class="sm:col-span-2">
              <label class="mb-1.5 block text-xs font-bold text-slate-600 dark:text-slate-400">API Token</label>
              <input
                v-model="form.paddleocr.api_token"
                type="password"
                :placeholder="hints.paddleocr.api_token_set ? `已设置 (${hints.paddleocr.api_token_hint})` : '输入 API Token'"
                class="w-full rounded-xl border border-slate-200/80 bg-white px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 transition-colors focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-white/10 dark:bg-slate-800/80 dark:text-slate-200 dark:placeholder-slate-500"
              />
            </div>
            <div>
              <label class="mb-1.5 block text-xs font-bold text-slate-600 dark:text-slate-400">OCR 模型</label>
              <input
                v-model="form.paddleocr.model"
                type="text"
                placeholder="PaddleOCR-VL-1.5"
                class="w-full rounded-xl border border-slate-200/80 bg-white px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 transition-colors focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-white/10 dark:bg-slate-800/80 dark:text-slate-200 dark:placeholder-slate-500"
              />
            </div>
          </div>

          <!-- PaddleOCR 开关 -->
          <div class="mt-5 border-t border-slate-100 pt-5 dark:border-white/5">
            <p class="mb-3 text-xs font-bold text-slate-600 dark:text-slate-400">功能开关</p>
            <div class="space-y-3">
              <label
                v-for="toggle in [
                  { key: 'use_doc_orientation', label: '文档方向检测' },
                  { key: 'use_doc_unwarping', label: '文档去畸变' },
                  { key: 'use_chart_recognition', label: '图表识别' },
                ]"
                :key="toggle.key"
                class="flex cursor-pointer items-center justify-between"
              >
                <span class="text-sm font-medium text-slate-700 dark:text-slate-300">{{ toggle.label }}</span>
                <button
                  type="button"
                  @click="form.paddleocr[toggle.key] = !form.paddleocr[toggle.key]"
                  class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  :class="form.paddleocr[toggle.key] ? 'bg-blue-600 dark:bg-indigo-500' : 'bg-slate-200 dark:bg-slate-700'"
                >
                  <span
                    class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out"
                    :class="form.paddleocr[toggle.key] ? 'translate-x-5' : 'translate-x-0'"
                  ></span>
                </button>
              </label>
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
  </div>
</template>
