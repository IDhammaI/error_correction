import { ref, reactive, computed } from 'vue'
import { fileKey } from '@/utils/index.js'
import * as api from '@/api/index.js'

/**
 * useFileUpload.js
 * 管理工作台文件上传队列、上传进度、撤销文件和重置上传会话。
 */
export function useFileUpload(pushToast, S, questions, selectedIds, splitCompleted, splitting, uploadMode) {
  const uploadBusy = ref(false)
  const uploadReady = ref(false)
  const pendingFiles = reactive([])
  const pendingPreviewUrls = computed(() =>
    pendingFiles.filter(pf => pf.file).map(pf => URL.createObjectURL(pf.file))
  )
  const fileProgress = reactive({})
  const waitingKeys = reactive(new Set())
  const uploadQueue = reactive([])
  let activeXhr = null
  let fakeProgressTimer = null
  let fakeProgressKeys = []

  /**
   * 统一限制上传进度范围，避免接口或模拟进度写入异常数值。
   */
  const setProgress = (key, p) => { fileProgress[key] = Math.max(0, Math.min(100, Number(p) || 0)) }

  /**
   * 停止模拟上传进度，并清空正在模拟的文件 key。
   */
  const stopFakeProgress = () => {
    if (fakeProgressTimer) {
      window.clearInterval(fakeProgressTimer)
      fakeProgressTimer = null
    }
    fakeProgressKeys = []
  }

  /**
   * 启动模拟进度，让没有真实进度回调的等待阶段也有连续反馈。
   */
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

  /**
   * 真正发起上传请求，并把 XHR 回调同步到上传状态和进度条。
   */
  const handleUpload = (files, { resetSession = false } = {}) => {
    const uploadFiles = Array.from(files || []).filter(f => pendingFiles.some(x => x.key === fileKey(f)))
    if (!uploadFiles.length) return
    uploadBusy.value = true
    const step = S.value
    const keys = uploadFiles.map(f => fileKey(f))
    for (const k of keys) waitingKeys.delete(k)
    startFakeProgress(keys)

    const formData = new FormData()
    if (resetSession) formData.append('reset_session', '1')
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
        pushToast('success', '上传成功')
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

  /**
   * 当前上传结束后，从等待队列里取下一批文件继续上传。
   */
  const pumpUploadQueue = () => {
    if (uploadBusy.value || !uploadQueue.length) return
    const next = uploadQueue.shift()
    if (next && next.length) handleUpload(next)
  }

  /**
   * 加入上传队列；如果正在上传，则排队等待，否则立即上传。
   */
  const enqueueUpload = (files) => {
    const list = Array.from(files || [])
    if (!list.length) return
    if (splitCompleted.value || splitting.value) { pushToast('error', '已分割完成，请先重新开始'); return }
    const isFreshStart = pendingFiles.length === 0
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
    handleUpload(list, { resetSession: isFreshStart })
  }

  /**
   * 请求后端撤销单个文件，并清理前端相关列表、进度和选择状态。
   */
  const doCancelFile = async (key, step) => {
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
      }
      pushToast('success', data.message || '已撤销')
      if (!pendingFiles.length && activeXhr) {
        try { activeXhr.abort() } catch (_) {}
      }
    } catch (_) { pushToast('error', '撤销失败: 网络错误') }
  }

  /**
   * 从待上传列表删除文件；已上传到后端的文件走撤销接口。
   */
  const removePendingFile = async (key) => {
    if (!key || splitting.value || splitCompleted.value) return
    if (uploadBusy.value || uploadReady.value) { await doCancelFile(key, S.value); return }
    const idx = pendingFiles.findIndex(x => x.key === key)
    if (idx >= 0) pendingFiles.splice(idx, 1)
    delete fileProgress[key]
    waitingKeys.delete(key)
    for (let i = uploadQueue.length - 1; i >= 0; i--) {
      uploadQueue[i] = (uploadQueue[i] || []).filter(f => fileKey(f) !== key)
      if (!uploadQueue[i].length) uploadQueue.splice(i, 1)
    }
  }

  /**
   * 重置整个上传会话，包括后端临时文件、前端队列、进度和题目结果。
   */
  const doReset = async (modelOptionsData, selectedLlmOptionId, step) => {
    if (activeXhr) {
      try { activeXhr.abort() } catch (_) {}
      activeXhr = null
    }
    stopFakeProgress()
    try {
      await api.resetUploadSession()
    } catch (_) {
      // 后端清理失败不阻断前端重置，避免页面卡死
    }
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
    
    if (modelOptionsData && modelOptionsData.value && modelOptionsData.value.default_option_id) {
      selectedLlmOptionId.value = modelOptionsData.value.default_option_id
    }
    pushToast('success', '已重置')
  }

  return {
    uploadBusy, uploadReady, pendingFiles, pendingPreviewUrls,
    fileProgress, waitingKeys,
    enqueueUpload, removePendingFile, stopFakeProgress, doReset,
  }
}
