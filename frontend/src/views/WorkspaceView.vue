<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, provide, reactive, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { fileKey, typesetMath as _typesetMathEl } from '../utils.js'
import * as api from '../api.js'
import { useAuth } from '../composables/useAuth.js'
import { usePageTransition } from '../composables/usePageTransition.js'
// 注意：移除了 AppHeader，因为现在由左侧边栏接管了全局导航功能
import BrandLogo from '../components/BrandLogo.vue'
import ContentPanel from '../components/ContentPanel.vue'
import StatusBar from '../components/StatusBar.vue'
import StepIndicator from '../components/StepIndicator.vue'
import FileList from '../components/FileList.vue'
import FileUploader from '../components/FileUploader.vue'
import QuestionList from '../components/QuestionList.vue'
import ActionBar from '../components/ActionBar.vue'
import SelectionPanel from '../components/SelectionPanel.vue'
import SplitLoading from '../components/SplitLoading.vue'
import ImageModal from '../components/ImageModal.vue'
import ToastContainer from '../components/ToastContainer.vue'
import Dashboard from '../components/Dashboard.vue'
import ReviewView from '../components/ReviewView.vue'
import ErrorBank from '../components/ErrorBank.vue'
import ChatView from '../components/ChatView.vue'
import SettingsView from '../components/SettingsView.vue'
import SplitHistory from '../components/SplitHistory.vue'
import NoteView from '../components/NoteView.vue'
import ChatPage from '../components/ChatPage.vue'

// ---- 认证状态 ----
const { currentUser } = useAuth()
const router = useRouter()
const route = useRoute()

const handleLogout = async () => {
  try {
    await fetch('/api/auth/logout', { method: 'POST' })
  } catch (_) {}
  currentUser.value = null
  router.push('/auth')
}

const navigateToHome = () => {
  document.body.style.transition = 'opacity 0.25s ease, transform 0.25s ease'
  document.body.style.opacity = '0'
  document.body.style.transform = 'translateY(-6px)'
  setTimeout(() => { window.location.href = '/' }, 260)
}

// ---- 视图路由控制 ----
const VIEW_TO_PATH = {
  workspace: '/app/workspace',
  workspace_review: '/app/workspace/review',
  dashboard: '/app/dashboard',
  review: '/app/review',
  'error-bank': '/app/error-bank',
  notes: '/app/notes',
  'ai-chat': '/app/ai-chat',
  settings: '/app/settings',
  'split-history': '/app/split-history',
  chat: '/app/chat',
}

const WORKSPACE_VIEWS = new Set(['workspace', 'workspace_review', 'split-history'])

const lastWorkspaceView = ref('workspace')

// ── 侧边栏分组折叠 ──
const NAV_GROUPS = [
  {
    label: null, // 无标题的顶级导航
    items: [
      { id: 'workspace', label: '录入工作台', icon: 'fa-wand-magic-sparkles', match: (v) => WORKSPACE_VIEWS.has(v) },
    ],
  },
  {
    label: '数据',
    collapsible: true,
    items: [
      { id: 'dashboard', label: '数据面板', icon: 'fa-chart-pie', match: (v) => v === 'dashboard' },
      { id: 'error-bank', label: '错题库', icon: 'fa-database', match: (v) => v === 'error-bank' },
      { id: 'notes', label: '笔记库', icon: 'fa-book-open', match: (v) => v === 'notes' },
    ],
  },
  {
    label: '更多',
    collapsible: true,
    items: [
      { id: 'review-disabled', label: '刷题', icon: 'fa-clock-rotate-left', disabled: true },
    ],
  },
]

const collapsedGroups = ref({})
const chatCollapsed = ref(false)

// ── 导航指示器动画（基于 DOM 实际位置） ──
const navRef = ref(null)
const navBtnRefs = ref({})
const indicatorStyle = ref({ opacity: 0, top: '0px', height: '0px' })
const indicatorTransition = ref(true)

// ── 对话区指示器 ──
const chatListRef = ref(null)
const chatBtnRefs = ref({})
const chatIndicatorStyle = ref({ opacity: 0, top: '0px', height: '0px' })
const chatIndicatorTransition = ref(true)

function updateIndicator(animate = true) {
  const cv = currentView.value
  const isChat = cv === 'ai-chat'

  // === 导航组指示器 ===
  if (isChat) {
    // 切到对话时，导航指示器隐藏
    indicatorTransition.value = animate
    indicatorStyle.value = { opacity: 0, top: '0px', height: '0px' }
  } else {
    let matchId = null
    let matchGroupIdx = -1
    for (let gi = 0; gi < NAV_GROUPS.length; gi++) {
      for (const item of NAV_GROUPS[gi].items) {
        if (item.match && item.match(cv)) { matchId = item.id; matchGroupIdx = gi; break }
      }
      if (matchId) break
    }
    if (matchGroupIdx >= 0 && collapsedGroups.value[matchGroupIdx]) {
      indicatorTransition.value = false
      indicatorStyle.value = { opacity: 0, top: '0px', height: '0px' }
    } else if (!matchId || !navBtnRefs.value[matchId] || !navRef.value) {
      indicatorTransition.value = animate
      indicatorStyle.value = { opacity: 0, top: '0px', height: '0px' }
    } else {
      indicatorTransition.value = animate
      const navRect = navRef.value.getBoundingClientRect()
      const btnRect = navBtnRefs.value[matchId].getBoundingClientRect()
      indicatorStyle.value = {
        opacity: 1,
        top: (btnRect.top - navRect.top) + 'px',
        height: btnRect.height + 'px',
      }
    }
  }

  // === 对话区指示器 ===
  if (!isChat || !activeAiChatId.value) {
    chatIndicatorTransition.value = animate
    chatIndicatorStyle.value = { opacity: 0, top: '0px', height: '0px' }
  } else {
    const btnEl = chatBtnRefs.value[activeAiChatId.value]
    if (!btnEl || !chatListRef.value) {
      chatIndicatorTransition.value = animate
      chatIndicatorStyle.value = { opacity: 0, top: '0px', height: '0px' }
    } else {
      chatIndicatorTransition.value = animate
      const listRect = chatListRef.value.getBoundingClientRect()
      const btnRect = btnEl.getBoundingClientRect()
      chatIndicatorStyle.value = {
        opacity: 1,
        top: (btnRect.top - listRect.top) + 'px',
        height: btnRect.height + 'px',
      }
    }
  }
}

