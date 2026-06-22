<script setup>
/**
 * ChatPageView.vue
 * 独立 AI 对话页面，支持多轮流式对话、深度思考展示和错题上下文引用。
 */
import { ref, watch, nextTick, computed, onMounted, onUnmounted } from 'vue'
import { MessageSquarePlus } from 'lucide-vue-next'
import * as api from '@/api/index.js'
import { getQuestionSnippet, renderMarkdown, typesetMath } from '@/utils/index.js'
import ContentPanel from '@/components/features/app/layout/ContentPanel.vue'
import BaseModal from '@/components/base/BaseModal.vue'
import { useToast } from '@/composables/useToast.js'
import { useSystemStatus } from '@/composables/useSystemStatus.js'
import { useAuth } from '@/composables/useAuth.js'
import { useAiChatSessions } from '@/composables/useAiChatSessions.js'
import { useWorkspaceNav } from '@/composables/useWorkspaceNav.js'
import { useProjects } from '@/composables/useProjects.js'
import deepseekLogo from '@/assets/deepseek.svg'
import ernieLogo from '@/assets/ernie.svg'

const QUOTA_EXCEEDED_CODE = 'DAILY_FREE_QUOTA_EXCEEDED'
const modelLogos = { openai: deepseekLogo, anthropic: ernieLogo }
const sourceLabelMap = { system: '平台托管', personal: '自己设置' }

const { pushToast } = useToast()
const {
  modelOptionsLoading,
  modelOptionsData,
  selectedLlmOptionId,
  selectedLlmOption,
  doFetchModelOptions,
} = useSystemStatus()
const { currentUser, setQuotaSnapshot, refreshCurrentUser } = useAuth()
const { activeAiChatId, createAiChat, onAiChatTitleUpdated } = useAiChatSessions(pushToast)
const { currentView, isMobile, canHover, setSettingsSubView } = useWorkspaceNav()
const { questionProjects } = useProjects()

const sessionId = computed(() => activeAiChatId.value)
const modelProvider = computed(() => selectedLlmOption.value?.category || 'openai')
const modelName = computed(() => selectedLlmOption.value?.model_name || '')
const providerSource = computed(() => selectedLlmOption.value?.source || '')
const providerId = computed(() => selectedLlmOption.value?.provider_id || '')
const username = computed(() => currentUser.value?.username || '')

// ---- 对话消息 ----
const messages = ref([])
const inputText = ref('')
const streaming = ref(false)
const modelMenuOpen = ref(false)
const messagesContainer = ref(null)
const contextQuestionsEl = ref(null)
const streamRenderTimer = ref(null)
const streamRenderRunning = ref(false)
const deepThink = ref(false)
const contextDialogOpen = ref(false)
const contextProjectId = ref(null)
const selectedContextQuestionIds = ref([])
const contextQuestionCache = ref({})
const loadingContextProjectId = ref(null)
const contextLoadError = ref('')
const hasConversationContent = computed(() => messages.value.length > 0 || streaming.value)
const AUTO_SCROLL_THRESHOLD = 80
const selectedContextProject = computed(() =>
  questionProjects.value.find((project) => String(project.id) === String(contextProjectId.value)) || null,
)
const contextQuestions = computed(() => contextQuestionCache.value[String(contextProjectId.value)] || [])
const selectedContextLabel = computed(() => {
  if (!selectedContextProject.value || selectedContextQuestionIds.value.length === 0) return ''
  return `${selectedContextProject.value.name} · ${selectedContextQuestionIds.value.length} 题`
})
const availableModelOptions = computed(() =>
  (modelOptionsData.value?.options || []).filter((option) => option.available !== false),
)
const selectedModelLabel = computed(() => selectedLlmOption.value?.model_name || '选择模型')
const selectedModelSourceLabel = computed(() => {
  if (!selectedLlmOption.value) return modelOptionsLoading.value ? '加载中' : '未配置'
  return sourceLabelMap[selectedLlmOption.value.source] || selectedLlmOption.value.source || '模型'
})
const canSwitchModel = computed(() => !streaming.value && availableModelOptions.value.length > 0)
const groupedChatModelOptions = computed(() => {
  const groups = modelOptionsData.value?.groups || []
  const groupLabels = new Map(groups.map((group) => [group.key, group.label]))
  const sources = []
  const seen = new Set()

  for (const option of availableModelOptions.value) {
    const source = option.source || 'other'
    if (!seen.has(source)) {
      seen.add(source)
      sources.push(source)
    }
  }

  return sources.map((source) => ({
    key: source,
    label: groupLabels.get(source) || sourceLabelMap[source] || '模型',
    options: availableModelOptions.value.filter((option) => (option.source || 'other') === source),
  }))
})

