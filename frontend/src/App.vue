<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, provide, reactive, ref, watch } from 'vue'
import { fileKey, typesetMath as _typesetMathEl } from './utils.js'
import * as api from './api.js'
// 注意：移除了 AppHeader，因为现在由左侧边栏接管了全局导航功能
import StatusBar from './components/StatusBar.vue'
import StepIndicator from './components/StepIndicator.vue'
import FileList from './components/FileList.vue'
import FileUploader from './components/FileUploader.vue'
import QuestionList from './components/QuestionList.vue'
import ActionBar from './components/ActionBar.vue'
import ImageModal from './components/ImageModal.vue'
import ToastContainer from './components/ToastContainer.vue'
import Dashboard from './components/Dashboard.vue'
import CatLoading from './components/CatLoading.vue'
import ErrorBank from './components/ErrorBank.vue'
import ChatView from './components/ChatView.vue'
import SettingsView from './components/SettingsView.vue'

// ---- 视图路由控制 ----
const currentView = ref('workspace') // 'workspace' | 'workspace_review' | 'dashboard' | 'error-bank' | 'chat'

// ---- 主题 ----
const theme = ref('light')
const applyTheme = (nextTheme) => {
  theme.value = nextTheme === 'dark' ? 'dark' : 'light'
  const root = document.documentElement
  if (theme.value === 'dark') root.classList.add('dark')
  else root.classList.remove('dark')
}

const toggleTheme = async (btnEl) => {
  const nextTheme = theme.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem('theme', nextTheme)

  const prefersReduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const canTransition = !prefersReduce && typeof document.startViewTransition === 'function'
  if (!canTransition || !btnEl) {
    applyTheme(nextTheme)
    return
  }

  const rect = btnEl.getBoundingClientRect()
  const x = rect.left + rect.width / 2
  const y = rect.top + rect.height / 2
  const endRadius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y))

  const transition = document.startViewTransition(() => applyTheme(nextTheme))
  try {
    await transition.ready
    const duration = 1000
    const grow = [`circle(0px at ${x}px ${y}px)`, `circle(${endRadius}px at ${x}px ${y}px)`]
    document.documentElement.animate(
      { clipPath: grow },
      { duration, easing: 'cubic-bezier(0.2, 0, 0, 1)', pseudoElement: '::view-transition-new(root)' },
    )
    document.documentElement.animate(
      { opacity: [1, 0.98] },
      { duration, easing: 'linear', pseudoElement: '::view-transition-old(root)' },
    )
    await transition.finished
  } catch (_) {
    applyTheme(nextTheme)
  }
}
// ---- 系统状态 ----
const statusLoading = ref(true)
const systemStatus = ref(null)
const statusError = ref('')
const selectedModel = ref('')  // 选中的具体模型名称（如 "gpt-4o-mini"）

const providerOptions = computed(() => {
  const s = systemStatus.value
  return s && s.available_models ? s.available_models : []
})