const currentView = computed({
  get() {
    const view = route.params.view || 'workspace'
    const subview = route.params.subview
    if (view === 'workspace' && subview === 'review') return 'workspace_review'
    return view
  },
  set(view) {
    const path = VIEW_TO_PATH[view]
    if (path && route.path !== path) router.push(path)
  },
})

watch(currentView, (v) => {
  if (WORKSPACE_VIEWS.has(v)) lastWorkspaceView.value = v
  nextTick(updateIndicator)
})
watch(collapsedGroups, () => {
  updateIndicator(false)
  nextTick(() => updateIndicator(false))
}, { deep: true })

// activeAiChatId 定义在后面，延迟注册 watch
onMounted(() => {
  watch(() => activeAiChatId.value, () => nextTick(updateIndicator))
})


// ---- 状态定义 ----
const { loading: globalLoading } = usePageTransition()

import { useTheme } from '../composables/useTheme.js'
const { isDark, toggleTheme, initTheme } = useTheme()
// 兼容旧代码中 theme 的引用
const theme = computed(() => isDark.value ? 'dark' : 'light')
const userMenuOpen = ref(false)
// ---- 系统状态 ----
const statusLoading = ref(true)
const systemStatus = ref(null)
const statusError = ref('')
const selectedModel = ref('')  // 选中的具体模型名称（如 "gpt-4o-mini"）

const providerOptions = computed(() => {
  const s = systemStatus.value
  return s && s.available_models ? s.available_models : []
})

// 是否有可用模型
const hasConfiguredModel = computed(() => providerOptions.value.some(p => p.configured))

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

// ---- 步骤 & Toast ----
const step = ref(1)

// 步骤 tab 数据（给 ContentPanel header 用）
const examStepLabels = ['上传', 'OCR', '分割', '导出']
const noteStepLabels = ['上传', 'OCR', '整理', '保存']
const workspaceSteps = computed(() => {
  const labels = uploadMode.value === 'note' ? noteStepLabels : examStepLabels
  return labels.map((label, i) => ({
    label,
    done: i + 1 < step.value,
    active: i + 1 === step.value,
  }))
})
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

// ---- 独立 AI 对话 ----
const aiChatSessions = ref([])
const activeAiChatId = ref(null)

async function loadAiChatSessions() {
  try {
    const data = await api.fetchMyChatSessions({ limit: 50 })
    aiChatSessions.value = data.sessions || []
  } catch (_) {}
}

async function createAiChat() {
  try {
    const session = await api.createIndependentChat('新对话')
    aiChatSessions.value.unshift(session)
    activeAiChatId.value = session.id
    if (currentView.value !== 'ai-chat') currentView.value = 'ai-chat'
  } catch (e) {
    pushToast('error', e.message)
  }
}

function selectAiChat(s) {
  activeAiChatId.value = s.id
  if (currentView.value !== 'ai-chat') currentView.value = 'ai-chat'
}

async function onAiChatTitleUpdated(sessionId, title) {
  const s = aiChatSessions.value.find(s => s.id === sessionId)
  if (s && s.title === '新对话') {
    s.title = title
    try { await api.updateChatTitle(sessionId, title) } catch (_) {}
  }
}

const chatMenuOpenId = ref(null)
const renamingChatId = ref(null)
const renameText = ref('')

function toggleChatMenu(id) {
  chatMenuOpenId.value = chatMenuOpenId.value === id ? null : id
}
function closeChatMenu() {
  chatMenuOpenId.value = null
}

async function startRenameChat(s) {
  chatMenuOpenId.value = null
  renamingChatId.value = s.id
  renameText.value = s.title
  await nextTick()
  const input = document.querySelector('input[data-rename-input]')
  if (input) { input.focus(); input.selectionStart = input.selectionEnd = input.value.length }
}

async function confirmRenameChat(s) {
  const title = renameText.value.trim()
  if (title && title !== s.title) {
    try {
      await api.updateChatTitle(s.id, title)
      s.title = title
    } catch (e) {
      pushToast('error', e.message)
    }
  }
  renamingChatId.value = null
}

async function deleteAiChat(id) {
  try {
    await api.deleteChat(id)
    aiChatSessions.value = aiChatSessions.value.filter(s => s.id !== id)
    if (activeAiChatId.value === id) activeAiChatId.value = null
  } catch (e) {
    pushToast('error', e.message)
  }
}

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
const uploadMode = ref('exam')  // 'exam'（试卷分割）或 'note'（笔记整理）
const uploadBusy = ref(false)
const uploadReady = ref(false)
const splitting = ref(false)
const splitCompleted = ref(false)
const showSplitHistory = ref(false)

// ── 背景星星 ──
const bgStars = (() => {
  const list = []
  for (let i = 0; i < 50; i++) {
    list.push({
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: 0.5 + Math.random() * 2,
      opacity: 0.1 + Math.random() * 0.4,
      duration: 2 + Math.random() * 4,
      delay: Math.random() * 5,
    })
  }
  return list
})()
const eraseEnabled = ref(true)

const pendingFiles = reactive([])
const fileProgress = reactive({})
const waitingKeys = reactive(new Set())
const uploadQueue = reactive([])
let activeXhr = null
let fakeProgressTimer = null
let fakeProgressKeys = []