const isSelectedChatModel = (option) => selectedLlmOptionId.value === option.option_id

const goToApiSettings = () => {
  modelMenuOpen.value = false
  const target = currentUser.value?.is_admin && selectedLlmOption.value?.source === 'system'
    ? 'system-providers'
    : 'api'
  setSettingsSubView(target)
}

const toggleModelMenu = async () => {
  if (streaming.value) return
  if (!modelOptionsData.value && !modelOptionsLoading.value) {
    await doFetchModelOptions()
  }
  if (!availableModelOptions.value.length) {
    pushToast('error', '暂无可用模型，请先在设置中配置')
    return
  }
  modelMenuOpen.value = !modelMenuOpen.value
}

const selectChatModel = (option) => {
  if (!option || streaming.value) return
  selectedLlmOptionId.value = option.option_id
  modelMenuOpen.value = false
}

/**
 * 创建新独立对话，并保持当前工作台视图为 AI 对话。
 */
function createCurrentAiChat() {
  return createAiChat(currentView)
}

watch(sessionId, (id, prevId) => {
  if (prevId !== undefined && id !== prevId) {
    clearContext()
  }
  if (id) loadMessages()
  else messages.value = []
}, { immediate: true })

watch(questionProjects, () => {
  if (contextProjectId.value && !selectedContextProject.value) {
    clearContext()
  }
})

watch([contextDialogOpen, contextQuestions], async () => {
  if (!contextDialogOpen.value || !contextQuestionsEl.value) return
  await nextTick()
  typesetMath(contextQuestionsEl.value)
}, { flush: 'post' })

onMounted(() => {
  if (!modelOptionsData.value && !modelOptionsLoading.value) {
    doFetchModelOptions()
  }
})

watch(streaming, (value) => {
  if (value) modelMenuOpen.value = false
})

/**
 * 加载当前独立对话的历史消息。
 */
async function loadMessages() {
  if (!sessionId.value) return
  try {
    const result = await api.fetchMessages(sessionId.value, { limit: 50 })
    messages.value = result.messages || []
    await nextTick()
    scrollToBottom()
    if (messagesContainer.value) typesetMath(messagesContainer.value)
  } catch (e) {
    pushToast('error', e.message)
  }
}

/**
 * 将消息容器滚动到底部。
 */
function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

/**
 * 判断用户是否接近底部，用于决定流式更新时是否自动跟随滚动。
 */
function isNearBottom() {
  const el = messagesContainer.value
  if (!el) return true
  return el.scrollHeight - el.scrollTop - el.clientHeight <= AUTO_SCROLL_THRESHOLD
}

function scrollToBottomIfNeeded(shouldScroll) {
  if (shouldScroll) scrollToBottom()
}

function getStreamingAssistantEl() {
  return messagesContainer.value?.querySelector('[data-streaming-assistant="true"]') || null
}

/**
 * 把流式缓存内容刷入消息正文，并对当前助手消息重新渲染公式。
 */
async function flushStreamingMessage(msg) {
  if (!msg || streamRenderRunning.value) return
  const shouldScroll = isNearBottom()
  streamRenderRunning.value = true
  msg.content = msg.rawContent || ''
  await nextTick()
  const el = getStreamingAssistantEl()
  if (el) await typesetMath(el)
  scrollToBottomIfNeeded(shouldScroll)
  streamRenderRunning.value = false

  if (msg.rawContent !== msg.content) {
    scheduleStreamRender(msg)
  }
}

/**
 * 对流式渲染做节流，避免每个 token 都触发 Markdown/MathJax 重排。
 */
function scheduleStreamRender(msg, delay = 260) {
  if (streamRenderTimer.value) return
  streamRenderTimer.value = window.setTimeout(async () => {
    streamRenderTimer.value = null
    await flushStreamingMessage(msg)
  }, delay)
}

onUnmounted(() => {
  if (streamRenderTimer.value) {
    window.clearTimeout(streamRenderTimer.value)
  }
})

/**
 * 发送独立对话消息，并消费后端 SSE 风格的流式响应。
 */
