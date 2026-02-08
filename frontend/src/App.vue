<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

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

  const transition = document.startViewTransition(() => {
    applyTheme(nextTheme)
  })

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

const statusLoading = ref(true)
const systemStatus = ref(null)
const statusError = ref('')
const statusPills = computed(() => {
  const s = systemStatus.value
  if (!s) return []
  const pills = []
  pills.push({ key: 'paddle', ok: !!s.paddleocr_configured, label: s.paddleocr_configured ? 'PaddleOCR' : 'PaddleOCR未配置' })
  pills.push({ key: 'deepseek', ok: !!s.deepseek_configured, label: s.deepseek_configured ? 'DeepSeek' : 'DeepSeek未配置' })
  if (s.langsmith_enabled) pills.push({ key: 'langsmith', ok: true, label: 'LangSmith追踪' })
  return pills
})

const fetchStatus = async () => {
  statusLoading.value = true
  statusError.value = ''
  try {
    const resp = await fetch('/api/status')
    const data = await resp.json()
    if (data && data.success) systemStatus.value = data.status
    else statusError.value = (data && data.error) || '获取系统状态失败'
  } catch (e) {
    statusError.value = e instanceof Error ? e.message : String(e)
  } finally {
    statusLoading.value = false
  }
}

const step = ref(1)

const toasts = ref([])
let toastId = 0
const pushToast = (type, message, timeout = 2600) => {
  const id = ++toastId
  toasts.value = [{ id, type, message }, ...toasts.value].slice(0, 5)
  if (timeout > 0) {
    window.setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, timeout)
  }
}

const modalOpen = ref(false)
const modalSrc = ref('')
const openModal = (src) => {
  modalSrc.value = src || ''
  modalOpen.value = !!src
}
const closeModal = () => {
  modalOpen.value = false
  modalSrc.value = ''
}

const uploadBusy = ref(false)
const uploadReady = ref(false)
const splitting = ref(false)
const splitCompleted = ref(false)
const fileInputEl = ref(null)

const pendingFiles = reactive([])
const fileProgress = reactive({})
const waitingKeys = reactive(new Set())
const uploadQueue = reactive([])
let activeXhr = null
let fakeProgressTimer = null
let fakeProgressKeys = []

const fileKey = (file) => `${file.name}|${file.size}|${file.lastModified}`

const pendingCount = computed(() => pendingFiles.length)
const splitEnabled = computed(() => !splitting.value && !splitCompleted.value && uploadReady.value && !uploadBusy.value)
const exportEnabled = computed(() => splitCompleted.value && selectedIds.size > 0)

const stopFakeProgress = () => {
  if (fakeProgressTimer) {
    window.clearInterval(fakeProgressTimer)
    fakeProgressTimer = null
  }
  fakeProgressKeys = []
}

const setProgress = (key, p) => {
  fileProgress[key] = Math.max(0, Math.min(100, Number(p) || 0))
}

const startFakeProgress = (keys) => {
  stopFakeProgress()
  fakeProgressKeys = Array.from(keys || [])
  const tick = () => {
    if (!uploadBusy.value) {
      stopFakeProgress()
      return
    }
    for (const key of fakeProgressKeys) {
      const current = Number(fileProgress[key] || 0)
      const cap = 82
      if (current >= cap) continue
      let inc = 0
      if (current < 55) inc = 1 + Math.random() * 3
      else if (current < 75) inc = 0.4 + Math.random() * 1.1
      else inc = 0.08 + Math.random() * 0.25
      setProgress(key, Math.min(cap, current + inc))
    }
  }
  tick()
  fakeProgressTimer = window.setInterval(tick, 360)
}

const isUploadBusy = () => uploadBusy.value

const enqueueUpload = (files) => {
  const list = Array.from(files || [])
  if (!list.length) return
  if (splitCompleted.value || splitting.value) {
    pushToast('error', '已分割完成，请先重新开始')
    return
  }

  for (const f of list) {
    const k = fileKey(f)
    if (pendingFiles.some((x) => x.key === k)) continue
    pendingFiles.push({ key: k, file: f })
    setProgress(k, 0)
  }

  if (isUploadBusy()) {
    for (const f of list) waitingKeys.add(fileKey(f))
    uploadQueue.push(list)
    return
  }

  handleUpload(list)
}

