<script setup>
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  sessions: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'create-chat', 'select-chat'])

const query = ref('')
const inputRef = ref(null)

const normalizedQuery = computed(() => query.value.trim().toLowerCase())
const filteredSessions = computed(() => {
  if (!normalizedQuery.value) return props.sessions
  return props.sessions.filter((session) => {
    const title = String(session.title || '').toLowerCase()
    return title.includes(normalizedQuery.value)
  })
})

const groupedSessions = computed(() => {
  const groups = []
  const today = []
  const earlier = []

  for (const session of filteredSessions.value) {
    if (isToday(session.updated_at || session.created_at)) today.push(session)
    else earlier.push(session)
  }

  if (today.length) groups.push({ label: '今天', sessions: today })
  if (earlier.length) groups.push({ label: today.length ? '更早' : '最近', sessions: earlier })
  return groups
})

function isToday(value) {
  if (!value) return false
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return false
  const now = new Date()
  return date.getFullYear() === now.getFullYear()
    && date.getMonth() === now.getMonth()
    && date.getDate() === now.getDate()
}

function close() {
  query.value = ''
  emit('close')
}

function createChat() {
  query.value = ''
  emit('create-chat')
}

function selectChat(session) {
  query.value = ''
  emit('select-chat', session)
}

watch(() => props.open, async (open) => {
  if (!open) return
  await nextTick()
  inputRef.value?.focus()
})
</script>

<template>
  <Teleport to="body">
    <Transition name="chat-search-backdrop" appear>
      <div
        v-if="open"
        class="fixed inset-0 z-[100] bg-slate-950/35 dark:bg-black/45"
        @click="close"
      ></div>
    </Transition>

    <Transition name="chat-search-panel" appear>
      <div
        v-if="open"
        class="fixed inset-0 z-[101] flex items-center justify-center p-4"
        @click.self="close"
        @keydown.esc="close"
      >
        <section
          class="flex max-h-[min(42rem,calc(100vh-3rem))] w-full max-w-[42.5rem] flex-col overflow-hidden rounded-2xl border border-slate-200/70 bg-white text-slate-900 shadow-2xl shadow-slate-950/20 dark:border-white/[0.08] dark:bg-[#2f2f2f] dark:text-[#f4f4f4] dark:shadow-black/40"
          role="dialog"
          aria-modal="true"
          aria-label="搜索聊天"
        >
          <header class="flex h-16 shrink-0 items-center border-b border-slate-200/70 px-6 dark:border-white/[0.08]">
            <input
              ref="inputRef"
              v-model="query"
              type="text"
              placeholder="搜索聊天..."
              class="min-w-0 flex-1 bg-transparent text-base text-slate-900 outline-none placeholder:text-slate-400 dark:text-white dark:placeholder:text-[#b8b8b8]"
            />
            <button
              type="button"
              class="ml-4 flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:text-[#b8b8b8] dark:hover:bg-white/[0.08] dark:hover:text-white"
              title="关闭"
              @click="close"
            >
              <i class="fa-solid fa-xmark text-base"></i>
            </button>
          </header>

          <div class="min-h-0 flex-1 overflow-y-auto px-6 py-4">
            <button
              type="button"
              class="mb-5 flex h-10 w-full items-center gap-3 rounded-lg px-0 text-left text-sm font-medium text-slate-900 transition-colors hover:text-slate-600 dark:text-white dark:hover:text-[#d8d8d8]"
              @click="createChat"
            >
              <i class="fa-regular fa-pen-to-square w-5 text-center text-base"></i>
              <span>新聊天</span>
            </button>

            <div v-if="groupedSessions.length" class="space-y-5">
              <section v-for="group in groupedSessions" :key="group.label">
                <h3 class="mb-2 text-xs font-medium text-slate-500 dark:text-[#a9a9a9]">{{ group.label }}</h3>
                <div class="space-y-1">
                  <button
                    v-for="session in group.sessions"
                    :key="session.id"
                    type="button"
                    class="flex h-11 w-full items-center gap-3 rounded-lg px-2 text-left text-sm text-slate-800 transition-colors hover:bg-slate-100 dark:px-0 dark:text-white dark:hover:bg-white/[0.06]"
                    @click="selectChat(session)"
                  >
                    <i class="fa-regular fa-comment w-5 shrink-0 text-center text-base text-slate-500 dark:text-white"></i>
                    <span class="min-w-0 flex-1 overflow-hidden text-ellipsis whitespace-nowrap">
                      {{ session.title || '新对话' }}
                    </span>
                  </button>
                </div>
              </section>
            </div>

            <div v-else class="grid min-h-44 place-items-center text-center text-sm text-slate-500 dark:text-[#a9a9a9]">
              <div>
                <i class="fa-solid fa-magnifying-glass mb-3 block text-lg"></i>
                <p>{{ query ? '没有找到匹配的聊天' : '暂无聊天记录' }}</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.chat-search-backdrop-enter-active,
.chat-search-backdrop-leave-active {
  transition: opacity 0.16s ease;
}

.chat-search-backdrop-enter-from,
.chat-search-backdrop-leave-to {
  opacity: 0;
}

.chat-search-panel-enter-active,
.chat-search-panel-leave-active {
  transition: opacity 0.18s ease, transform 0.18s cubic-bezier(0.16, 1, 0.3, 1);
}

.chat-search-panel-enter-from,
.chat-search-panel-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}
</style>
