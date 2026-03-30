<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import * as api from '../api.js'
import { renderMarkdown, typesetMath } from '../utils.js'

const props = defineProps({
  visible: Boolean,
  modelProvider: { type: String, default: 'openai' },
  modelName: { type: String, default: '' },
})
const emit = defineEmits(['push-toast'])

// ---- 会话列表 ----
const sessions = ref([])
const activeSessionId = ref(null)
const loadingSessions = ref(false)

async function loadSessions() {
  loadingSessions.value = true
  try {
    const data = await api.fetchMyChatSessions({ limit: 50 })
    sessions.value = data.sessions || []
  } catch (e) {
    emit('push-toast', 'error', e.message)
  } finally {
    loadingSessions.value = false
  }
}

watch(() => props.visible, (v) => { if (v) loadSessions() }, { immediate: true })

async function createNewChat() {
  try {
    const session = await api.createIndependentChat('新对话')
    sessions.value.unshift(session)
    activeSessionId.value = session.id
    messages.value = []
  } catch (e) {
    emit('push-toast', 'error', e.message)
  }
}

function selectSession(s) {
  activeSessionId.value = s.id
  loadMessages()
}

async function deleteSession(id) {
  try {
    await api.deleteChat(id)
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (activeSessionId.value === id) {
      activeSessionId.value = null
      messages.value = []
    }
  } catch (e) {
    emit('push-toast', 'error', e.message)
  }
}

// ---- 对话消息 ----
const messages = ref([])
const inputText = ref('')
const streaming = ref(false)
const messagesContainer = ref(null)
const abortCtrl = ref(null)

async function loadMessages() {
  if (!activeSessionId.value) return
  try {
    const result = await api.fetchMessages(activeSessionId.value, { limit: 50 })
    messages.value = result.messages || []
    await nextTick()
    scrollToBottom()
    typesetMath(messagesContainer.value)
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
  if (!text || !activeSessionId.value || streaming.value) return

  inputText.value = ''
  messages.value.push({ role: 'user', content: text })
  messages.value.push({ role: 'assistant', content: '' })
  await nextTick()
  scrollToBottom()

  streaming.value = true
  const ctrl = new AbortController()
  abortCtrl.value = ctrl

  try {
    const resp = await api.streamChat(
      activeSessionId.value,
      text,
      props.modelProvider,
      ctrl.signal,
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
            // 更新会话标题（用第一条消息的前 20 字）
            const firstMsg = text.slice(0, 20) + (text.length > 20 ? '...' : '')
            const session = sessions.value.find(s => s.id === activeSessionId.value)
            if (session && session.title === '新对话') {
              try {
                await api.updateChatTitle(activeSessionId.value, firstMsg)
                session.title = firstMsg
              } catch (_) {}
            }
          }
          if (payload.error) {
            messages.value[messages.value.length - 1].content += `\n\n⚠️ ${payload.error}`
          }
        } catch (_) {}
      }
    }

    await nextTick()
    typesetMath(messagesContainer.value)
  } catch (e) {
    if (e.name !== 'AbortError') {
      messages.value[messages.value.length - 1].content += `\n\n⚠️ ${e.message}`
    }
  } finally {
    streaming.value = false
    abortCtrl.value = null
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
  <div class="flex h-full overflow-hidden">
    <!-- 左侧：对话历史列表 -->
    <div class="w-72 shrink-0 flex flex-col border-r border-slate-200/60 dark:border-white/5 bg-white/50 dark:bg-white/[0.02]">
      <!-- 新建对话按钮 -->
      <div class="p-4">
        <button
          @click="createNewChat"
          class="w-full h-10 rounded-xl bg-blue-600 text-white text-sm font-bold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
        >
          <i class="fa-solid fa-plus"></i> 新建对话
        </button>
      </div>

      <!-- 历史列表 -->
      <div class="flex-1 overflow-y-auto px-2 pb-4 custom-scrollbar">
        <div v-if="sessions.length === 0 && !loadingSessions" class="px-4 py-8 text-center text-sm text-slate-400 dark:text-slate-500">
          暂无对话记录
        </div>
        <div
          v-for="s in sessions"
          :key="s.id"
          @click="selectSession(s)"
          class="group flex items-center gap-2 px-3 py-2.5 rounded-xl mb-1 cursor-pointer transition-colors"
          :class="activeSessionId === s.id
            ? 'bg-blue-50 dark:bg-indigo-500/10 text-blue-700 dark:text-indigo-300'
            : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/[0.04]'"
        >
          <i class="fa-solid fa-message text-xs shrink-0" :class="activeSessionId === s.id ? '' : 'opacity-40'"></i>
          <span class="flex-1 truncate text-sm">{{ s.title }}</span>
          <button
            @click.stop="deleteSession(s.id)"
            class="shrink-0 opacity-0 group-hover:opacity-100 text-slate-400 hover:text-rose-500 transition-all"
          >
            <i class="fa-solid fa-trash text-xs"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 右侧：对话窗口 -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- 空状态 -->
      <div v-if="!activeSessionId" class="flex-1 flex flex-col items-center justify-center text-center px-8">
        <div class="mb-6 flex size-16 items-center justify-center rounded-2xl bg-slate-100 dark:bg-white/[0.04]">
          <i class="fa-solid fa-comments text-2xl text-slate-400 dark:text-slate-500"></i>
        </div>
        <p class="text-xl font-bold text-slate-700 dark:text-slate-200">AI 学习助手</p>
        <p class="mt-2 text-sm text-slate-400 dark:text-slate-500 max-w-sm">选择一个对话继续，或点击"新建对话"开始提问</p>
        <button @click="createNewChat" class="mt-6 h-10 px-6 rounded-xl bg-blue-600 text-white text-sm font-bold hover:bg-blue-700 transition-colors">
          <i class="fa-solid fa-plus mr-2"></i>新建对话
        </button>
      </div>

      <!-- 有活跃对话 -->
      <template v-else>
        <!-- 消息区域 -->
        <div ref="messagesContainer" class="flex-1 overflow-y-auto px-4 py-6 sm:px-8 custom-scrollbar">
          <div class="mx-auto max-w-3xl space-y-6">
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
  </div>
</template>