const pumpUploadQueue = () => {
  if (isUploadBusy()) return
  if (!uploadQueue.length) return
  const next = uploadQueue.shift()
  if (next && next.length) handleUpload(next)
}

const removePendingFile = async (key) => {
  if (!key) return
  if (splitting.value || splitCompleted.value) return

  const locked = isUploadBusy() || uploadReady.value
  if (locked) {
    await cancelFile(key)
    return
  }

  const idx = pendingFiles.findIndex((x) => x.key === key)
  if (idx >= 0) pendingFiles.splice(idx, 1)
  delete fileProgress[key]
  waitingKeys.delete(key)
  for (let i = uploadQueue.length - 1; i >= 0; i--) {
    uploadQueue[i] = (uploadQueue[i] || []).filter((f) => fileKey(f) !== key)
    if (!uploadQueue[i].length) uploadQueue.splice(i, 1)
  }
}

const cancelFile = async (key) => {
  try {
    if (fakeProgressKeys.length) fakeProgressKeys = fakeProgressKeys.filter((k) => k !== key)
    if (!fakeProgressKeys.length) stopFakeProgress()

    const resp = await fetch('/api/cancel_file', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_key: key }),
    })
    const data = await resp.json().catch(() => null)

    if (data && data.success) {
      const idx = pendingFiles.findIndex((x) => x.key === key)
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
        try {
          activeXhr.abort()
        } catch (_) {}
      }
    } else {
      pushToast('error', (data && data.error) || '撤销失败')
    }
  } catch (_) {
    pushToast('error', '撤销失败: 网络错误')
  }
}

const handleUpload = (files) => {
  const uploadFiles = Array.from(files || []).filter((f) => pendingFiles.some((x) => x.key === fileKey(f)))
  if (!uploadFiles.length) return

  uploadBusy.value = true
  step.value = 2

  const keys = uploadFiles.map((f) => fileKey(f))
  for (const k of keys) waitingKeys.delete(k)
  startFakeProgress(keys)

  const formData = new FormData()
  for (const f of uploadFiles) {
    formData.append('files', f)
    formData.append('file_key', fileKey(f))
  }

  const xhr = new XMLHttpRequest()
  activeXhr = xhr
  xhr.open('POST', '/api/upload', true)

  xhr.upload.addEventListener('progress', (e) => {
    if (!e.lengthComputable) return
    const pct = Math.max(0, Math.min(95, (e.loaded / e.total) * 95))
    for (const k of keys) {
      if (pendingFiles.some((x) => x.key === k)) setProgress(k, Math.max(fileProgress[k] || 0, pct))
    }
  })

  xhr.addEventListener('load', () => {
    stopFakeProgress()
    uploadBusy.value = false
    activeXhr = null

    let data = null
    try {
      data = JSON.parse(xhr.responseText)
    } catch (_) {}

    if (data && data.success) {
      for (const k of keys) {
        if (pendingFiles.some((x) => x.key === k)) setProgress(k, 100)
      }
      uploadReady.value = pendingFiles.length > 0
      step.value = pendingFiles.length > 0 ? 3 : 1
      pushToast('success', `文件处理成功！本次新增 ${data.result.file_count} 个文件，总共有 ${data.result.image_count} 张图片`)
      pumpUploadQueue()
      return
    }

    const msg = (data && data.error) || '文件处理失败'
    pushToast('error', msg)
    pumpUploadQueue()
  })

  xhr.addEventListener('error', () => {
    stopFakeProgress()
    uploadBusy.value = false
    activeXhr = null
    pushToast('error', '上传失败: 网络错误')
    pumpUploadQueue()
  })

  xhr.addEventListener('abort', () => {
    stopFakeProgress()
    uploadBusy.value = false
    activeXhr = null
    pumpUploadQueue()
  })

  xhr.send(formData)
}

const questions = ref([])
const selectedIds = reactive(new Set())
const questionsBoxEl = ref(null)
const questionListEl = ref(null)
let sortable = null

const selectedCountLabel = computed(() => `已选择 ${selectedIds.size} 道题目`)

const selectAll = () => {
  for (const q of questions.value) selectedIds.add(q.question_id)
}
const deselectAll = () => {
  selectedIds.clear()
}