const splitEnabled = computed(() => !splitting.value && !splitCompleted.value && uploadReady.value && !uploadBusy.value && hasConfiguredModel.value)
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
      step.value = 2
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
      step.value = pendingFiles.length > 0 ? 2 : 1
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
const noteViewRef = ref(null)

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

  // 笔记模式：走笔记整理流程
  if (uploadMode.value === 'note') {
    await doNoteOrganize()
    return
  }

  // 试卷模式：走原有分割流程
  splitting.value = true
  step.value = 3
  currentView.value = 'workspace_review'
  pushToast('info', '正在调用AI分割题目，请稍候...', 1800)
  try {
    const data = await api.splitQuestions(selectedProvider.value, selectedModel.value, { erase: eraseEnabled.value })
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

const doNoteOrganize = async () => {
  splitting.value = true
  step.value = 3
  pushToast('info', '正在调用AI整理笔记，请稍候...', 3000)
  try {
    // 收集已上传文件，构建 FormData 发给笔记 API
    const formData = new FormData()
    for (const pf of pendingFiles) {
      if (pf.file) formData.append('files', pf.file)
    }
    formData.append('model_provider', selectedProvider.value)
    if (selectedModel.value) formData.append('model_name', selectedModel.value)

    const result = await new Promise((resolve, reject) => {
      api.createNote(formData, {
        onSuccess: (data) => resolve(data),
        onError: (msg) => reject(new Error(msg)),
      })
    })

    splitCompleted.value = true
    step.value = 4
    pushToast('success', '笔记整理完成！')

    // 跳转到笔记页面查看
    setTimeout(() => {
      currentView.value = 'notes'
    }, 800)
  } catch (e) {
    pushToast('error', '笔记整理失败: ' + (e instanceof Error ? e.message : String(e)))
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

const handleLoadRecord = (qs, record) => {
  questions.value = qs || []
  selectedIds.clear()
  splitCompleted.value = true
  step.value = 4
  currentView.value = 'workspace_review'
  pushToast('success', `已加载「${record?.subject || '历史记录'}」的 ${qs.length} 道题目`)
  nextTick(() => typesetMath())
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
    await nextTick()
    setTimeout(() => {
      questionListRef.value?.triggerTypeset?.()
    }, 650)
  }
  if (newView === 'ai-chat') {
    loadAiChatSessions()
  }
})

// ---- 页面加载动画 ----
const pageLoading = ref(true)

// ---- 生命周期 ----
onMounted(() => {
  initTheme()
  document.addEventListener('keydown', onKeydown)
  document.addEventListener('click', closeChatMenu)
  loadAiChatSessions()
  nextTick(updateIndicator)

  // 刷新时如果落在 /workspace/review 但没有数据，重定向回上传页
  if (currentView.value === 'workspace_review' && !splitCompleted.value) {
    router.replace('/app/workspace')
  }
  
  // 延迟系统状态检查，直到入场加载动画完全结束
  // 这能确保在动画过程中不会因为网络请求导致掉帧，且视觉上更连贯
  setTimeout(() => {
    pageLoading.value = false
    
    // 如果全局 loading 已经结束（说明动画已经淡出或不需要淡出），开始检查
    if (!globalLoading.value) {
      doFetchStatus()
    } else {
      // 否则，监听全局 loading 状态，待其变为 false（即 AppLoading 彻底消失）后触发
      const unwatch = watch(globalLoading, (val) => {
        if (!val) {
          doFetchStatus()
          unwatch()
        }
      })
    }
  }, 2000)
})

onBeforeUnmount(() => {
  stopFakeProgress()
  document.removeEventListener('keydown', onKeydown)
  document.removeEventListener('click', closeChatMenu)
})
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden bg-[#0c0c0e] font-sans text-slate-300 relative">

    <!-- 全局背景装饰（Linear 风格） -->
    <div class="fixed inset-0 z-0 pointer-events-none">
      <!-- 左上角光圈 -->
      <div class="absolute -top-[20%] -left-[10%] w-[600px] h-[600px] rounded-full" style="background: radial-gradient(circle, rgba(129,115,223,0.06) 0%, transparent 70%);"></div>
      <!-- 噪点纹理 -->
      <div class="absolute inset-0 opacity-[0.04]" style="background-image: url(&quot;data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E&quot;); background-size: 256px 256px;"></div>
      <!-- 闪烁星星 -->
      <div
        v-for="(s, i) in bgStars"
        :key="i"
        class="absolute rounded-full bg-white ws-star"
        :style="{
          left: s.left + '%',
          top: s.top + '%',
          width: s.size + 'px',
          height: s.size + 'px',
          '--star-opacity': s.opacity,
          animationDuration: s.duration + 's',
          animationDelay: s.delay + 's',
        }"
      ></div>
    </div>

    <Transition name="ws-loading-fade">
      <div v-if="pageLoading" class="fixed inset-0 z-[200] flex flex-col items-center justify-center gap-8 bg-[#0A0A0F]">
        <BrandLogo size="lg" breathe />
        <div class="w-48">
          <div class="h-0.5 w-full rounded-full bg-white/10 overflow-hidden">
            <div class="h-full rounded-full ws-loading-bar" style="background: linear-gradient(to right, rgba(129,115,223,0.8), rgba(99,87,199,0.8));"></div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ================== PC端：左侧边栏导航 ================== -->
    <aside class="hidden w-64 flex-col justify-between md:flex z-20">
      <div>
        <!-- Logo 标题区 -->
        <div class="flex h-20 items-center justify-between px-4 py-6">
          <button @click="navigateToHome" class="flex min-w-0 items-center gap-2 rounded-md px-1 py-1 hover:bg-white/[0.04] transition-colors" title="返回介绍页">
            <BrandLogo size="sm" />
            <span class="text-sm font-medium text-[#f7f8f8]">智卷错题本</span>
          </button>
          <div class="flex items-center gap-1">
            <button @click="currentView = 'settings'" class="flex h-7 w-7 items-center justify-center rounded-md text-[#62666d] hover:bg-white/[0.04] hover:text-[#8a8f98] transition-colors" title="系统设置">
              <i class="fa-solid fa-gear text-xs"></i>
            </button>
            <button @click="handleLogout()" class="flex h-7 w-7 items-center justify-center rounded-md border border-white/[0.08] text-[#62666d] hover:bg-white/[0.04] hover:text-[#8a8f98] transition-colors" title="退出登录">
              <i class="fa-solid fa-right-from-bracket text-xs"></i>
            </button>
          </div>
        </div>

        <!-- 视图切换菜单 — Linear 分组折叠 -->
        <nav ref="navRef" class="flex flex-col gap-1.5 px-4 relative">
          <!-- 滑动指示器 -->
          <div
            class="absolute left-4 right-4 z-0 rounded-lg overflow-hidden brand-btn"
            :class="indicatorTransition ? 'transition-all duration-300 ease-out' : ''"
            :style="indicatorStyle"
          >
          </div>

          <template v-for="(group, gi) in NAV_GROUPS" :key="gi">
            <!-- 分组标题（可折叠） -->
            <button
              v-if="group.label"
              @click="group.collapsible && (collapsedGroups[gi] = !collapsedGroups[gi])"
              class="flex items-center gap-1 px-3 pt-4 pb-1 text-xs font-medium uppercase tracking-[0.15em] text-[#62666d] hover:text-[#8a8f98] transition-colors"
              :class="group.collapsible ? 'cursor-pointer' : 'cursor-default'"
            >
              <span>{{ group.label }}</span>
              <i
                v-if="group.collapsible"
                class="fa-solid fa-play text-[8px] text-[#62666d] transition-transform duration-200"
                :class="collapsedGroups[gi] ? '' : 'rotate-90'"
              ></i>
            </button>

            <!-- 分组内容（grid 折叠动画） -->
            <div class="grid transition-[grid-template-rows] duration-200 ease-out" :class="collapsedGroups[gi] ? 'grid-rows-[0fr]' : 'grid-rows-[1fr]'">
            <div class="overflow-hidden">
            <div class="flex flex-col gap-1">
              <template v-for="item in group.items" :key="item.id">
                <!-- 禁用项 -->
                <button
                  v-if="item.disabled"
                  disabled
                  class="flex items-center justify-between rounded-lg px-3 py-3 text-sm cursor-not-allowed text-[#62666d]"
                >
                  <div class="flex items-center gap-3">
                    <i class="fa-solid w-4 text-center text-sm" :class="item.icon"></i>
                    <span>{{ item.label }}</span>
                  </div>
                  <span class="text-[10px] font-medium px-2 py-0.5 rounded-md bg-white/[0.04] text-[#62666d]">敬请期待</span>
                </button>
                <!-- 普通项 -->
                <button
                  v-else
                  :ref="el => navBtnRefs[item.id] = el"
                  @click="currentView = (item.id === 'workspace' ? lastWorkspaceView : item.id)"
                  class="group relative z-10 flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-200"
                  :class="item.match(currentView)
                    ? 'text-white'
                    : 'text-[#8a8f98] hover:bg-white/[0.04] hover:text-[#d0d6e0]'"
                >
                  <i class="fa-solid w-4 text-center text-sm" :class="item.icon"></i>
                  <span>{{ item.label }}</span>
                </button>
              </template>
            </div>
            </div>
            </div>
          </template>
        </nav>

      </div>

      <!-- AI 对话历史列表 -->
      <div class="flex-1 min-h-0 flex flex-col mt-4 px-4">
        <div class="flex items-center justify-between px-3 pt-4 pb-2">
          <button @click="chatCollapsed = !chatCollapsed" class="flex items-center gap-1 text-xs font-medium uppercase tracking-[0.15em] text-[#62666d] hover:text-[#8a8f98] transition-colors cursor-pointer">
            <span>对话</span>
            <i class="fa-solid fa-play text-[8px] text-[#62666d] transition-transform duration-200" :class="chatCollapsed ? '' : 'rotate-90'"></i>
          </button>
          <button @click="createAiChat" class="text-[#8a8f98] hover:text-[#d0d6e0] transition-colors">
            <i class="fa-solid fa-plus text-[10px]"></i>
          </button>
        </div>
        <!-- 折叠动画 -->
        <div class="grid transition-[grid-template-rows] duration-200 ease-out" :class="chatCollapsed ? 'grid-rows-[0fr]' : 'grid-rows-[1fr]'">
        <div class="overflow-hidden">
        <div ref="chatListRef" class="flex-1 overflow-y-auto pb-2 custom-scrollbar relative" @click="chatMenuOpenId = null">
          <!-- 对话区滑动指示器 -->
          <div
            class="absolute left-0 right-0 z-0 rounded-md overflow-hidden brand-btn"
            :class="chatIndicatorTransition ? 'transition-all duration-300 ease-out' : ''"
            :style="chatIndicatorStyle"
          >
          </div>

          <div v-if="aiChatSessions.length === 0" class="px-3 py-4 text-center text-xs text-[#62666d]">
            暂无对话
          </div>
          <div
            v-for="s in aiChatSessions"
            :key="s.id"
            :ref="el => chatBtnRefs[s.id] = el"
            class="group relative z-10 flex items-center gap-2 px-3 py-1.5 rounded-md mb-px cursor-pointer transition-colors"
            :class="activeAiChatId === s.id && currentView === 'ai-chat'
              ? 'text-white'
              : 'text-[#8a8f98] hover:bg-white/[0.04] hover:text-[#d0d6e0]'"
            @click="renamingChatId !== s.id && selectAiChat(s)"
          >
            <i class="fa-solid fa-message text-[10px] shrink-0" :class="activeAiChatId === s.id && currentView === 'ai-chat' ? 'text-white/60' : 'text-[#62666d]'"></i>

            <!-- 重命名输入框 -->
            <input
              v-if="renamingChatId === s.id"
              v-model="renameText"
              data-rename-input
              @click.stop
              @keydown.enter="confirmRenameChat(s)"
              @keydown.escape="renamingChatId = null"
              @blur="confirmRenameChat(s)"
              class="flex-1 min-w-0 bg-transparent text-xs outline-none border-b border-white/[0.12] py-0.5 text-[#f7f8f8]"
            />
            <span v-else class="relative z-10 flex-1 truncate text-xs">{{ s.title }}</span>

            <!-- 三个点按钮 -->
            <button
              @click.stop="toggleChatMenu(s.id)"
              class="shrink-0 opacity-0 group-hover:opacity-100 text-[#62666d] hover:text-[#d0d6e0] transition-all"
            >
              <i class="fa-solid fa-ellipsis text-[10px]"></i>
            </button>

            <!-- Dropdown 菜单 -->
            <Transition
              enter-active-class="transition duration-100 ease-out"
              enter-from-class="opacity-0 scale-95"
              enter-to-class="opacity-100 scale-100"
              leave-active-class="transition duration-75 ease-in"
              leave-from-class="opacity-100 scale-100"
              leave-to-class="opacity-0 scale-95"
            >
              <div
                v-if="chatMenuOpenId === s.id"
                class="absolute right-2 top-full mt-1 z-50 w-32 rounded-md brand-btn overflow-hidden"
                @click.stop
              >
                <button
                  @click="startRenameChat(s)"
                  class="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-[#d0d6e0] hover:bg-white/[0.05] transition-colors"
                >
                  <i class="fa-solid fa-pen text-[10px] w-3 text-center text-[#62666d]"></i> 重命名
                </button>
                <button
                  @click="chatMenuOpenId = null; deleteAiChat(s.id)"
                  class="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-rose-400 hover:bg-rose-500/10 transition-colors"
                >
                  <i class="fa-solid fa-trash text-[10px] w-4 text-center"></i> 删除
                </button>
              </div>
            </Transition>
          </div>
        </div>
        </div>
        </div>
      </div>

      <!-- 底部用户区 -->
      <div class="relative p-2">
        <!-- Dropdown 菜单（在用户信息上方弹出） -->
        <Transition
          enter-active-class="transition duration-150 ease-out"
          enter-from-class="opacity-0 translate-y-2"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition duration-100 ease-in"
          leave-from-class="opacity-100 translate-y-0"
          leave-to-class="opacity-0 translate-y-2"
        >
          <div v-if="userMenuOpen" class="absolute bottom-full left-2 right-2 mb-1 rounded-md brand-btn overflow-hidden z-50">
            <button
              @click="currentView = 'settings'; userMenuOpen = false"
              class="flex w-full items-center gap-2.5 px-3 py-2 text-sm text-[#d0d6e0] hover:bg-white/[0.05] transition-colors"
            >
              <i class="fa-solid fa-gear w-4 text-center text-xs text-[#62666d]"></i>
              系统设置
            </button>
            <button
              @click="(e) => { userMenuOpen = false; toggleTheme(e.currentTarget) }"
              class="flex w-full items-center gap-2.5 px-3 py-2 text-sm text-[#d0d6e0] hover:bg-white/[0.05] transition-colors"
            >
              <i class="fa-solid w-4 text-center text-xs text-[#62666d]" :class="isDark ? 'fa-sun' : 'fa-moon'"></i>
              {{ isDark ? '浅色模式' : '深色模式' }}
            </button>
            <div class="border-t border-white/[0.05]"></div>
            <button
              @click="handleLogout; userMenuOpen = false"
              class="flex w-full items-center gap-2.5 px-3 py-2 text-sm text-rose-400 hover:bg-rose-500/10 transition-colors"
            >
              <i class="fas fa-right-from-bracket w-4 text-center text-xs"></i>
              退出登录
            </button>
          </div>
        </Transition>

        <!-- 用户信息（点击弹出菜单） -->
        <button
          @click="userMenuOpen = !userMenuOpen"
          class="flex w-full items-center gap-2 px-2 py-1.5 rounded-md hover:bg-white/[0.04] transition-colors"
        >
          <div class="h-8 w-8 shrink-0 rounded-xl relative overflow-hidden flex items-center justify-center text-white text-sm font-medium" style="background: linear-gradient(to bottom, rgba(129,115,223,0.9), rgba(99,87,199,0.9)); box-shadow: inset 0 1px 0 0 rgba(255,255,255,0.12);">
            <span class="absolute inset-0 pointer-events-none" style="background-image: linear-gradient(to right, rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.06) 1px, transparent 1px); background-size: 8px 8px; mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%); -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);"></span>
            <span class="relative z-10">{{ currentUser?.username?.[0]?.toUpperCase() ?? '?' }}</span>
          </div>
          <div class="flex-1 min-w-0 text-left">
            <p class="text-sm text-[#f7f8f8] truncate leading-tight">{{ currentUser?.username }}</p>
          </div>
          <i class="fa-solid fa-chevron-up text-[10px] text-[#62666d]"></i>
        </button>
      </div>
    </aside>

    <!-- ================== 移动端：底部 Tab 导航栏 ================== -->
    <nav class="fixed bottom-0 left-0 right-0 z-50 border-t border-white/[0.06] bg-[#0A0A0F]/90 pb-2 pt-2 md:hidden">
      <div class="flex justify-around">
        <button @click="currentView = lastWorkspaceView" class="flex flex-col items-center p-2" :class="WORKSPACE_VIEWS.has(currentView) ? 'text-indigo-400' : 'text-white/40'">
          <i class="fa-solid fa-file-arrow-up text-lg"></i>
          <span class="mt-1 text-xs font-bold">录入</span>
        </button>
        <button @click="currentView = 'notes'" class="flex flex-col items-center p-2" :class="currentView === 'notes' ? 'text-indigo-400' : 'text-white/40'">
          <i class="fa-solid fa-book-open text-lg"></i>
          <span class="mt-1 text-xs font-bold">笔记库</span>
        </button>
        <button @click="currentView = 'dashboard'" class="flex flex-col items-center p-2" :class="currentView === 'dashboard' ? 'text-indigo-400' : 'text-white/40'">
          <i class="fa-solid fa-chart-pie text-lg"></i>
          <span class="mt-1 text-xs font-bold">数据面板</span>
        </button>
        <button @click="currentView = 'error-bank'" class="flex flex-col items-center p-2" :class="currentView === 'error-bank' ? 'text-indigo-400' : 'text-white/40'">
          <i class="fa-solid fa-layer-group text-lg"></i>
          <span class="mt-1 text-xs font-bold">错题本</span>
        </button>
        <button @click="currentView = 'settings'" class="flex flex-col items-center p-2" :class="currentView === 'settings' ? 'text-indigo-400' : 'text-white/40'">
          <i class="fa-solid fa-sliders text-lg"></i>
          <span class="mt-1 text-xs font-bold">设置</span>
        </button>
        <button @click="(e) => toggleTheme(e.currentTarget)" class="flex flex-col items-center p-2 text-white/40">
          <i class="fa-solid text-lg" :class="theme === 'dark' ? 'fa-sun' : 'fa-moon'"></i>
          <span class="mt-1 text-xs font-bold">主题</span>
        </button>
      </div>
    </nav>

    <!-- ================== 右侧区域 ================== -->
    <div class="relative z-10 flex-1 overflow-hidden pb-20 md:pb-3 md:pt-3 md:pr-3">

      <Transition name="view-fade" mode="out-in">
        <!-- 视图 1：录入工作台（分两页：上传解析页 / 题目核对页） -->
        <div v-if="currentView === 'workspace' || currentView === 'workspace_review'" key="workspace" class="h-full">
          <Transition name="flip" mode="out-in">
            <!-- 第一页：录入与分析 -->
            <ContentPanel v-if="currentView === 'workspace'" key="upload" title="智能录入与分析" :steps="workspaceSteps" :current-step="step - 1">
              <template #toolbar>
                <button
                  @click="showSplitHistory = !showSplitHistory"
                  class="inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
                  :class="showSplitHistory
                    ? 'bg-white/[0.06] text-[#f7f8f8] border border-white/[0.12]'
                    : 'border border-white/[0.08] bg-white/[0.02] text-[#d0d6e0] hover:bg-white/[0.05] hover:border-white/[0.12]'"
                >
                  <i class="fa-solid fa-clock-rotate-left text-[10px]"></i>
                  分割历史
                </button>
              </template>

              <!-- 右侧栏：分割历史 -->
              <template v-if="showSplitHistory" #sidebar>
                <SplitHistory
                  :theme="theme"
                  :visible="showSplitHistory"
                  @push-toast="pushToast"
                  @open-image="openModal"
                  @load-record="(r) => { handleLoadRecord(r); showSplitHistory = false }"
                  @go-workspace="currentView = splitCompleted ? 'workspace_review' : 'workspace'"
                />
              </template>

                <!-- 工具栏：状态 + 模式切换 + 擦除开关 -->
                <div class="flex flex-wrap items-center gap-3 py-2">
                  <!-- 模式切换 -->
                  <div class="flex items-center rounded-md brand-btn p-0.5">
                    <button
                      @click="uploadMode = 'exam'"
                      class="h-7 px-3 rounded text-xs font-medium transition-all"
                      :class="uploadMode === 'exam' ? 'bg-white/[0.06] text-[#f7f8f8]' : 'text-[#62666d] hover:text-[#8a8f98]'"
                    >
                      <i class="fa-solid fa-file-lines mr-1.5"></i>试卷分割
                    </button>
                    <button
                      @click="uploadMode = 'note'"
                      class="h-7 px-3 rounded text-xs font-medium transition-all"
                      :class="uploadMode === 'note' ? 'bg-white/[0.06] text-[#f7f8f8]' : 'text-[#62666d] hover:text-[#8a8f98]'"
                    >
                      <i class="fa-solid fa-book-open mr-1.5"></i>笔记整理
                    </button>
                  </div>

                  <!-- 分隔 -->
                  <div class="h-4 w-px bg-white/[0.08]"></div>

                  <!-- 擦除开关 -->
                  <label class="flex cursor-pointer items-center gap-2" @click="eraseEnabled = !eraseEnabled">
                    <div class="relative h-4 w-7 rounded-full transition-colors" :class="eraseEnabled ? 'bg-[rgb(129,115,223)]' : 'bg-white/[0.08]'">
                      <div class="absolute top-0.5 h-3 w-3 rounded-full bg-white transition-transform" :class="eraseEnabled ? 'translate-x-3' : 'translate-x-0.5'"></div>
                    </div>
                    <span class="text-xs text-[#8a8f98]">擦除笔迹</span>
                    <span class="relative group/tip">
                      <i class="fa-solid fa-circle-question text-[10px] text-[#62666d] cursor-help"></i>
                      <span class="absolute bottom-full right-0 mb-2 px-3 py-1.5 rounded-md bg-[#191a1b] border border-white/[0.08] text-xs text-[#d0d6e0] whitespace-nowrap opacity-0 pointer-events-none group-hover/tip:opacity-100 transition-opacity">
                        上传后自动擦除图片中的手写笔迹
                      </span>
                    </span>
                  </label>

                  <!-- 引擎状态（推到右侧） -->
                  <div class="ml-auto">
                    <StatusBar
                      :status-loading="statusLoading"
                      :status-error="statusError"
                      :status-pills="statusPills"
                      :provider-options="providerOptions"
                      :selected-model="selectedModel"
                      :disabled="splitting || splitCompleted"
                      :no-models="!hasConfiguredModel"
                      @update:selected-model="(v) => selectedModel = v"
                    />
                  </div>
                </div>

                <!-- 上传区（一体化） -->
                <div class="flex-1 min-h-0 overflow-y-auto custom-scrollbar flex flex-col items-center justify-center py-8 gap-6">

                  <!-- 引导信息 -->
                  <div class="text-center max-w-md">
                    <h3 class="text-base font-medium text-[#f7f8f8] mb-2">
                      {{ uploadMode === 'note' ? '上传手写笔记' : '上传试卷图片' }}
                    </h3>
                    <p class="text-sm text-[#62666d] leading-relaxed">
                      {{ uploadMode === 'note'
                        ? '支持拍照或扫描件，AI 将自动识别内容并整理为结构化笔记'
                        : '支持 PDF 和图片格式，AI 将自动完成 OCR 识别、题目分割和知识点标注'
                      }}
                    </p>
                  </div>

                  <!-- 流程步骤卡片 -->
                  <div class="grid grid-cols-4 gap-4 w-full max-w-2xl">
                    <div class="flex flex-col items-center gap-3 rounded-lg brand-btn p-4 text-center">
                      <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-white/[0.04]">
                        <i class="fa-solid fa-cloud-arrow-up text-xl text-[rgb(129,115,223)]"></i>
                      </div>
                      <span class="text-sm text-[#8a8f98]">{{ uploadMode === 'note' ? '上传笔记' : '上传文件' }}</span>
                    </div>
                    <div class="flex flex-col items-center gap-3 rounded-lg brand-btn p-4 text-center">
                      <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-white/[0.04]">
                        <i class="fa-solid fa-eye text-xl text-[rgb(129,115,223)]"></i>
                      </div>
                      <span class="text-sm text-[#8a8f98]">AI 识别</span>
                    </div>
                    <div class="flex flex-col items-center gap-3 rounded-lg brand-btn p-4 text-center">
                      <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-white/[0.04]">
                        <i class="fa-solid text-xl text-[rgb(129,115,223)]" :class="uploadMode === 'note' ? 'fa-wand-magic-sparkles' : 'fa-scissors'"></i>
                      </div>
                      <span class="text-sm text-[#8a8f98]">{{ uploadMode === 'note' ? '智能整理' : '分割纠错' }}</span>
                    </div>
                    <div class="flex flex-col items-center gap-3 rounded-lg brand-btn p-4 text-center">
                      <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-white/[0.04]">
                        <i class="fa-solid text-xl text-[rgb(129,115,223)]" :class="uploadMode === 'note' ? 'fa-bookmark' : 'fa-file-export'"></i>
                      </div>
                      <span class="text-sm text-[#8a8f98]">{{ uploadMode === 'note' ? '保存笔记' : '导出归档' }}</span>
                    </div>
                  </div>

                  <!-- 拖拽上传（与步骤卡片同宽） -->
                  <FileUploader
                    :pending-files="pendingFiles"
                    :file-progress="fileProgress"
                    :waiting-keys="waitingKeys"
                    :upload-busy="uploadBusy"
                    :upload-ready="uploadReady"
                    :splitting="splitting"
                    :split-completed="splitCompleted"
                    :expand="false"
                    :disabled="!hasConfiguredModel"
                    @upload="enqueueUpload"
                    @remove-file="removePendingFile"
                    class="w-full max-w-2xl"
                  />

                  <!-- 已上传文件 -->
                  <FileList
                    class="w-full max-w-2xl"
                    :pending-files="pendingFiles"
                    :file-progress="fileProgress"
                    :waiting-keys="waitingKeys"
                    :upload-busy="uploadBusy"
                    :upload-ready="uploadReady"
                    :splitting="splitting"
                    :split-completed="splitCompleted"
                    @remove-file="removePendingFile"
                  />

                  <!-- 操作按钮 -->
                  <ActionBar
                    class="mt-4"
                    :split-enabled="splitEnabled"
                    :export-enabled="false"
                    :splitting="splitting"
                    :split-completed="splitCompleted"
                    :upload-mode="uploadMode"
                    @split="doSplit"
                  />
                </div>
            </ContentPanel>

            <!-- 第二页：解析结果核对 -->
            <ContentPanel v-else-if="currentView === 'workspace_review'" key="review" title="题目数据核对" :steps="workspaceSteps" :current-step="3">
              <template #toolbar>
                <button
                  @click="() => { doReset(); currentView = 'workspace' }"
                  class="group inline-flex items-center gap-2 rounded-md border border-white/[0.08] bg-white/[0.02] px-3 py-1.5 text-xs font-medium text-[#d0d6e0] hover:bg-white/[0.05] hover:border-white/[0.12] transition-colors"
                >
                  <i class="fa-solid fa-arrow-left-long text-xs transition-transform group-hover:-translate-x-0.5"></i>
                  返回
                </button>
              </template>

                <!-- 分割进行中 -->
                <!-- <SplitLoading v-if="splitting" /> -->

                <!-- 题目列表 -->
                <div class="flex-1 overflow-y-auto pr-2 custom-scrollbar py-2 pb-24">
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

            </ContentPanel>
          </Transition>
        </div>

        <!-- 视图 2：待复习 -->
        <ContentPanel v-else-if="currentView === 'review'" key="review_view" title="待复习">
          <ReviewView
            :theme="theme"
            :visible="currentView === 'review'"
            @go-workspace="currentView = 'workspace'"
            @push-toast="pushToast"
            @open-image="openModal"
            @start-chat="openChat"
          />
        </ContentPanel>

        <!-- 视图 3：数据面板 -->
        <ContentPanel v-else-if="currentView === 'dashboard'" key="dashboard_view" title="数据面板">
          <template #toolbar>
            <button @click="currentView = 'workspace'" class="inline-flex items-center gap-2 rounded-md brand-btn px-3 py-1.5 text-xs font-medium text-[#f7f8f8]">
              <i class="fa-solid fa-plus-circle text-[10px]"></i> 录入新题目
            </button>
          </template>
          <Dashboard
            :theme="theme"
            :visible="currentView === 'dashboard'"
            @go-workspace="currentView = 'workspace'"
            @push-toast="pushToast"
          />
        </ContentPanel>

        <!-- 视图 4：错题库 -->
        <ContentPanel v-else-if="currentView === 'error-bank'" key="error_bank_view" title="错题库">
          <template #toolbar>
            <button @click="currentView = 'workspace'" class="flex h-7 w-7 items-center justify-center rounded-md text-[#62666d] hover:bg-white/[0.04] hover:text-[#8a8f98] transition-colors" title="录入新题目">
              <i class="fa-solid fa-plus text-xs"></i>
            </button>
          </template>
          <template v-if="errorBankRef?.filterPanelOpen" #sidebar>
            <div class="p-4 space-y-4">
              <div class="flex items-center justify-between">
                <span class="text-xs font-medium text-[#f7f8f8]">筛选设置</span>
                <button @click="errorBankRef.filterPanelOpen = false" class="text-[#62666d] hover:text-[#8a8f98] transition-colors">
                  <i class="fa-solid fa-xmark text-xs"></i>
                </button>
              </div>

              <!-- 学科 -->
              <div>
                <label class="mb-1.5 block text-xs font-medium text-[#62666d]">学科</label>
                <CustomSelect v-model="errorBankRef.filters.subject" :options="errorBankRef.subjects" placeholder="全部学科" />
              </div>

              <!-- 题型 -->
              <div>
                <label class="mb-1.5 block text-xs font-medium text-[#62666d]">题型</label>
                <CustomSelect v-model="errorBankRef.filters.question_type" :options="errorBankRef.questionTypes" placeholder="全部题型" />
              </div>

              <!-- 复习状态 -->
              <div>
                <label class="mb-1.5 block text-xs font-medium text-[#62666d]">复习状态</label>
                <CustomSelect v-model="errorBankRef.filters.review_status" :options="['待复习', '复习中', '已掌握']" placeholder="全部状态" />
              </div>

              <!-- 知识点标签 -->
              <div v-if="errorBankRef.tagNames?.length">
                <label class="mb-1.5 block text-xs font-medium text-[#62666d]">知识点</label>
                <div class="flex flex-wrap gap-1.5">
                  <button v-for="tag in errorBankRef.tagNames" :key="tag"
                    @click="errorBankRef.toggleTagSelect(tag)"
                    class="rounded-md px-2 py-0.5 text-xs font-medium transition-all"
                    :class="errorBankRef.selectedTags?.has(tag)
                      ? 'bg-[rgb(129,115,223)] text-white'
                      : 'border border-white/[0.06] bg-white/[0.02] text-[#62666d] hover:text-[#8a8f98] hover:border-white/[0.1]'"
                  >{{ tag }}</button>
                </div>
              </div>
            </div>
          </template>

          <ErrorBank
            ref="errorBankRef"
            :theme="theme"
            :visible="currentView === 'error-bank'"
            @go-workspace="currentView = 'workspace'"
            @push-toast="pushToast"
            @open-image="openModal"
            @start-chat="openChat"
          />
        </ContentPanel>

        <!-- 视图 5：分割历史（已移入录入工作台右侧栏） -->

        <!-- 视图 6：系统设置 -->
        <ContentPanel v-else-if="currentView === 'settings'" key="settings_view" title="系统设置">
          <SettingsView
            :visible="currentView === 'settings'"
            @saved="doFetchStatus"
          />
        </ContentPanel>

        <!-- 视图 7：AI 辅导对话 -->
        <ContentPanel v-else-if="currentView === 'chat'" key="chat_view" title="AI 辅导">
          <ChatView
            v-if="chatActive"
            :session-id="chatSessionId"
            :question="chatQuestion"
            :model-provider="selectedProvider"
            :model-name="selectedModel"
            :username="currentUser?.username"
            @back="backToErrorBank"
          />
        </ContentPanel>

        <!-- 视图 8：笔记 -->
        <ContentPanel v-else-if="currentView === 'notes'" key="notes_view" title="笔记库">
          <template #toolbar>
            <button @click="noteViewRef?.triggerUpload?.()" class="inline-flex items-center gap-2 rounded-md brand-btn px-3 py-1.5 text-xs font-medium text-[#f7f8f8]">
              <i class="fa-solid fa-plus text-[10px]"></i> 上传笔记
            </button>
          </template>
          <NoteView
            ref="noteViewRef"
            :visible="currentView === 'notes'"
            :model-provider="selectedProvider"
            :model-name="selectedModel"
            :theme="theme"
            @push-toast="pushToast"
          />
        </ContentPanel>

        <!-- 视图 9：AI 对话 -->
        <ContentPanel v-else-if="currentView === 'ai-chat'" key="ai_chat_view" title="AI 对话">
          <ChatPage
            :visible="currentView === 'ai-chat'"
            :session-id="activeAiChatId"
            :model-provider="selectedProvider"
            :model-name="selectedModel"
            :username="currentUser?.username"
            @push-toast="pushToast"
            @create-chat="createAiChat"
            @session-title-updated="onAiChatTitleUpdated"
          />
        </ContentPanel>
      </Transition>

      <!-- workspace_review 浮动选择面板 -->
      <SelectionPanel
        :visible="currentView === 'workspace_review'"
        :count="selectedIds.size"
        export-label="导出错题本"
        :show-save="true"
        @export="doExport"
        @save="doSaveToDb"
        @clear="deselectAll"
      />

    </div>

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
        <div class="absolute inset-0 bg-black/60" @click="answerModalOpen = false"></div>
        <div class="relative w-full max-w-lg rounded-lg brand-btn p-6">
          <h3 class="mb-1 text-base font-medium text-[#f7f8f8]">录入答案</h3>
          <p class="mb-4 text-xs text-[#62666d]">
            AI 辅导需要正确答案作为参考。支持 Markdown 格式，数学公式使用 LaTeX（$..$ 行内，$$...$$ 独占行）
          </p>
          <textarea
            v-model="answerModalText"
            rows="10"
            placeholder="在此粘贴或输入答案/解析..."
            class="w-full resize-none rounded-md border border-white/[0.08] bg-white/[0.02] px-4 py-3 font-mono text-sm text-[#d0d6e0] placeholder-[#62666d] focus:border-white/[0.12] focus:outline-none transition-colors"
          ></textarea>
          <div class="mt-4 flex justify-end gap-3">
            <button
              @click="answerModalOpen = false"
              class="rounded-md border border-white/[0.08] bg-white/[0.02] px-4 py-2 text-sm font-medium text-[#d0d6e0] transition-colors hover:bg-white/[0.05]"
            >
              取消
            </button>
            <button
              @click="saveAnswerAndChat"
              :disabled="answerModalSaving"
              class="rounded-md bg-[#5e6ad2] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#7170ff] disabled:opacity-50"
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
::view-transition-old(root),
::view-transition-new(root) {
  animation: none;
  mix-blend-mode: normal;
}


.ws-loading-fade-leave-active { transition: opacity 0.4s ease; }
.ws-loading-fade-leave-to { opacity: 0; }

/* 星星闪烁 */
@keyframes ws-star-twinkle {
  0%, 100% { opacity: var(--star-opacity); }
  50% { opacity: 0.02; }
}
.ws-star {
  animation: ws-star-twinkle ease-in-out infinite;
}

.ws-loading-bar {
  animation: wsLoadProgress 2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}
@keyframes wsLoadProgress {
  from { width: 0%; }
  to   { width: 100%; }
}

/* 视图切换：极简淡入淡出 (Simple Fade) */
.view-fade-enter-active,
.view-fade-leave-active {
  transition: opacity 0.3s ease;
}

.view-fade-enter-from,
.view-fade-leave-to {
  opacity: 0;
}

/* 工作台内部页面切换：左右滑动淡入 (Flip) */
.flip-enter-active,
.flip-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.flip-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.flip-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

</style>
