<script setup>
import { ref, watch, nextTick } from 'vue'
import * as api from '../api.js'
import { renderMarkdown, typesetMath } from '../utils.js'

const props = defineProps({
  visible: Boolean,
  sessionId: { type: Number, default: null },
  modelProvider: { type: String, default: 'openai' },
  modelName: { type: String, default: '' },
  username: { type: String, default: '' },
})
const emit = defineEmits(['push-toast', 'create-chat', 'session-title-updated'])

// ---- 对话消息 ----
const messages = ref([])
const inputText = ref('')
const streaming = ref(false)
const messagesContainer = ref(null)

watch(() => props.sessionId, (id) => {
  if (id) loadMessages()
  else messages.value = []
}, { immediate: true })

async function loadMessages() {
  if (!props.sessionId) return
  try {
    const result = await api.fetchMessages(props.sessionId, { limit: 50 })
    messages.value = result.messages || []
    await nextTick()
    scrollToBottom()
    if (messagesContainer.value) typesetMath(messagesContainer.value)
  } catch (e) {
    emit('push-toast', 'error', e.message)
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || !props.sessionId || streaming.value) return

  inputText.value = ''
  messages.value.push({ role: 'user', content: text })
  messages.value.push({ role: 'assistant', content: '' })
  await nextTick()
  scrollToBottom()

  streaming.value = true

  try {
    const resp = await api.streamChat(
      props.sessionId,
      text,
      props.modelProvider,
      null,
      props.modelName,
    )

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

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
          if (payload.token) {
            messages.value[messages.value.length - 1].content += payload.token
            await nextTick()
            scrollToBottom()
          }
          if (payload.done) {
            // 自动更新标题
            const firstMsg = text.slice(0, 20) + (text.length > 20 ? '...' : '')
            emit('session-title-updated', props.sessionId, firstMsg)
          }
          if (payload.error) {
            messages.value[messages.value.length - 1].content += `\n\n⚠️ ${payload.error}`
          }
        } catch (_) {}
      }
    }

    await nextTick()
    if (messagesContainer.value) typesetMath(messagesContainer.value)
  } catch (e) {
    if (e.name !== 'AbortError') {
      messages.value[messages.value.length - 1].content += `\n\n⚠️ ${e.message}`
    }
  } finally {
    streaming.value = false
  }
}

const textareaRef = ref(null)

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 200) + 'px'
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- 消息区域（含空状态） -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto custom-scrollbar">
      <div class="mx-auto max-w-5xl px-4 sm:px-8">

        <!-- 空状态：居中问候 -->
        <div v-if="messages.length === 0 && !streaming" class="flex flex-col items-center justify-center" style="min-height: calc(100vh - 200px)">
          <p class="text-2xl font-bold text-slate-800 dark:text-white">
            Hi，{{ username || '同学' }}
          </p>
          <p class="mt-2 text-sm text-slate-400 dark:text-slate-500">有问题，尽管问</p>
        </div>

        <!-- 消息列表 -->
        <div v-else class="space-y-6 py-6">
          <div v-for="(msg, i) in messages" :key="i" class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
            <div
              class="max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed"
              :class="msg.role === 'user'
                ? 'bg-blue-600 text-white rounded-br-lg'
                : 'bg-slate-100 dark:bg-white/[0.06] text-slate-700 dark:text-slate-200 rounded-bl-lg'"
            >
              <div v-if="msg.role === 'assistant'" v-html="renderMarkdown(msg.content)" class="prose prose-sm prose-slate dark:prose-invert max-w-none"></div>
              <div v-else class="whitespace-pre-wrap">{{ msg.content }}</div>
            </div>
          </div>

          <!-- 流式加载指示 -->
          <div v-if="streaming && messages.length && !messages[messages.length - 1].content" class="flex justify-start">
            <div class="bg-slate-100 dark:bg-white/[0.06] rounded-2xl rounded-bl-lg px-4 py-3">
              <div class="flex gap-1">
                <span class="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style="animation-delay: 0ms"></span>
                <span class="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style="animation-delay: 150ms"></span>
                <span class="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style="animation-delay: 300ms"></span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- 底部输入区域 -->
    <div class="shrink-0 px-4 pb-4 pt-2 sm:px-8">
      <div class="mx-auto max-w-5xl">
        <div class="rounded-2xl border border-slate-200/60 bg-white dark:border-white/10 dark:bg-[#1a1a24] overflow-hidden">
          <!-- 文本输入 -->
          <textarea
            ref="textareaRef"
            v-model="inputText"
            @keydown="handleKeydown"
            @input="autoResize"
            :disabled="streaming || !sessionId"
            rows="1"
            :placeholder="sessionId ? '有问题，尽管问，shift+enter 换行' : '请先新建或选择一个对话'"
            class="w-full resize-none bg-transparent px-4 pt-3 pb-1 text-sm outline-none text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500"
            style="min-height: 24px; max-height: 200px;"
          ></textarea>

          <!-- 底部工具栏 -->
          <div class="flex items-center justify-between px-3 pb-2.5 pt-1">
            <!-- 左侧功能按钮 -->
            <div class="flex items-center gap-0.5">
              <button
                disabled
                class="h-8 px-2.5 rounded-lg text-xs font-bold flex items-center gap-1.5 text-slate-400 dark:text-slate-500 cursor-not-allowed"
                title="深度思考（敬请期待）"
              >
                <i class="fa-solid fa-brain text-sm"></i>
                <span class="hidden sm:inline">深度思考</span>
              </button>
              <button
                disabled
                class="h-8 px-2.5 rounded-lg text-xs font-bold flex items-center gap-1.5 text-slate-400 dark:text-slate-500 cursor-not-allowed"
                title="联网搜索（敬请期待）"
              >
                <i class="fa-solid fa-globe text-sm"></i>
                <span class="hidden sm:inline">联网搜索</span>
              </button>
            </div>

            <!-- 右侧操作按钮 -->
            <div class="flex items-center gap-1.5">
              <button
                disabled
                class="h-8 w-8 rounded-lg flex items-center justify-center text-slate-400 dark:text-slate-500 hover:bg-slate-100 dark:hover:bg-white/5 transition-colors cursor-not-allowed"
                title="附件（敬请期待）"
              >
                <i class="fa-solid fa-plus text-sm"></i>
              </button>
              <button
                @click="sessionId ? sendMessage() : emit('create-chat')"
                :disabled="sessionId ? (!inputText.trim() || streaming) : false"
                class="h-8 w-8 rounded-full flex items-center justify-center transition-all"
                :class="inputText.trim() && sessionId
                  ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm'
                  : 'bg-slate-200 text-slate-400 dark:bg-white/10 dark:text-slate-500 opacity-50'"
              >
                <i class="fa-solid fa-arrow-up text-xs"></i>
              </button>
            </div>
          </div>
        </div>
        <p class="mt-2 text-center text-xs text-slate-400 dark:text-slate-500">内容由 AI 生成，仅供参考</p>
      </div>
    </div>
  </div>
</template>
