<script setup>
import { ref, watch, nextTick } from 'vue'
import * as api from '../api.js'
import { renderMarkdown, typesetMath } from '../utils.js'

const props = defineProps({
  visible: Boolean,
  sessionId: { type: Number, default: null },
  modelProvider: { type: String, default: 'openai' },
  modelName: { type: String, default: '' },
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

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- 空状态 -->
    <div v-if="!sessionId" class="flex-1 flex flex-col items-center justify-center text-center px-8">
      <div class="mb-6 flex size-16 items-center justify-center rounded-2xl bg-slate-100 dark:bg-white/[0.04]">
        <i class="fa-solid fa-comments text-2xl text-slate-400 dark:text-slate-500"></i>
      </div>
      <p class="text-xl font-bold text-slate-700 dark:text-slate-200">AI 学习助手</p>
      <p class="mt-2 text-sm text-slate-400 dark:text-slate-500 max-w-sm">在左侧选择一个对话，或新建一个开始提问</p>
      <button @click="emit('create-chat')" class="mt-6 h-10 px-6 rounded-xl bg-blue-600 text-white text-sm font-bold hover:bg-blue-700 transition-colors">
        <i class="fa-solid fa-plus mr-2"></i>新建对话
      </button>
    </div>

    <!-- 有活跃对话 -->
    <template v-else>
      <!-- 消息区域 -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto px-4 py-6 sm:px-8 custom-scrollbar">
        <div class="mx-auto max-w-3xl space-y-6">
          <!-- 空对话提示 -->
          <div v-if="messages.length === 0 && !streaming" class="flex flex-col items-center justify-center py-20 text-center">
            <i class="fa-solid fa-paper-plane text-3xl text-slate-300 dark:text-slate-600 mb-4"></i>
            <p class="text-sm text-slate-400 dark:text-slate-500">发送一条消息开始对话</p>
          </div>

          <div v-for="(msg, i) in messages" :key="i" class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
            <div
              class="max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed"
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

      <!-- 输入区域 -->
      <div class="shrink-0 border-t border-slate-200/60 dark:border-white/5 px-4 py-4 sm:px-8">
        <div class="mx-auto max-w-3xl flex gap-3">
          <textarea
            v-model="inputText"
            @keydown="handleKeydown"
            :disabled="streaming"
            rows="1"
            placeholder="输入你的问题..."
            class="flex-1 resize-none rounded-xl border border-slate-200/60 bg-white/60 px-4 py-2.5 text-sm outline-none transition-all focus:border-blue-300 focus:ring-2 focus:ring-blue-500/20 dark:border-white/10 dark:bg-white/[0.03] dark:text-white dark:focus:border-indigo-500/50 custom-scrollbar"
          ></textarea>
          <button
            @click="sendMessage"
            :disabled="!inputText.trim() || streaming"
            class="h-10 w-10 shrink-0 rounded-xl bg-blue-600 text-white flex items-center justify-center hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <i class="fa-solid fa-paper-plane text-sm"></i>
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