// 从 selectedModel 反查 provider
const selectedProvider = computed(() => {
  for (const p of providerOptions.value) {
    if (p.models && p.models.includes(selectedModel.value)) return p.value
  }
  // 找不到时回退到首个已配置的 provider，而非硬编码 'openai'
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
    { key: 'ensexam', loading: true, label: 'EnsExam (未接入)' },
    { key: 'langsmith', loading: true, label: 'LangSmith (未接入)' },
  ]
  const s = systemStatus.value
  if (!s) return []
  const pills = []
  pills.push({ key: 'paddle', ok: !!s.paddleocr_configured, label: s.paddleocr_configured ? 'PaddleOCR' : 'PaddleOCR未配置' })
  pills.push({ key: 'ensexam', ok: false, label: 'EnsExam (未接入)', isPlaceholder: true })
  pills.push(s.langsmith_enabled
    ? { key: 'langsmith', ok: true, label: 'LangSmith追踪' }
    : { key: 'langsmith', ok: false, label: 'LangSmith (未接入)', isPlaceholder: true }
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

// ---- 步骤 & Toast ----
const step = ref(1)
const toasts = ref([])
let toastId = 0
const pushToast = (type, message, timeout = 2600) => {
  const id = ++toastId
  toasts.value = [{ id, type, message }, ...toasts.value].slice(0, 5)
  if (timeout > 0) window.setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, timeout)
}
provide('pushToast', pushToast)

// ---- AI 辅导对话 ----
const chatSessionId = ref(null)
const chatQuestion = ref(null)
const chatActive = ref(false)

// 答案录入弹窗（AI 辅导前置）
const answerModalOpen = ref(false)
const answerModalTarget = ref(null)
const answerModalText = ref('')
const answerModalSaving = ref(false)

const openChat = async (question) => {
  chatQuestion.value = question
  // 如果没有答案，先弹出答案录入弹窗
  if (!question.answer) {
    answerModalTarget.value = question
    answerModalText.value = ''
    answerModalOpen.value = true
    return
  }
  await doOpenChatSession(question)
}

const doOpenChatSession = async (question) => {
  try {
    const sessions = await api.fetchChatSessions(question.id)
    if (sessions.length) {
      chatSessionId.value = sessions[0].id
    } else {
      const session = await api.createChat(question.id)
      chatSessionId.value = session.id
    }
    chatActive.value = true
    currentView.value = 'chat'
  } catch (e) {
    pushToast('error', '打开对话失败: ' + (e instanceof Error ? e.message : String(e)))
  }
}

const saveAnswerAndChat = async () => {
  if (!answerModalTarget.value || answerModalSaving.value) return
  const text = answerModalText.value.trim()
  if (!text) { pushToast('error', '请输入答案/解析内容'); return }
  answerModalSaving.value = true
  try {
    await api.saveQuestionAnswer(answerModalTarget.value.id, text)
    answerModalTarget.value.answer = text
    answerModalOpen.value = false
    pushToast('success', '答案已保存')
    // 继续打开对话
    await doOpenChatSession(answerModalTarget.value)
  } catch (e) {
    pushToast('error', '保存答案失败: ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    answerModalSaving.value = false
  }
}

const backToErrorBank = () => {
  chatActive.value = false
  chatSessionId.value = null
  chatQuestion.value = null
  currentView.value = 'error-bank'
}

// ---- 图片弹窗 ----
const modalOpen = ref(false)
const modalSrc = ref('')
const modalScale = ref(1)
const openModal = (src) => {
  modalSrc.value = src || ''
  modalScale.value = 1
  modalOpen.value = !!src
  if (src) document.body.style.overflow = 'hidden'
}
const closeModal = () => {
  modalOpen.value = false
  modalSrc.value = ''
  modalScale.value = 1
  document.body.style.overflow = ''
}
const onKeydown = (e) => { if (e.key === 'Escape' && modalOpen.value) closeModal() }

// ---- 上传状态 ----
const uploadBusy = ref(false)
const uploadReady = ref(false)
const splitting = ref(false)
const splitCompleted = ref(false)

const pendingFiles = reactive([])
const fileProgress = reactive({})
const waitingKeys = reactive(new Set())
const uploadQueue = reactive([])
let activeXhr = null
let fakeProgressTimer = null
let fakeProgressKeys = []

const splitEnabled = computed(() => !splitting.value && !splitCompleted.value && uploadReady.value && !uploadBusy.value)
const exportEnabled = computed(() => splitCompleted.value && selectedIds.size > 0)

const stopFakeProgress = () => {
  if (fakeProgressTimer) {
    window.clearInterval(fakeProgressTimer)
    fakeProgressTimer = null
  }
  fakeProgressKeys = []
}
const setProgress = (key, p) => { fileProgress[key] = Math.max(0, Math.min(100, Number(p) || 0)) }

const startFakeProgress = (keys) => {
  stopFakeProgress()
  fakeProgressKeys = Array.from(keys || [])
  const tick = () => {
    if (!uploadBusy.value) { stopFakeProgress(); return }
    for (const key of fakeProgressKeys) {
      const current = Number(fileProgress[key] || 0)
      const cap = 82
      if (current >= cap) continue
      let inc = current < 55 ? 1 + Math.random() * 3 : current < 75 ? 0.4 + Math.random() * 1.1 : 0.08 + Math.random() * 0.25
      setProgress(key, Math.min(cap, current + inc))
    }
  }
  tick()
  fakeProgressTimer = window.setInterval(tick, 360)
}

const enqueueUpload = (files) => {
  const list = Array.from(files || [])
  if (!list.length) return
  if (splitCompleted.value || splitting.value) { pushToast('error', '已分割完成，请先重新开始'); return }
  for (const f of list) {
    const k = fileKey(f)
    if (pendingFiles.some(x => x.key === k)) continue
    pendingFiles.push({ key: k, file: f })
    setProgress(k, 0)
  }
  if (uploadBusy.value) {
    for (const f of list) waitingKeys.add(fileKey(f))
    uploadQueue.push(list)
    return
  }
  handleUpload(list)
}

const pumpUploadQueue = () => {
  if (uploadBusy.value || !uploadQueue.length) return
  const next = uploadQueue.shift()
  if (next && next.length) handleUpload(next)
}
const removePendingFile = async (key) => {
  if (!key || splitting.value || splitCompleted.value) return
  if (uploadBusy.value || uploadReady.value) { await doCancelFile(key); return }
  const idx = pendingFiles.findIndex(x => x.key === key)
  if (idx >= 0) pendingFiles.splice(idx, 1)
  delete fileProgress[key]
  waitingKeys.delete(key)
  for (let i = uploadQueue.length - 1; i >= 0; i--) {
    uploadQueue[i] = (uploadQueue[i] || []).filter(f => fileKey(f) !== key)
    if (!uploadQueue[i].length) uploadQueue.splice(i, 1)
  }
}

const doCancelFile = async (key) => {
  try {
    if (fakeProgressKeys.length) fakeProgressKeys = fakeProgressKeys.filter(k => k !== key)
    if (!fakeProgressKeys.length) stopFakeProgress()
    const data = await api.cancelFile(key)
    const idx = pendingFiles.findIndex(x => x.key === key)
    if (idx >= 0) pendingFiles.splice(idx, 1)
    delete fileProgress[key]
    waitingKeys.delete(key)
    questions.value = []
    selectedIds.clear()
    splitCompleted.value = false
    if (!pendingFiles.length) {
      uploadReady.value = false
      step.value = 1
    } else {
      step.value = 3
    }
    pushToast('success', data.message || '已撤销')
    if (!pendingFiles.length && activeXhr) {
      try { activeXhr.abort() } catch (_) {}
    }
  } catch (_) { pushToast('error', '撤销失败: 网络错误') }
}

const handleUpload = (files) => {
  const uploadFiles = Array.from(files || []).filter(f => pendingFiles.some(x => x.key === fileKey(f)))
  if (!uploadFiles.length) return
  uploadBusy.value = true
  step.value = 2
  const keys = uploadFiles.map(f => fileKey(f))
  for (const k of keys) waitingKeys.delete(k)
  startFakeProgress(keys)

  const formData = new FormData()
  for (const f of uploadFiles) {
    formData.append('files', f)
    formData.append('file_key', fileKey(f))
  }

  activeXhr = api.uploadFiles(formData, {
    onProgress: (ratio) => {
      const pct = Math.max(0, Math.min(95, ratio * 95))
      for (const k of keys) {
        if (pendingFiles.some(x => x.key === k)) setProgress(k, Math.max(fileProgress[k] || 0, pct))
      }
    },
    onSuccess: () => {
      stopFakeProgress()
      uploadBusy.value = false
      activeXhr = null
      for (const k of keys) {
        if (pendingFiles.some(x => x.key === k)) setProgress(k, 100)
      }
      uploadReady.value = pendingFiles.length > 0
      step.value = pendingFiles.length > 0 ? 3 : 1
      pushToast('success', `上传成功！本次新增 ${keys.length} 个文件，点击"开始分割题目"开始处理`)
      pumpUploadQueue()
    },
    onError: (msg) => {
      stopFakeProgress()
      uploadBusy.value = false
      activeXhr = null
      pushToast('error', msg)
      pumpUploadQueue()
    },
    onAbort: () => {
      stopFakeProgress()
      uploadBusy.value = false
      activeXhr = null
      pumpUploadQueue()
    },
  })
}

// ---- 题目 ----
const questions = ref([])
const selectedIds = reactive(new Set())
const questionListRef = ref(null)
const errorBankRef = ref(null)

const toggleQuestion = (id) => { selectedIds.has(id) ? selectedIds.delete(id) : selectedIds.add(id) }
const selectAll = () => { for (const q of questions.value) selectedIds.add(q.question_id) }
const deselectAll = () => { selectedIds.clear() }
const reorderQuestions = (oldIndex, newIndex) => {
  const arr = questions.value.slice()
  const [moved] = arr.splice(oldIndex, 1)
  arr.splice(newIndex, 0, moved)
  questions.value = arr
}

const typesetMath = async () => {
  await nextTick()
  const el = questionListRef.value?.questionsBoxEl
  await _typesetMathEl(el || undefined)
}
const doSplit = async () => {
  if (!uploadReady.value || splitting.value || splitCompleted.value) return
  splitting.value = true
  step.value = 3
  pushToast('info', '正在调用AI分割题目，请稍候...', 1800)
  try {
    const data = await api.splitQuestions(selectedProvider.value, selectedModel.value)
    questions.value = data.questions || []
    selectedIds.clear()
    if (data.warnings && data.warnings.length) {
      for (const w of data.warnings) pushToast('warning', w, 6000)
    }
    if (questions.value.length > 0) {
      splitCompleted.value = true
      step.value = 4
      if (!data.warnings || !data.warnings.length) {
        pushToast('success', `成功分割 ${questions.value.length} 道题目`)
      }
      await typesetMath()
      // 分割完成后自动翻页到核对页面（仅在用户仍在工作台时跳转）
      setTimeout(() => {
        if (currentView.value === 'workspace') {
          currentView.value = 'workspace_review'
        }
      }, 800)
    }
  } catch (e) {
    pushToast('error', '分割失败: ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    splitting.value = false
  }
}

const doExport = async () => {
  if (!selectedIds.size) { pushToast('error', '请至少选择一道题目！'); return }
  try {
    const data = await api.exportQuestions(Array.from(selectedIds))
    step.value = 5
    pushToast('success', `错题本导出成功！已保存到: ${data.output_path}`)
    let filename = 'wrongbook.md'
    if (data.output_path) {
      const parts = String(data.output_path).split(/[/\\]/)
      const last = parts[parts.length - 1]
      if (last) filename = last
    }
    const a = document.createElement('a')
    a.href = `/download/${encodeURIComponent(filename)}?t=${Date.now()}`
    a.download = filename
    a.style.display = 'none'
    document.body.appendChild(a)
    a.click()
    a.remove()
  } catch (e) {
    pushToast('error', '导出失败: ' + (e instanceof Error ? e.message : String(e)))
  }
}

const doSaveToDb = async () => {
  if (!selectedIds.size) { pushToast('error', '请至少选择一道题目！'); return }
  try {
    // 收集已录入的答案数据一并传给后端
    const answers = questions.value
      .filter(q => selectedIds.has(q.question_id) && (q.answer || q.user_answer))
      .map(q => ({ question_id: q.question_id, answer: q.answer || '', user_answer: q.user_answer || '' }))
    const data = await api.saveToDb(Array.from(selectedIds), answers)
    pushToast('success', data.message || '已导入错题库')
    errorBankRef.value?.refresh()
  } catch (e) {
    pushToast('error', '导入失败: ' + (e instanceof Error ? e.message : String(e)))
  }
}

const doReset = () => {
  uploadBusy.value = false
  uploadReady.value = false
  splitting.value = false
  splitCompleted.value = false
  pendingFiles.splice(0, pendingFiles.length)
  for (const k of Object.keys(fileProgress)) delete fileProgress[k]
  waitingKeys.clear()
  uploadQueue.splice(0, uploadQueue.length)
  questions.value = []
  selectedIds.clear()
  const configured = providerOptions.value.find(m => m.configured)
  selectedModel.value = configured ? configured.default_model : ''
  step.value = 1
  pushToast('success', '已重置')
}

watch(currentView, async (newView) => {
  if (newView === 'workspace_review') {
    // 等待翻页动画结束
    await nextTick()
    setTimeout(() => {
      questionListRef.value?.triggerTypeset?.()
    }, 650)
  }
})

// ---- 生命周期 ----
onMounted(() => {
  const saved = localStorage.getItem('theme')
  const initial = saved || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
  applyTheme(initial)
  doFetchStatus()
  document.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  stopFakeProgress()
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden bg-slate-50 font-sans text-slate-900 transition-colors duration-500 dark:bg-[#05050A] dark:text-slate-300">
    
    <!-- ================== PC端：左侧边栏导航 ================== -->
    <aside class="hidden w-64 flex-col justify-between border-r border-slate-200 bg-white transition-colors md:flex dark:border-white/5 dark:bg-[#0A0A0F]/80 z-20">
      <div>
        <!-- Logo 标题区 -->
        <div class="flex h-20 items-center gap-3 border-b border-slate-100 px-6 dark:border-white/5">
          <div class="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/30 dark:shadow-indigo-500/20">
            <i class="fa-solid fa-file-circle-check text-xl relative z-10"></i>
            <div class="absolute inset-0 animate-pulse rounded-xl bg-blue-400/20 blur-md"></div>
          </div>
          <span class="text-xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-700 to-indigo-700 dark:from-white dark:to-indigo-200">
            智卷系统
          </span>
        </div>

        <!-- 视图切换菜单 -->
        <nav class="mt-6 flex flex-col gap-1.5 px-4">
          <div class="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">核心功能</div>
          
          <button
            @click="currentView = splitCompleted ? 'workspace_review' : 'workspace'"
            class="group relative flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-bold transition-all duration-300"
            :class="currentView === 'workspace' || currentView === 'workspace_review' ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20 dark:bg-indigo-500 dark:shadow-indigo-500/20' : 'text-slate-600 hover:bg-slate-100 hover:text-blue-600 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-indigo-300'"
          >
            <i class="fa-solid fa-wand-magic-sparkles w-5 text-center text-lg transition-transform group-hover:scale-110"></i>
            <span>录题工作台</span>
            <div v-if="currentView === 'workspace' || currentView === 'workspace_review'" class="absolute right-2 h-1.5 w-1.5 rounded-full bg-white/60"></div>
          </button>

          <button
            @click="currentView = 'dashboard'"
            class="group relative flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-bold transition-all duration-300"
            :class="currentView === 'dashboard' ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20 dark:bg-indigo-500 dark:shadow-indigo-500/20' : 'text-slate-600 hover:bg-slate-100 hover:text-blue-600 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-indigo-300'"
          >
            <i class="fa-solid fa-chart-pie w-5 text-center text-lg transition-transform group-hover:scale-110"></i>
            <span>我的错题本</span>
            <div v-if="currentView === 'dashboard'" class="absolute right-2 h-1.5 w-1.5 rounded-full bg-white/60"></div>
          </button>

          <button
            @click="currentView = 'error-bank'"
            class="group relative flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-bold transition-all duration-300"
            :class="currentView === 'error-bank' ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20 dark:bg-indigo-500 dark:shadow-indigo-500/20' : 'text-slate-600 hover:bg-slate-100 hover:text-blue-600 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-indigo-300'"
          >
            <i class="fa-solid fa-database w-5 text-center text-lg transition-transform group-hover:scale-110"></i>
            <span>错题库</span>
            <div v-if="currentView === 'error-bank'" class="absolute right-2 h-1.5 w-1.5 rounded-full bg-white/60"></div>
          </button>
        </nav>
      </div>

      <!-- 底部控制与返回栏 -->
      <div class="space-y-1.5 border-t border-slate-100 p-4 dark:border-white/5">
        <button
          @click="currentView = 'settings'"
          class="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold transition-all"
          :class="currentView === 'settings' ? 'bg-blue-600 text-white shadow-md dark:bg-indigo-500 dark:shadow-[0_0_15px_rgba(99,102,241,0.3)]' : 'text-slate-600 hover:bg-slate-100 hover:text-blue-600 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-indigo-300'"
        >
          <i class="fa-solid fa-gear w-5 text-center text-lg"></i>
          系统设置
        </button>

        <button
          @click="(e) => toggleTheme(e.currentTarget)"
          class="flex w-full items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-600 transition-all hover:bg-slate-100 hover:text-blue-600 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-indigo-300"
        >
          <i class="fa-solid w-5 text-center text-lg transition-transform" :class="theme === 'dark' ? 'fa-sun text-amber-400 rotate-12' : 'fa-moon'"></i>
          <span>{{ theme === 'dark' ? '浅色模式' : '深色模式' }}</span>
        </button>

        <a
          href="/"
          class="flex w-full items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-500 transition-all hover:bg-slate-100 hover:text-blue-600 dark:text-slate-500 dark:hover:bg-white/5 dark:hover:text-indigo-300"
        >
          <i class="fa-solid fa-arrow-left-long w-5 text-center text-lg"></i>
          <span>返回介绍</span>
        </a>
      </div>
    </aside>

    <!-- ================== 移动端：底部 Tab 导航栏 ================== -->
    <nav class="fixed bottom-0 left-0 right-0 z-50 border-t border-slate-200 bg-white/90 pb-2 pt-2 backdrop-blur-xl md:hidden dark:border-white/10 dark:bg-[#0A0A0F]/90">
      <div class="flex justify-around">
        <button @click="currentView = splitCompleted ? 'workspace_review' : 'workspace'" class="flex flex-col items-center p-2 transition-colors" :class="currentView === 'workspace' || currentView === 'workspace_review' ? 'text-blue-600 dark:text-indigo-400' : 'text-slate-500 dark:text-slate-400'">
          <i class="fa-solid fa-wand-magic-sparkles mb-1 text-xl"></i>
          <span class="text-[10px] font-bold">工作台</span>
        </button>
        <button @click="currentView = 'dashboard'" class="flex flex-col items-center p-2 transition-colors" :class="currentView === 'dashboard' ? 'text-blue-600 dark:text-indigo-400' : 'text-slate-500 dark:text-slate-400'">
          <i class="fa-solid fa-chart-pie mb-1 text-xl"></i>
          <span class="text-[10px] font-bold">错题本</span>
        </button>
        <button @click="currentView = 'error-bank'" class="flex flex-col items-center p-2 transition-colors" :class="currentView === 'error-bank' ? 'text-blue-600 dark:text-indigo-400' : 'text-slate-500 dark:text-slate-400'">
          <i class="fa-solid fa-database mb-1 text-xl"></i>
          <span class="text-[10px] font-bold">错题库</span>
        </button>
        <button @click="currentView = 'settings'" class="flex flex-col items-center p-2 transition-colors" :class="currentView === 'settings' ? 'text-blue-600 dark:text-indigo-400' : 'text-slate-500 dark:text-slate-400'">
          <i class="fa-solid fa-gear mb-1 text-xl"></i>
          <span class="text-[10px] font-bold">设置</span>
        </button>
        <button @click="(e) => toggleTheme(e.currentTarget)" class="flex flex-col items-center p-2 text-slate-500 transition-colors dark:text-slate-400">
          <i class="fa-solid mb-1 text-xl" :class="theme === 'dark' ? 'fa-sun text-amber-400' : 'fa-moon'"></i>
          <span class="text-[10px] font-bold">主题</span>
        </button>
      </div>
    </nav>

    <!-- ================== 右侧主内容区 ================== -->
    <main class="relative z-10 flex-1 overflow-hidden pb-20 md:pb-0">
      
      <!-- 视图 1：录题工作台（分两页：上传解析页 / 题目核对页） -->
      <div v-show="currentView === 'workspace' || currentView === 'workspace_review'" class="relative h-full flex flex-col overflow-hidden">
        <!-- 专属背景光晕 (动态漂浮 - 极致柔和的高级感) -->
        <div class="pointer-events-none absolute inset-0 z-0 overflow-hidden">
          <div class="animate-blob absolute -top-[10%] left-[-10%] h-[50vw] w-[50vw] rounded-full bg-blue-400/[0.12] mix-blend-multiply blur-[120px] transition-colors duration-1000 dark:bg-indigo-600/20 dark:mix-blend-screen"></div>
          <div class="animate-blob animation-delay-4000 absolute -bottom-[10%] right-[-10%] h-[45vw] w-[45vw] rounded-full bg-indigo-300/[0.15] mix-blend-multiply blur-[100px] transition-colors duration-1000 dark:bg-fuchsia-600/20 dark:mix-blend-screen"></div>
          <div class="animate-blob animation-delay-2000 absolute left-[15%] top-[25%] h-[35vw] w-[35vw] rounded-full bg-cyan-200/[0.12] mix-blend-multiply blur-[110px] transition-colors duration-1000 dark:bg-blue-500/10 dark:mix-blend-screen"></div>
        </div>

        <div class="container relative z-10 mx-auto flex h-full max-w-5xl flex-col px-4 py-4 sm:px-8 sm:py-6">
          <Transition name="flip" mode="out-in">
            <!-- 第一页：录题与分析 -->
            <div v-if="currentView === 'workspace'" key="upload" class="flex flex-1 flex-col">
              <div class="mb-4 flex flex-col items-start gap-2 pl-2 sm:pl-0 md:flex-row md:items-center md:justify-between shrink-0">
                <div>
                  <div class="mb-1 flex items-center gap-2">
                    <span class="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-blue-700 dark:bg-indigo-500/20 dark:text-indigo-300">
                      Baidu Powered
                    </span>
                    <span class="h-1 w-1 rounded-full bg-slate-300 dark:bg-slate-600"></span>
                    <span class="text-[9px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">v2.0</span>
                  </div>
                  <h2 class="text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl dark:text-white">
                    智能录入与分析
                  </h2>
                </div>
              </div>

              <div class="main-content relative flex flex-1 flex-col bg-transparent">
                <StatusBar
                  class="border-b border-slate-200/60 pb-6 dark:border-white/5"
                  :status-loading="statusLoading"
                  :status-error="statusError"
                  :status-pills="statusPills"
                  :provider-options="providerOptions"
                  :selected-model="selectedModel"
                  :disabled="splitting || splitCompleted"
                  @update:selected-model="(v) => selectedModel = v"
                />

                <div class="flex-1 overflow-y-auto pr-2 custom-scrollbar flex flex-col space-y-8 py-6">
                  <StepIndicator :step="step" class="border-b border-slate-200/60 pb-8 dark:border-white/5" />

                  <FileList
                    :pending-files="pendingFiles"
                    :file-progress="fileProgress"
                    :waiting-keys="waitingKeys"
                    :upload-busy="uploadBusy"
                    :upload-ready="uploadReady"
                    :splitting="splitting"
                    :split-completed="splitCompleted"
                    @remove-file="removePendingFile"
                  />

                  <FileUploader
                    class="transition-all duration-500"
                    :class="questions.length === 0 ? 'flex-1' : 'border-b border-slate-200/60 pb-8 dark:border-white/5'"
                    :pending-files="pendingFiles"
                    :file-progress="fileProgress"
                    :waiting-keys="waitingKeys"
                    :upload-busy="uploadBusy"
                    :upload-ready="uploadReady"
                    :splitting="splitting"
                    :split-completed="splitCompleted"
                    :expand="questions.length === 0"
                    @upload="enqueueUpload"
                    @remove-file="removePendingFile"
                  />
                </div>

                <ActionBar
                  class="shrink-0 border-t border-slate-200/60 pt-6 dark:border-white/5"
                  :split-enabled="splitEnabled"
                  :export-enabled="false"
                  :splitting="splitting"
                  :split-completed="splitCompleted"
                  @split="doSplit"
                />
              </div>
            </div>

            <!-- 第二页：解析结果核对 -->
            <div v-else key="review" class="flex flex-1 flex-col overflow-hidden">
              <div class="mb-4 flex items-center justify-between pl-2 sm:pl-0 shrink-0">
                <div class="flex items-center gap-4">
                  <button 
                    @click="() => { doReset(); currentView = 'workspace' }"
                    class="group flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200/60 bg-white/60 text-slate-500 backdrop-blur-md transition-all hover:border-blue-500/50 hover:bg-white hover:text-blue-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-400 dark:hover:border-indigo-500/50 dark:hover:text-indigo-300"
                  >
                    <i class="fa-solid fa-arrow-left-long transition-transform group-hover:-translate-x-1"></i>
                  </button>
                  <div>
                    <h2 class="text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl dark:text-white">
                      题目数据核对
                    </h2>
                    <p class="text-xs font-bold text-slate-400 dark:text-slate-500 mt-0.5">请确认解析结果的准确性并进行导出或存档</p>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <span class="rounded-full bg-blue-100 px-3 py-1 text-[10px] font-black text-blue-700 dark:bg-indigo-500/20 dark:text-indigo-300">
                    {{ questions.length }} 道题目已解析
                  </span>
                </div>
              </div>

              <div class="flex-1 overflow-y-auto pr-2 custom-scrollbar py-2">
                <QuestionList
                  ref="questionListRef"
                  :questions="questions"
                  :selected-ids="selectedIds"
                  @toggle-select="toggleQuestion"
                  @select-all="selectAll"
                  @deselect-all="deselectAll"
                  @open-image="openModal"
                  @reorder="reorderQuestions"
                />
              </div>

              <ActionBar
                class="shrink-0 border-t border-slate-200/60 pt-6 dark:border-white/5"
                :split-enabled="false"
                :export-enabled="exportEnabled"
                :splitting="false"
                :split-completed="true"
                @export="doExport"
                @save-to-db="doSaveToDb"
              />
            </div>
          </Transition>
        </div>
      </div>

      <!-- AI 分割任务全局遮罩 -->
      <CatLoading v-if="splitting && (currentView === 'workspace' || currentView === 'workspace_review')" />

      <!-- 视图 2：我的错题本数据看板 (完全独立组件) -->
      <Dashboard
        v-show="currentView === 'dashboard'"
        :theme="theme"
        :visible="currentView === 'dashboard'"
        @go-workspace="currentView = 'workspace'"
        @push-toast="pushToast"
        @open-image="openModal"
        @start-chat="openChat"
      />

      <!-- 视图 3：错题库 -->
      <ErrorBank
        ref="errorBankRef"
        v-show="currentView === 'error-bank'"
        :theme="theme"
        :visible="currentView === 'error-bank'"
        @go-workspace="currentView = 'workspace'"
        @push-toast="pushToast"
        @open-image="openModal"
        @start-chat="openChat"
      />

      <!-- 视图 4：系统设置 -->
      <SettingsView
        v-show="currentView === 'settings'"
        :visible="currentView === 'settings'"
        @saved="doFetchStatus"
      />

      <!-- 视图 5：AI 辅导对话 -->
      <div v-show="currentView === 'chat'" class="h-full">
        <ChatView
          v-if="chatActive"
          :session-id="chatSessionId"
          :question="chatQuestion"
          :model-provider="selectedProvider"
          :model-name="selectedModel"
          @back="backToErrorBank"
        />
      </div>
    </main>

    <!-- 全局弹窗与通知 -->
    <Teleport to="body">
      <ImageModal
        :open="modalOpen"
        :src="modalSrc"
        :scale="modalScale"
        @close="closeModal"
        @update:scale="(s) => modalScale = s"
      />
      <ToastContainer :toasts="toasts" />

      <!-- 答案录入弹窗（AI 辅导前置） -->
      <div v-if="answerModalOpen" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm dark:bg-black/60" @click="answerModalOpen = false"></div>
        <div class="relative w-full max-w-lg rounded-2xl border border-slate-200/60 bg-white p-6 shadow-2xl dark:border-white/10 dark:bg-slate-900">
          <h3 class="mb-1 text-lg font-bold text-slate-900 dark:text-white">录入答案</h3>
          <p class="mb-4 text-xs text-slate-500 dark:text-slate-400">
            AI 辅导需要正确答案作为参考。支持 Markdown 格式，数学公式使用 LaTeX（$..$ 行内，$$...$$ 独占行）
          </p>
          <textarea
            v-model="answerModalText"
            rows="10"
            placeholder="在此粘贴或输入答案/解析..."
            class="w-full resize-none rounded-xl border border-slate-200/80 bg-slate-50 px-4 py-3 font-mono text-sm text-slate-800 placeholder-slate-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-white/10 dark:bg-slate-800 dark:text-slate-200"
          ></textarea>
          <div class="mt-4 flex justify-end gap-3">
            <button
              @click="answerModalOpen = false"
              class="rounded-xl border border-slate-200/60 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              取消
            </button>
            <button
              @click="saveAnswerAndChat"
              :disabled="answerModalSaving"
              class="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-bold text-white shadow-sm transition-all hover:bg-blue-700 disabled:opacity-50 dark:bg-indigo-500 dark:hover:bg-indigo-600"
            >
              {{ answerModalSaving ? '保存中...' : '保存并开始辅导' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style>
/* 自定义背景光晕动画 - 极致性能优化版 */
@keyframes blob {
  0% { transform: translate3d(0, 0, 0) scale(1); opacity: 0.6; }
  33% { transform: translate3d(80px, -120px, 0) scale(1.2); opacity: 0.8; }
  66% { transform: translate3d(-60px, 60px, 0) scale(0.8); opacity: 0.3; }
  100% { transform: translate3d(0, 0, 0) scale(1); opacity: 0.6; }
}

.animate-blob {
  animation: blob 30s infinite alternate ease-in-out;
  will-change: transform, opacity;
}

.animation-delay-2000 {
  animation-delay: 2s;
}

.animation-delay-4000 {
  animation-delay: 4s;
}

::view-transition-old(root),
::view-transition-new(root) {
  animation: none;
  mix-blend-mode: normal;
}

/* 翻页动画效果 */
.flip-enter-active {
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}
.flip-leave-active {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
.flip-enter-from {
  opacity: 0;
  transform: translateX(30px) scale(0.98);
}
.flip-leave-to {
  opacity: 0;
  transform: translateX(-30px) scale(0.98);
}
</style>