const formatOption = (s) => String(s || '')

/** 判断内容是否包含 HTML 标签（OCR 表格等） */
const isHtml = (s) => /<\/?(?:table|tr|td|th|thead|tbody)\b/i.test(s || '')

const typesetMath = async () => {
  await nextTick()
  const mj = window.MathJax
  const el = questionsBoxEl.value
  if (!mj || !el || typeof mj.typesetPromise !== 'function') return
  try {
    await mj.typesetPromise([el])
  } catch (_) {}
}

const initSortable = async () => {
  await nextTick()
  const el = questionListEl.value
  if (!el) return
  const Sortable = window.Sortable
  if (!Sortable) return
  if (sortable) sortable.destroy()
  sortable = Sortable.create(el, {
    animation: 150,
    handle: '[data-drag-handle="1"]',
    onEnd: (evt) => {
      const oldIndex = evt.oldIndex
      const newIndex = evt.newIndex
      if (oldIndex == null || newIndex == null || oldIndex === newIndex) return
      const arr = questions.value.slice()
      const [moved] = arr.splice(oldIndex, 1)
      arr.splice(newIndex, 0, moved)
      questions.value = arr
    },
  })
}

const doSplit = async () => {
  if (!uploadReady.value) {
    pushToast('error', '请先上传文件')
    return
  }
  if (splitting.value || splitCompleted.value) return

  splitting.value = true
  step.value = 3
  pushToast('info', '正在调用AI分割题目，请稍候...', 1800)

  try {
    const resp = await fetch('/api/split', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
    const data = await resp.json()
    if (data && data.success) {
      questions.value = data.questions || []
      selectedIds.clear()
      splitCompleted.value = true
      step.value = 4
      pushToast('success', `成功分割 ${questions.value.length} 道题目`)
      await typesetMath()
      await initSortable()
      return
    }
    pushToast('error', (data && data.error) || '题目分割失败')
  } catch (e) {
    pushToast('error', '分割失败: ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    splitting.value = false
  }
}

const doExport = async () => {
  if (!selectedIds.size) {
    pushToast('error', '请至少选择一道题目！')
    return
  }
  try {
    const resp = await fetch('/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ selected_ids: Array.from(selectedIds) }),
    })
    const data = await resp.json()
    if (data && data.success) {
      step.value = 5
      pushToast('success', `错题本导出成功！已保存到: ${data.output_path}`)

      let filename = 'wrongbook.md'
      if (data.output_path) {
        const parts = String(data.output_path).split(/[/\\]/)
        const last = parts[parts.length - 1]
        if (last) filename = last
      }
      const downloadUrl = `/download/${encodeURIComponent(filename)}?t=${Date.now()}`
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = filename
      a.style.display = 'none'
      document.body.appendChild(a)
      a.click()
      a.remove()
      return
    }
    pushToast('error', (data && data.error) || '导出失败')
  } catch (e) {
    pushToast('error', '导出失败: ' + (e instanceof Error ? e.message : String(e)))
  }
}

const doReset = async () => {
  try {
    await fetch('/api/reset', { method: 'POST' }).catch(() => null)
  } finally {
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
    step.value = 1
    pushToast('success', '已重置')
  }
}

const onFileInput = (e) => {
  enqueueUpload(e.target.files)
  e.target.value = ''
}

const uploadHover = ref(false)
const onDrop = (e) => {
  e.preventDefault()
  uploadHover.value = false
  enqueueUpload(e.dataTransfer.files)
}

onMounted(() => {
  const saved = localStorage.getItem('theme')
  const initial = saved || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
  applyTheme(initial)
  fetchStatus()
})

onBeforeUnmount(() => {
  stopFakeProgress()
  if (sortable) sortable.destroy()
  sortable = null
})
</script>

<template>
  <div class="min-h-full bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-50">
    <div class="container mx-auto max-w-5xl px-4 py-8">
      <header class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 class="text-2xl font-semibold tracking-tight sm:text-3xl">
            <i class="fa-solid fa-file-circle-check mr-2 text-slate-700 dark:text-slate-200"></i>
            错题本生成系统
          </h1>
          <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">智能识别、分割和导出试卷题目</p>
        </div>
        <button
          type="button"
          class="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition-colors duration-200 hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-200 active:scale-[0.98] motion-reduce:active:scale-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800 dark:focus:ring-slate-800"
          @click="(e) => toggleTheme(e.currentTarget)"
        >
          <i class="fa-solid" :class="theme === 'dark' ? 'fa-sun' : 'fa-moon'"></i>
          <span>{{ theme === 'dark' ? '浅色' : '深色' }}</span>
        </button>
      </header>

      <div class="main-content rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6 dark:border-slate-800 dark:bg-slate-900">
        <div
          class="mb-6 flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-200"
        >
          <span class="font-semibold text-slate-900 dark:text-slate-100">系统状态</span>
          <span
            v-if="statusLoading"
            class="inline-flex items-center gap-2 rounded-full bg-slate-200 px-3 py-1 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            <span class="inline-block h-2 w-2 animate-pulse rounded-full bg-slate-500"></span>
            检查中...
          </span>
          <span
            v-else-if="statusError"
            class="inline-flex items-center gap-2 rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-800 dark:bg-rose-900/40 dark:text-rose-200"
          >
            <i class="fa-solid fa-circle-xmark"></i>
            {{ statusError }}
          </span>
          <span
            v-else
            v-for="p in statusPills"
            :key="p.key"
            class="inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold"
            :class="
              p.ok
                ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200'
                : 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200'
            "
          >
            <i class="fa-solid" :class="p.ok ? 'fa-circle-check' : 'fa-circle-xmark'"></i>
            {{ p.label }}
          </span>
        </div>

        <div class="mb-8">
          <ol class="w-full items-center space-y-4 sm:flex sm:justify-between sm:space-x-0 sm:space-y-0 rtl:space-x-reverse">
            <li
              v-for="n in 4"
              :key="n"
              class="step flex items-center space-x-3 rtl:space-x-reverse"
              :class="n === step ? 'text-blue-700 dark:text-blue-300' : 'text-slate-600 dark:text-slate-300'"
            >
              <span
                class="step-circle flex h-10 w-10 shrink-0 items-center justify-center rounded-full lg:h-12 lg:w-12"
                :class="
                  n < step
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-200'
                    : n === step
                      ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-200'
                      : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300'
                "
              >
                <i v-if="n < step" class="fa-solid fa-check"></i>
                <span v-else class="text-sm font-semibold tabular-nums">{{ n }}</span>
              </span>
              <span>
                <h3 class="step-label font-medium leading-tight">
                  {{ n === 1 ? '上传文件' : n === 2 ? 'OCR解析' : n === 3 ? '分割题目' : '预览导出' }}
                </h3>
                <p class="step-desc text-sm text-slate-600 dark:text-slate-300">
                  {{
                    n === 1
                      ? '选择 PDF / 图片并上传'
                      : n === 2
                        ? '结构化识别题干/图片'
                        : n === 3
                          ? 'AI 识别题号并拆分'
                          : '勾选题目并导出'
                  }}
                </p>
              </span>
            </li>
          </ol>
        </div>

        <div v-if="pendingCount" class="mb-6">
          <div class="flex flex-wrap items-center gap-2">
            <div
              v-for="item in pendingFiles"
              :key="item.key"
              class="file-chip inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100"
              :class="(uploadBusy || uploadReady) && 'file-chip--progress'"
              :style="{ '--p': String(fileProgress[item.key] ?? 0) }"
              :data-file-key="item.key"
            >
              <i
                class="fa-regular"
                :class="
                  item.file.name.toLowerCase().endsWith('.pdf')
                    ? 'fa-file-pdf text-rose-600 dark:text-rose-300'
                    : 'fa-file-image text-slate-600 dark:text-slate-300'
                "
              ></i>
              <span class="max-w-[260px] truncate" :title="item.file.name">{{ item.file.name }}</span>
              <span class="ml-1 text-xs font-semibold tabular-nums text-slate-500 dark:text-slate-300">
                {{
                  waitingKeys.has(item.key) && uploadBusy && (fileProgress[item.key] ?? 0) === 0
                    ? '等待中...'
                    : `${Math.round(fileProgress[item.key] ?? 0)}%`
                }}
              </span>
              <button
                type="button"
                class="ml-1 inline-flex h-6 w-6 flex-none items-center justify-center rounded-md text-slate-500 transition focus:outline-none focus:ring-4 focus:ring-slate-200 hover:bg-slate-100 hover:text-slate-700 dark:text-slate-300 dark:focus:ring-slate-800 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                :disabled="splitting || splitCompleted"
                @click.stop="() => removePendingFile(item.key)"
              >
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>
          </div>
        </div>

        <div
          class="rounded-2xl border-2 border-dashed px-6 py-10 text-center transition dark:bg-slate-950/40"
          :class="
            uploadHover
              ? 'border-slate-400 bg-slate-100 dark:border-slate-600 dark:bg-slate-950/60'
              : 'border-slate-300 bg-slate-50 hover:border-slate-400 hover:bg-slate-100 dark:border-slate-700 dark:hover:border-slate-600 dark:hover:bg-slate-950/60'
          "
          @dragenter.prevent="uploadHover = true"
          @dragover.prevent="uploadHover = true"
          @dragleave.prevent="uploadHover = false"
          @drop="onDrop"
          @click="() => fileInputEl?.click()"
        >
          <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-white shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
            <i class="fa-regular fa-file-lines text-2xl text-slate-700 dark:text-slate-200"></i>
          </div>
          <div class="text-base font-semibold text-slate-900 dark:text-slate-100">点击或拖拽添加文件</div>
          <div class="mt-2 text-sm text-slate-500 dark:text-slate-300">
            支持 PDF、PNG、JPG 等格式，可同时选择多个文件（单文件最大 50MB）
          </div>
          <input
            ref="fileInputEl"
            type="file"
            class="hidden"
            accept=".pdf,.png,.jpg,.jpeg,.bmp,.tiff,.webp"
            multiple
            @change="onFileInput"
          />
        </div>

        <div ref="questionsBoxEl" class="mt-8">
          <div v-if="questions.length" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-6">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">题目预览</h3>
                <p class="mt-1 text-sm text-slate-500 dark:text-slate-300">点击卡片选择需要导出的题目</p>
              </div>
              <div class="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  class="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition-colors duration-200 hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-200 active:scale-[0.98] motion-reduce:active:scale-100 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-200 dark:hover:bg-slate-800 dark:focus:ring-slate-800"
                  @click="selectAll"
                >
                  <i class="fa-solid fa-check-double"></i>
                  全选
                </button>
                <button
                  type="button"
                  class="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition-colors duration-200 hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-200 active:scale-[0.98] motion-reduce:active:scale-100 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-200 dark:hover:bg-slate-800 dark:focus:ring-slate-800"
                  @click="deselectAll"
                >
                  <i class="fa-solid fa-xmark"></i>
                  取消
                </button>
                <span class="ml-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
                  {{ selectedCountLabel }}
                </span>
              </div>
            </div>

            <div ref="questionListEl" class="mt-5 grid gap-4" id="questionList">
              <div
                v-for="q in questions"
                :key="q.question_id"
                class="question-card relative rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md dark:border-slate-800 dark:bg-slate-950/30"
                :class="selectedIds.has(q.question_id) && 'ring-2 ring-slate-400 bg-slate-50 dark:bg-slate-950/50'"
                @click="() => (selectedIds.has(q.question_id) ? selectedIds.delete(q.question_id) : selectedIds.add(q.question_id))"
              >
                <div class="mb-3 flex items-center gap-3 border-b border-slate-100 pb-3 dark:border-slate-800">
                  <button
                    type="button"
                    class="inline-flex items-center justify-center rounded-md border border-slate-200 bg-white px-2 py-1 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                    data-drag-handle="1"
                    @click.stop
                  >
                    <i class="fa-solid fa-grip-lines"></i>
                  </button>
                  <span class="text-base font-semibold text-slate-900 dark:text-slate-100">题目 {{ q.question_id }}</span>
                  <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                    {{ q.question_type }}
                  </span>
                  <label class="ml-auto inline-flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300" @click.stop>
                    <input
                      type="checkbox"
                      class="question-select h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-400 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                      :checked="selectedIds.has(q.question_id)"
                      @change="(e) => (e.target.checked ? selectedIds.add(q.question_id) : selectedIds.delete(q.question_id))"
                    />
                    选择
                  </label>
                </div>

                <div class="question-content">
                  <template v-if="q.content_blocks && q.content_blocks.length">
                    <template v-for="(b, i) in q.content_blocks" :key="`${q.question_id}-${i}`">
                      <div v-if="b.block_type === 'text' && isHtml(b.content)" v-html="b.content" class="question-text my-2 leading-7 text-slate-800 dark:text-slate-100"></div>
                      <p v-else-if="b.block_type === 'text'" class="my-2 whitespace-pre-line leading-7 text-slate-800 dark:text-slate-100">{{ b.content }}</p>
                      <img
                        v-else-if="b.block_type === 'image' && b.content"
                        :src="b.content"
                        class="my-3 max-w-full cursor-zoom-in rounded-lg border border-slate-200 shadow-sm dark:border-slate-800"
                        @click.stop="() => openModal(b.content)"
                        alt="图片"
                      />
                      <p v-else-if="b.block_type === 'image'" class="my-2 text-sm font-semibold text-amber-600 dark:text-amber-400">
                        <i class="fa-regular fa-image mr-2"></i>图片资源
                      </p>
                      <p v-else class="my-2 whitespace-pre-line leading-7 text-slate-800 dark:text-slate-100">{{ b.content }}</p>
                    </template>
                  </template>
                  <p v-else class="text-sm text-slate-500 dark:text-slate-300">（内容为空）</p>

                  <div v-if="q.options && q.options.length" class="mt-4 grid gap-2">
                    <div
                      v-for="(opt, idx) in q.options"
                      :key="`${q.question_id}-opt-${idx}`"
                      class="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-800 dark:bg-slate-900 dark:text-slate-100"
                    >
                      {{ formatOption(opt) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-6 flex flex-wrap items-center justify-center gap-3">
          <button
            type="button"
            class="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors duration-200 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-200 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 motion-reduce:active:scale-100 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-900/50"
            :disabled="!splitEnabled"
            @click="doSplit"
          >
            <template v-if="splitting">
              <i class="fa-solid fa-circle-notch fa-spin"></i>
              正在分割...
            </template>
            <template v-else-if="splitCompleted">
              <i class="fa-solid fa-circle-check"></i>
              已完成分割
            </template>
            <template v-else>
              <i class="fa-solid fa-wand-magic-sparkles"></i>
              开始分割题目
            </template>
          </button>
          <button
            type="button"
            class="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors duration-200 hover:bg-emerald-700 focus:outline-none focus:ring-4 focus:ring-emerald-200 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 motion-reduce:active:scale-100 dark:focus:ring-emerald-900/50"
            :disabled="!exportEnabled"
            @click="doExport"
          >
            <i class="fa-solid fa-download"></i>
            导出错题本
          </button>
          <button
            type="button"
            class="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition-colors duration-200 hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-200 active:scale-[0.98] motion-reduce:active:scale-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800 dark:focus:ring-slate-800"
            @click="doReset"
          >
            <i class="fa-solid fa-arrow-rotate-right"></i>
            重新开始
          </button>
        </div>
      </div>
    </div>
  </div>

  <div
    class="img-modal fixed inset-0 z-50 hidden items-center justify-center bg-black/80 p-4"
    :class="modalOpen ? 'flex' : 'hidden'"
    @click="closeModal"
  >
    <img class="max-h-[90vh] w-auto max-w-full rounded-xl shadow-2xl" :src="modalSrc" alt="预览" @click.stop />
  </div>

  <div class="pointer-events-none fixed left-1/2 top-4 z-50 flex w-[min(420px,calc(100vw-2rem))] -translate-x-1/2 flex-col gap-2">
    <div
      v-for="t in toasts"
      :key="t.id"
      class="pointer-events-auto rounded-xl px-4 py-3 text-sm font-medium shadow-lg ring-1"
      :class="
        t.type === 'success'
          ? 'bg-emerald-600 text-white ring-emerald-700/30'
          : t.type === 'error'
            ? 'bg-rose-600 text-white ring-rose-700/30'
            : 'bg-slate-900 text-white ring-slate-700/30'
      "
    >
      {{ t.message }}
    </div>
  </div>
</template>