async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || !sessionId.value || streaming.value) return

  inputText.value = ''
  const rollbackIndex = messages.value.length
  // 消息结构：{ role, content, reasoning?, reasoningOpen? }
  const sentAt = Date.now()
  messages.value.push({ id: `local-user-${sentAt}`, role: 'user', content: text })
  messages.value.push({ id: `local-assistant-${sentAt}`, role: 'assistant', content: '', rawContent: '', reasoning: '', reasoningOpen: false })
  await nextTick()
  scrollToBottom()
  // 重置 textarea 高度
  if (textareaRef.value) textareaRef.value.style.height = 'auto'

  streaming.value = true
  const useDeepThink = deepThink.value

  try {
    const resp = await api.streamChat(
      sessionId.value,
      text,
      modelProvider.value,
      null,
      modelName.value,
      {
        deepThink: useDeepThink,
        providerSource: providerSource.value,
        providerId: providerId.value,
        contextRefs: selectedContextQuestionIds.value.length ? [{
          type: 'question',
          project_id: contextProjectId.value,
          question_ids: selectedContextQuestionIds.value,
        }] : [],
      },
    )

    if (!resp.ok) {
      const err = await resp.json().catch(() => null)
      const error = new Error((err && err.error) || `HTTP ${resp.status}`)
      error.status = resp.status
      error.code = err?.code || null
      error.quota = err?.quota || null
      throw error
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    const lastMsg = () => messages.value[messages.value.length - 1]

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const payload = JSON.parse(line.slice(6))
          if (payload.reasoning) {
            const shouldScroll = isNearBottom()
            lastMsg().reasoning += payload.reasoning
            lastMsg().reasoningOpen = true
            await nextTick()
            scrollToBottomIfNeeded(shouldScroll)
          }
          if (payload.token) {
            const shouldScroll = isNearBottom()
            if (lastMsg().reasoningOpen && lastMsg().reasoning) {
              lastMsg().reasoningOpen = false
            }
            lastMsg().rawContent = (lastMsg().rawContent || '') + payload.token
            scheduleStreamRender(lastMsg())
            scrollToBottomIfNeeded(shouldScroll)
          }
          if (payload.done) {
            const firstMsg = text.slice(0, 20) + (text.length > 20 ? '...' : '')
            onAiChatTitleUpdated(sessionId.value, firstMsg)
          }
          if (payload.error) {
            lastMsg().rawContent = (lastMsg().rawContent || lastMsg().content || '') + `\n\n⚠️ ${payload.error}`
            await flushStreamingMessage(lastMsg())
          }
        } catch (_) { }
      }
    }

    await refreshCurrentUser()
    const assistantMsg = messages.value[messages.value.length - 1]
    if (assistantMsg?.role === 'assistant' && assistantMsg.rawContent !== undefined) {
      if (streamRenderTimer.value) {
        window.clearTimeout(streamRenderTimer.value)
        streamRenderTimer.value = null
      }
      await flushStreamingMessage(assistantMsg)
    }
    await nextTick()
    if (messagesContainer.value) typesetMath(messagesContainer.value)
  } catch (e) {
    if (e?.code === QUOTA_EXCEEDED_CODE) {
      messages.value.splice(rollbackIndex, 2)
      if (e.quota) setQuotaSnapshot(e.quota)
      pushToast('error', e.message || '今日免费体验次数已用完')
    } else if (e.name !== 'AbortError') {
      messages.value[messages.value.length - 1].content += `\n\n⚠️ ${e.message}`
    }
  } finally {
    streaming.value = false
  }
}


const textareaRef = ref(null)

/**
 * Enter 发送消息，Shift + Enter 保留换行。
 */
function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

/**
 * 根据输入内容自动调整 textarea 高度。
 */
function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 200) + 'px'
}

/**
 * 切换上下文题目所属的错题库，并懒加载该项目题目。
 */
async function openContextProject(project) {
  const nextId = project?.id || null
  if (!nextId) return
  if (String(contextProjectId.value) !== String(nextId)) {
    contextProjectId.value = nextId
    selectedContextQuestionIds.value = []
  }
  await loadContextQuestions(nextId)
}

/**
 * 打开上下文选择弹窗，默认选中第一个错题库。
 */
async function openContextDialog() {
  contextDialogOpen.value = true
  if (!contextProjectId.value && questionProjects.value.length) {
    await openContextProject(questionProjects.value[0])
  }
}

/**
 * 加载某个错题库下可作为对话上下文的题目列表。
 */
async function loadContextQuestions(projectId) {
  const key = String(projectId)
  if (contextQuestionCache.value[key]) return
  loadingContextProjectId.value = projectId
  contextLoadError.value = ''
  try {
    const data = await api.fetchErrorBank({ project_id: projectId, page: 1, page_size: 30 })
    contextQuestionCache.value = {
      ...contextQuestionCache.value,
      [key]: data.items || [],
    }
  } catch (e) {
    contextLoadError.value = e.message || '题目加载失败'
  } finally {
    loadingContextProjectId.value = null
    await nextTick()
    if (contextDialogOpen.value && contextQuestionsEl.value) {
      typesetMath(contextQuestionsEl.value)
    }
  }
}

/**
 * 切换某道题是否作为本次提问的上下文。
 */
function toggleContextQuestion(questionId) {
  const id = Number(questionId)
  const exists = selectedContextQuestionIds.value.some((item) => Number(item) === id)
  selectedContextQuestionIds.value = exists
    ? selectedContextQuestionIds.value.filter((item) => Number(item) !== id)
    : [...selectedContextQuestionIds.value, id]
}

function isContextQuestionSelected(questionId) {
  return selectedContextQuestionIds.value.some((item) => String(item) === String(questionId))
}

/**
 * 清空当前已选择的上下文题目。
 */
function clearContext() {
  contextProjectId.value = null
  selectedContextQuestionIds.value = []
  contextLoadError.value = ''
}

function questionContextSnippet(question) {
  return getQuestionSnippet(question, 0, '暂无题干内容')
}
</script>

<template>
  <div class="h-full min-h-0">
    <ContentPanel title="AI 对话">
      <template #toolbar>
        <div class="flex items-center rounded-full bg-gray-100/50 p-1 dark:bg-white/[0.04]">
          <button @click="createCurrentAiChat"
            class="flex h-8 w-8 items-center justify-center rounded-full text-gray-500 transition-all hover:bg-white dark:text-[#8a8f98] dark:hover:bg-white/[0.08] dark:hover:text-white"
            :title="canHover ? '新对话' : null">
            <MessageSquarePlus class="h-4 w-4" />
          </button>
        </div>
      </template>
      <div class="flex h-full min-h-0 flex-col overflow-hidden">
        <!-- 消息区域（含空状态） -->
        <div ref="messagesContainer" class="min-h-0 flex-1 custom-scrollbar"
          :class="hasConversationContent ? 'overflow-y-auto' : 'overflow-hidden'">
          <div class="mx-auto flex h-full max-w-5xl flex-col px-4 sm:px-8">

            <!-- 空状态：居中问候 -->
            <div v-if="messages.length === 0 && !streaming"
              class="flex min-h-0 flex-1 flex-col items-center justify-center">
              <p class="text-2xl font-bold text-gray-900 dark:text-[#f7f8f8]">
                Hi，{{ username || '同学' }}
              </p>
              <p class="mt-2 text-sm text-gray-500 dark:text-[#62666d]">有问题，尽管问</p>
            </div>

            <!-- 消息列表 -->
            <TransitionGroup v-else appear name="chat-message" tag="div" class="space-y-6 py-6">
              <div v-for="(msg, i) in messages" :key="msg.id || `${msg.role}-${i}-${msg.content.slice(0, 12)}`"
                class="flex chat-message-item"
                :class="msg.role === 'user' ? 'justify-end chat-message-item--user' : 'justify-start chat-message-item--assistant'">
                <div class="rounded-2xl px-4 py-3 text-sm leading-relaxed"
                  :class="msg.role === 'user'
                    ? 'max-w-[85%] accent-bg text-white rounded-br-lg shadow-sm dark:text-white dark:border-none'
                    : 'w-full bg-transparent text-gray-800 rounded-bl-lg dark:text-[#d0d6e0]'">
                  <!-- 思考过程折叠面板 -->
                  <div v-if="msg.role === 'assistant' && msg.reasoning" class="mb-3">
                    <button @click="msg.reasoningOpen = !msg.reasoningOpen"
                      class="flex items-center gap-2 text-xs font-bold text-gray-500 hover:text-gray-700 dark:text-[#8a8f98] dark:hover:text-[#d0d6e0] transition-colors">
                      <i class="fa-solid fa-brain accent-text"></i>
                      <span>{{ streaming && i === messages.length - 1 && !msg.content ? '思考中...' : '已深度思考' }}</span>
                      <i class="fa-solid text-[10px] transition-transform"
                        :class="msg.reasoningOpen ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
                    </button>
                    <Transition enter-active-class="transition-all duration-200 ease-out"
                      enter-from-class="opacity-0 max-h-0" enter-to-class="opacity-100 max-h-[400px]"
                      leave-active-class="transition-all duration-150 ease-in"
                      leave-from-class="opacity-100 max-h-[400px]" leave-to-class="opacity-0 max-h-0">
                      <div v-if="msg.reasoningOpen"
                        class="mt-2 overflow-auto max-h-[400px] rounded-xl bg-gray-50 border border-gray-100 p-3 text-xs text-gray-600 leading-relaxed custom-scrollbar whitespace-pre-wrap dark:bg-white/[0.03] dark:border-none dark:text-[#8a8f98]">
                        {{ msg.reasoning }}</div>
                    </Transition>
                  </div>
                  <!-- 正文内容 -->
                  <div v-if="msg.role === 'assistant' && !(streaming && i === messages.length - 1 && !msg.content)"
                    v-html="renderMarkdown(msg.content)" class="prose prose-sm max-w-none dark:prose-invert"
                    :data-streaming-assistant="streaming && i === messages.length - 1 ? 'true' : null"></div>
                  <div v-else-if="msg.role === 'assistant' && streaming && i === messages.length - 1 && !msg.content"
                    class="flex gap-1">
                    <span class="w-2 h-2 rounded-full bg-gray-400 dark:bg-[#62666d] animate-bounce"
                      style="animation-delay: 0ms"></span>
                    <span class="w-2 h-2 rounded-full bg-gray-400 dark:bg-[#62666d] animate-bounce"
                      style="animation-delay: 150ms"></span>
                    <span class="w-2 h-2 rounded-full bg-gray-400 dark:bg-[#62666d] animate-bounce"
                      style="animation-delay: 300ms"></span>
                  </div>
                  <div v-else class="whitespace-pre-wrap">{{ msg.content }}</div>
                </div>
              </div>
            </TransitionGroup>

          </div>
        </div>

        <!-- 底部输入区域 -->
        <div class="shrink-0 px-4 pt-2 sm:px-8">
          <div class="mx-auto max-w-5xl">
            <div
              class="rounded-xl bg-white shadow-sm dark:bg-white/[0.03]">
              <!-- 文本输入 -->
              <textarea ref="textareaRef" v-model="inputText" @keydown="handleKeydown" @input="autoResize"
                :disabled="streaming || !sessionId" rows="1"
                :placeholder="sessionId ? '有问题，尽管问，shift+enter 换行' : '请先新建或选择一个对话'"
                class="w-full resize-none bg-transparent px-4 pt-3 pb-1 text-sm outline-none text-gray-900 placeholder-gray-400 dark:text-[#f7f8f8] dark:placeholder-[#62666d]"
                style="min-height: 24px; max-height: 200px;"></textarea>

              <!-- 底部工具栏 -->
              <div class="flex items-center justify-between px-3 pb-2.5 pt-1">
                <!-- 左侧功能按钮 -->
                <div class="flex items-center gap-2">
                  <div class="relative">
                    <button data-chat-model-selector type="button" :disabled="streaming || modelOptionsLoading"
                      class="group flex h-9 w-[min(18rem,calc(100vw-9rem))] items-center gap-2 rounded-lg bg-gray-100/80 px-2.5 text-xs font-bold shadow-sm shadow-black/[0.02] transition-colors sm:w-64 dark:bg-white/[0.04] dark:shadow-black/20"
                      :class="canSwitchModel
                        ? 'text-gray-700 hover:bg-white hover:text-gray-950 dark:text-[#d0d6e0] dark:hover:bg-white/[0.07] dark:hover:text-[#f7f8f8]'
                        : 'cursor-not-allowed text-gray-400 dark:text-[#62666d]'"
                      :title="canHover ? '切换对话模型' : null" @click="toggleModelMenu">
                      <span
                        class="relative flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-white text-gray-500 dark:bg-white/[0.06] dark:text-[#8a8f98]">
                        <img v-if="selectedLlmOption && modelLogos[selectedLlmOption.category]"
                          :src="modelLogos[selectedLlmOption.category]" class="h-3.5 w-3.5 object-contain" alt="" />
                        <i v-else class="fa-solid fa-robot text-[10px]"></i>
                        <span
                          class="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full border border-white bg-emerald-500 dark:border-[#171719]"></span>
                      </span>
                      <span class="min-w-0 flex-1 truncate text-[13px] font-semibold">
                        {{ modelOptionsLoading ? '加载模型...' : selectedModelLabel }}
                      </span>
                      <span
                        class="hidden shrink-0 rounded-md bg-white px-1.5 py-0.5 text-[10px] font-semibold text-gray-500 dark:bg-white/[0.06] dark:text-[#8a8f98] md:inline-flex">
                        {{ selectedModelSourceLabel }}
                      </span>
                      <i class="fa-solid fa-chevron-down shrink-0 text-[10px] text-gray-400 transition-transform dark:text-[#62666d]"
                        :class="modelMenuOpen ? 'rotate-180' : ''"></i>
                    </button>

                    <Transition enter-active-class="transition duration-150 ease-out"
                      enter-from-class="translate-y-1 opacity-0" enter-to-class="translate-y-0 opacity-100"
                      leave-active-class="transition duration-100 ease-in" leave-from-class="translate-y-0 opacity-100"
                      leave-to-class="translate-y-1 opacity-0">
                      <div v-if="modelMenuOpen"
                        class="absolute bottom-11 left-0 z-30 w-72 overflow-hidden rounded-xl border border-gray-200 bg-white p-1.5 text-sm text-gray-700 shadow-xl shadow-black/10 outline-none dark:border-white/[0.08] dark:bg-[#1f1f20] dark:text-[#d7d7d8] dark:shadow-black/35">
                        <template v-for="group in groupedChatModelOptions" :key="group.key">
                          <div
                            class="select-none px-3 py-2 text-[11px] font-semibold text-gray-500 first:pt-1.5 dark:text-[#8a8f98]">
                            {{ group.label }}
                          </div>
                          <button v-for="option in group.options" :key="option.option_id" type="button"
                            :data-chat-model-option="option.option_id"
                            class="flex h-9 w-full items-center gap-3 rounded-md px-3 text-left outline-none transition-colors"
                            :class="isSelectedChatModel(option)
                              ? 'bg-gray-100 text-gray-950 dark:bg-white/[0.07] dark:text-[#f7f8f8]'
                              : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-[#cbd5e1] dark:hover:bg-white/[0.07] dark:hover:text-[#f7f8f8]'"
                            @click="selectChatModel(option)">
                            <img v-if="modelLogos[option.category]" :src="modelLogos[option.category]"
                              class="h-4 w-4 shrink-0 object-contain opacity-80" alt="" />
                            <i v-else
                              class="fa-solid fa-robot w-4 shrink-0 text-center text-sm text-gray-500 dark:text-[#9aa0aa]"></i>
                            <span class="min-w-0 flex-1 truncate font-semibold">{{ option.model_name || option.label }}</span>
                            <span v-if="option.is_default"
                              class="shrink-0 rounded-md bg-white px-1.5 py-0.5 text-[10px] font-semibold text-gray-400 dark:bg-white/[0.06] dark:text-[#8a8f98]">
                              默认
                            </span>
                            <i v-if="isSelectedChatModel(option)"
                              class="fa-solid fa-check shrink-0 text-[10px] text-emerald-500"></i>
                          </button>
                        </template>

                        <div class="my-1 h-px bg-gray-200 dark:bg-white/[0.08]"></div>
                        <button type="button"
                          class="flex h-9 w-full items-center gap-3 rounded-md px-3 text-sm font-semibold text-gray-700 outline-none transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-[#d7d7d8] dark:hover:bg-white/[0.07] dark:hover:text-[#f7f8f8]"
                          @click.stop="goToApiSettings">
                          <i
                            class="fa-solid fa-plug-circle-bolt w-4 shrink-0 text-center text-sm text-gray-500 dark:text-[#9aa0aa]"></i>
                          <span>API 设置</span>
                        </button>
                      </div>
                    </Transition>
                  </div>
                  <button @click="deepThink = !deepThink"
                    class="h-8 px-2.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-colors"
                    :class="deepThink
                      ? 'accent-bg-soft accent-text'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50 dark:text-[#62666d] dark:hover:text-[#8a8f98] dark:hover:bg-transparent'" :title="canHover ? '深度思考' : null">
                    <i class="fa-solid fa-brain text-sm"></i>
                    <span class="hidden sm:inline">深度思考</span>
                  </button>
                </div>

                <!-- 右侧操作按钮 -->
                <div class="flex items-center gap-1.5">
                  <div v-if="selectedContextLabel"
                    class="flex max-w-[150px] items-center gap-1.5 rounded-lg border border-[rgb(var(--accent-rgb)/0.24)] bg-[rgb(var(--accent-rgb)/0.10)] px-2.5 py-1.5 text-xs font-semibold accent-text sm:max-w-[220px]">
                    <i class="fa-solid fa-database text-[11px]"></i>
                    <span class="min-w-0 truncate">{{ selectedContextLabel }}</span>
                    <button class="ml-0.5 text-[10px] opacity-70 transition-opacity hover:opacity-100"
                      :title="canHover ? '移除引用' : null" @click.stop="clearContext">
                      <i class="fa-solid fa-xmark"></i>
                    </button>
                  </div>
                  <button @click.stop="openContextDialog"
                    class="h-8 w-8 rounded-lg flex items-center justify-center text-gray-500 hover:bg-gray-50 hover:text-gray-700 dark:text-[#62666d] dark:hover:bg-white/[0.04] dark:hover:text-[#d0d6e0] transition-colors"
                    :title="canHover ? '引用错题' : null">
                    <i class="fa-solid fa-plus text-sm"></i>
                  </button>
                  <button @click="sessionId ? sendMessage() : createCurrentAiChat()"
                    :disabled="sessionId ? (!inputText.trim() || streaming) : false"
                    class="h-8 w-8 rounded-full flex items-center justify-center transition-all" :class="inputText.trim() && sessionId
                      ? 'accent-bg text-white shadow-sm'
                      : 'bg-gray-100 text-gray-400 dark:bg-white/[0.06] dark:text-[#62666d]'">
                    <i class="fa-solid fa-arrow-up text-xs"></i>
                  </button>
                </div>
              </div>
            </div>
            <p class="mt-2 text-center text-xs text-gray-400 dark:text-[#62666d]">内容由 AI 生成，仅供参考</p>
          </div>
        </div>
      </div>
    </ContentPanel>

    <BaseModal :open="contextDialogOpen" title="引用错题回答" icon="fa-database" iconBg="accent-bg-soft"
      iconClass="accent-text" maxWidth="max-w-4xl sm:w-[58rem]" bodyClass="px-0 py-0"
      @close="contextDialogOpen = false">
      <div v-if="questionProjects.length === 0" class="px-6 py-6">
        <div class="rounded-xl border border-dashed border-gray-200 px-6 py-10 text-center dark:border-white/[0.08]">
          <div
            class="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-gray-100 text-gray-400 dark:bg-white/[0.05] dark:text-[#62666d]">
            <i class="fa-solid fa-database"></i>
          </div>
          <p class="mt-3 text-sm font-semibold text-gray-700 dark:text-[#d0d6e0]">还没有可引用的错题库</p>
          <p class="mt-1 text-xs text-gray-400 dark:text-[#62666d]">先创建错题库并导入题目后，就可以在 AI 对话里引用。</p>
        </div>
      </div>
      <div v-else
        class="grid h-[66vh] min-h-[28rem] grid-cols-1 overflow-hidden border-t border-gray-100 dark:border-white/[0.06] md:grid-cols-[15rem_minmax(0,1fr)]">
        <aside
          class="border-b border-gray-100 bg-gray-50/70 p-3 dark:border-white/[0.06] dark:bg-black/10 md:border-b-0 md:border-r">
          <div class="mb-2 px-2 text-[11px] font-medium text-gray-400 dark:text-[#62666d]">选择错题库</div>
          <div
            class="flex max-h-32 gap-1 overflow-x-auto pb-1 custom-scrollbar md:block md:max-h-none md:space-y-1 md:overflow-y-auto md:overflow-x-hidden md:pb-0">
            <button v-for="project in questionProjects" :key="project.id"
              class="flex min-w-32 items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-semibold transition-colors md:w-full"
              :class="String(contextProjectId) === String(project.id)
                ? 'bg-[rgb(var(--accent-rgb)/0.14)] accent-text'
                : 'text-gray-600 hover:bg-white hover:text-gray-900 dark:text-[#9aa0aa] dark:hover:bg-white/[0.045] dark:hover:text-[#f7f8f8]'"
              @click="openContextProject(project)">
              <i class="fa-solid fa-database w-4 text-center text-xs"></i>
              <span class="min-w-0 flex-1 truncate">{{ project.name }}</span>
            </button>
          </div>
        </aside>

        <section class="flex min-h-0 flex-col">
          <div class="flex items-center justify-between border-b border-gray-100 px-5 py-3 dark:border-white/[0.06]">
            <div class="min-w-0">
              <p class="truncate text-sm font-bold text-gray-900 dark:text-[#f7f8f8]">
                {{ selectedContextProject?.name || '选择错题库' }}
              </p>
              <p class="mt-0.5 text-xs text-gray-400 dark:text-[#62666d]">
                选择本次对话要参考的具体题目
              </p>
            </div>
            <button v-if="selectedContextQuestionIds.length" class="shrink-0 text-xs font-semibold accent-text"
              @click="clearContext">
              清空
            </button>
          </div>

          <div ref="contextQuestionsEl" class="min-h-0 flex-1 overflow-y-auto p-4 custom-scrollbar">
            <div v-if="!contextProjectId"
              class="flex h-full items-center justify-center text-sm text-gray-400 dark:text-[#62666d]">
              先选择一个错题库
            </div>
            <div v-else-if="loadingContextProjectId && String(loadingContextProjectId) === String(contextProjectId)"
              class="flex h-full items-center justify-center gap-2 text-sm text-gray-400 dark:text-[#62666d]">
              <i class="fa-solid fa-spinner animate-spin"></i>
              加载题目中
            </div>
            <div v-else-if="contextLoadError" class="flex h-full items-center justify-center text-sm text-rose-500">
              {{ contextLoadError }}
            </div>
            <div v-else-if="contextQuestions.length === 0"
              class="flex h-full items-center justify-center text-sm text-gray-400 dark:text-[#62666d]">
              这个错题库还没有题目
            </div>
            <div v-else class="space-y-2">
              <button v-for="question in contextQuestions" :key="question.id"
                class="group flex items-start gap-3 rounded-xl border px-3 py-3 text-left transition-colors"
                :class="isContextQuestionSelected(question.id)
                  ? 'border-[rgb(var(--accent-rgb)/0.45)] bg-[rgb(var(--accent-rgb)/0.12)]'
                  : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50 dark:border-white/[0.07] dark:bg-white/[0.025] dark:hover:border-white/[0.12] dark:hover:bg-white/[0.045]'"
                @click="toggleContextQuestion(question.id)">
                <span
                  class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border transition-colors"
                  :class="isContextQuestionSelected(question.id)
                    ? 'accent-bg accent-border text-white'
                    : 'border-gray-300 bg-white dark:border-white/[0.16] dark:bg-transparent'">
                  <i v-if="isContextQuestionSelected(question.id)" class="fa-solid fa-check text-[10px]"></i>
                </span>
                <span class="min-w-0 flex-1">
                  <span
                    class="flex flex-wrap items-center gap-1.5 text-[11px] font-semibold text-gray-500 dark:text-[#8a8f98]">
                    <span>#{{ question.id }}</span>
                    <span v-if="question.question_type"
                      class="rounded-md bg-gray-100 px-1.5 py-0.5 dark:bg-white/[0.06]">
                      {{ question.question_type }}
                    </span>
                    <span v-if="question.subject"
                      class="rounded-md bg-[rgb(var(--accent-rgb)/0.12)] px-1.5 py-0.5 accent-text">
                      {{ question.subject }}
                    </span>
                  </span>
                  <span class="mt-2 block text-sm leading-relaxed text-gray-700 dark:text-[#d0d6e0]">
                    {{ questionContextSnippet(question) }}
                  </span>
                </span>
              </button>
            </div>
          </div>
        </section>
      </div>
      <template #footer>
        <div class="mr-auto flex items-center gap-2 text-xs text-gray-400 dark:text-[#62666d]">
          <i class="fa-solid fa-link"></i>
          <span>已选择 {{ selectedContextQuestionIds.length }} 题</span>
        </div>
        <button
          class="rounded-lg px-4 py-2 text-sm font-semibold text-gray-500 transition-colors hover:bg-gray-100 dark:text-[#8a8f98] dark:hover:bg-white/[0.05]"
          @click="contextDialogOpen = false">
          取消
        </button>
        <button
          class="rounded-lg px-4 py-2 text-sm font-semibold text-white transition-colors accent-bg disabled:opacity-40"
          :disabled="selectedContextQuestionIds.length === 0" @click="contextDialogOpen = false">
          确定引用
        </button>
      </template>
    </BaseModal>
  </div>
</template>

<style scoped>
.chat-message-enter-active {
  transition:
    opacity 0.32s ease,
    transform 0.32s cubic-bezier(0.16, 1, 0.3, 1);
}

.chat-message-enter-from {
  opacity: 0;
  transform: translateY(14px) scale(0.96);
}

.chat-message-enter-from.chat-message-item--user {
  transform: translateX(18px) translateY(8px) scale(0.96);
}

.chat-message-enter-from.chat-message-item--assistant {
  transform: translateX(-18px) translateY(8px) scale(0.98);
}

.chat-message-leave-active {
  transition:
    opacity 0.16s ease,
    transform 0.16s ease;
}

.chat-message-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.99);
}

.chat-message-move {
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

:deep(.prose mjx-container[display="true"]) {
  display: block;
  overflow-x: auto;
  margin: 0.9rem 0;
  padding: 0.9rem 1rem;
  border: none;
  border-radius: 0.75rem;
  background: rgb(248 250 252 / 0.72);
}

:global(.dark .prose mjx-container[display="true"]) {
  border: none;
  border-radius: 0.75rem;
  background: #43434347;
  color: #d0d6e0;
}
</style>
