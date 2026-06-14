import { ref, watch, inject } from 'vue'
import * as api from '@/api/index.js'
import { useAuth } from '@/composables/useAuth.js'
import { useProjects } from '@/composables/useProjects.js'

const QUOTA_EXCEEDED_CODE = 'DAILY_FREE_QUOTA_EXCEEDED'

/**
 * useSplitPipeline.js
 * 串联“擦除空白、OCR、AI 分割、笔记整理、导出、入库”的工作台主流程。
 */
export function useSplitPipeline(pushToast, currentView, step, S, uploadReady, splitting, splitCompleted, uploadMode, selectedLlmOption, questions, selectedIds, pendingFiles, typesetMath) {
  const openProjectDialog = inject('openProjectDialog', null)
  const { setQuotaSnapshot, refreshCurrentUser } = useAuth()
  const { activeQuestionProjectId, activeNoteProjectId, noteProjects, setActiveProject, loadProjects } = useProjects()
  const eraseLoading = ref(false)
  const eraseImages = ref([])
  const eraseDone = ref(false)
  const ocrLoading = ref(false)
  const ocrPages = ref([])
  const ocrDone = ref(false)
  const eraseEnabled = ref(true)
  const currentRunId = ref(null)
  const currentRecordId = ref(null)

  // ── 笔记本项目选择弹窗 ────────────────────────────────
  const noteProjectDialogOpen = ref(false)
  const noteTargetProjectId = ref(null)
  const noteProjectSaving = ref(false)

  // 笔记模式默认不启用擦除，试卷模式默认启用
  watch(uploadMode, (mode) => {
    eraseEnabled.value = mode !== 'note'
  })

  /**
   * 从接口错误里同步额度快照，并判断是否命中免费额度耗尽。
   */
  const syncQuotaFromError = (error) => {
    if (error?.quota) setQuotaSnapshot(error.quota)
    return error?.code === QUOTA_EXCEEDED_CODE
  }

  /**
   * 主流程成功后刷新用户额度，让页面展示和后端额度保持一致。
   */
  const refreshQuotaSnapshot = async () => {
    try {
      await refreshCurrentUser()
    } catch (_) { }
  }

  /**
   * 根据是否启用擦除，决定从擦除步骤还是 OCR 步骤开始。
   */
  const startProcess = () => {
    if (eraseEnabled.value) {
      doErase()
    } else {
      doOcr()
    }
  }

  /**
   * 调用后端擦除接口，生成去除手写痕迹后的预览图。
   */
  const doErase = async () => {
    if (eraseLoading.value) return
    eraseLoading.value = true
    eraseDone.value = false
    eraseImages.value = []
    currentView.value = 'workspace_review'
    step.value = S.value.ERASE
    try {
      const data = await api.runErase()
      eraseImages.value = data.images || []
      eraseDone.value = true
      pushToast('success', data.message || '擦除完成')
    } catch (e) {
      pushToast('error', e.message || '擦除失败')
      currentView.value = 'workspace'
      step.value = S.value.UPLOAD
    } finally {
      eraseLoading.value = false
    }
  }

  /**
   * 调用 OCR 接口识别上传图片或 PDF，并同步扣减后的额度。
   */
  const doOcr = async () => {
    if (ocrLoading.value) return
    ocrLoading.value = true
    ocrDone.value = false
    ocrPages.value = []
    eraseDone.value = false
    currentView.value = 'workspace_review'
    step.value = S.value.OCR
    try {
      const data = await api.runOcr()
      ocrPages.value = data.pages || []
      ocrDone.value = true
      await refreshQuotaSnapshot()
      pushToast('success', `OCR 完成，共 ${data.pages?.length || 0} 页`)
    } catch (e) {
      if (syncQuotaFromError(e)) {
        pushToast('error', e.message || '今日免费体验次数已用完')
      } else {
        pushToast('error', e.message || 'OCR 失败')
      }
      currentView.value = 'workspace'
      step.value = S.value.UPLOAD
    } finally {
      ocrLoading.value = false
    }
  }

  /**
   * 根据上传模式分流：错题模式执行 AI 分割，笔记模式执行笔记整理。
   */
  const doSplit = async () => {
    if (!uploadReady.value || splitting.value || splitCompleted.value) return

    if (uploadMode.value === 'note') {
      openNoteProjectDialog()
      return
    }

    splitting.value = true
    currentRunId.value = null
    ocrDone.value = false
    step.value = S.value.SPLIT
    pushToast('info', '正在调用AI分割题目，请稍候...', 1800)
    try {
      const data = await api.splitQuestions(
        selectedLlmOption.value?.category || 'openai',
        selectedLlmOption.value?.model_name || '',
        selectedLlmOption.value?.source || '',
        selectedLlmOption.value?.provider_id || ''
      )
      currentRunId.value = data.run_id || null
      questions.value = data.questions || []
      selectedIds.clear()
      if (data.warnings && data.warnings.length) {
        for (const w of data.warnings) pushToast('warning', w, 6000)
      }
      if (questions.value.length > 0) {
        splitCompleted.value = true
        step.value = S.value.EXPORT
        if (!data.warnings || !data.warnings.length) {
          pushToast('success', `成功分割 ${questions.value.length} 道题目`)
        }
        await typesetMath()
        await refreshQuotaSnapshot()
        setTimeout(() => {
          if (currentView.value === 'workspace') {
            currentView.value = 'workspace_review'
          }
        }, 800)
      }
    } catch (e) {
      if (syncQuotaFromError(e)) {
        pushToast('error', e.message || '今日免费体验次数已用完')
      } else {
        pushToast('error', '分割失败: ' + (e instanceof Error ? e.message : String(e)))
      }
    } finally {
      splitting.value = false
    }
  }

  /**
   * 打开笔记本项目选择弹窗。
   */
  const openNoteProjectDialog = () => {
    if (!noteProjects.value.length) {
      if (openProjectDialog) {
        openProjectDialog('note')
      } else {
        pushToast('error', '请先创建一个笔记本')
      }
      return
    }
    noteTargetProjectId.value = activeNoteProjectId.value || noteProjects.value[0]?.id || null
    noteProjectDialogOpen.value = true
  }

  const closeNoteProjectDialog = () => {
    if (noteProjectSaving.value) return
    noteProjectDialogOpen.value = false
  }

  /**
   * 确认选择笔记本后执行笔记整理。
   */
  const confirmNoteOrganize = async () => {
    if (!noteTargetProjectId.value || noteProjectSaving.value) return
    noteProjectSaving.value = true
    noteProjectDialogOpen.value = false
    try {
      await _doNoteOrganize(noteTargetProjectId.value)
    } finally {
      noteProjectSaving.value = false
    }
  }

  /**
   * 将上传文件提交给笔记整理接口，生成笔记后切换到笔记视图。
   */
  const _doNoteOrganize = async (targetProjectId) => {
    splitting.value = true
    currentRunId.value = null
    step.value = S.value.SPLIT
    pushToast('info', '正在调用AI整理笔记，请稍候...', 3000)
    try {
      const formData = new FormData()
      for (const pf of pendingFiles) {
        if (pf.file) {
          const newFile = new File([pf.file], pf.file.name, { type: pf.file.type, lastModified: pf.file.lastModified })
          formData.append('files', newFile)
        }
      }
      formData.append('model_provider', selectedLlmOption.value?.category || 'openai')
      if (selectedLlmOption.value?.model_name) {
        formData.append('model_name', selectedLlmOption.value.model_name)
      }
      if (selectedLlmOption.value?.source) {
        formData.append('provider_source', selectedLlmOption.value.source)
      }
      if (selectedLlmOption.value?.provider_id) {
        formData.append('provider_id', selectedLlmOption.value.provider_id)
      }
      formData.append('project_id', targetProjectId)

      await new Promise((resolve, reject) => {
        api.createNote(formData, {
          onSuccess: (data) => resolve(data),
          onError: (error) => reject(error),
        })
      })
      await loadProjects()

      splitCompleted.value = true
      step.value = S.value.EXPORT
      await refreshQuotaSnapshot()
      pushToast('success', '笔记整理完成！')

      setTimeout(() => {
        currentView.value = 'notes'
      }, 800)
    } catch (e) {
      if (syncQuotaFromError(e)) {
        pushToast('error', e.message || '今日免费体验次数已用完')
      } else {
        pushToast('error', '笔记整理失败: ' + (e instanceof Error ? e.message : String(e)))
      }
    } finally {
      splitting.value = false
    }
  }

  /**
   * 导出选中的错题，并触发浏览器下载生成的 markdown 文件。
   */
  const doExport = async () => {
    if (!selectedIds.size) { pushToast('error', '请至少选择一道题目！'); return }
    try {
      const data = await api.exportQuestions(Array.from(selectedIds), currentRunId.value)
      step.value = S.value.EXPORT + 1
      pushToast('success', `错题本导出成功！已保存到: ${data.output_path}`)
      let filename = 'wrongbook.md'
      if (data.output_path) {
        const parts = String(data.output_path).split(/[/\\]/)
        const last = parts[parts.length - 1]
        if (last) filename = last
      }
      let downloadHref = data.download_url || `/download/${encodeURIComponent(filename)}`
      downloadHref += downloadHref.includes('?') ? `&t=${Date.now()}` : `?t=${Date.now()}`
      const a = document.createElement('a')
      a.href = downloadHref
      a.download = filename
      a.style.display = 'none'
      document.body.appendChild(a)
      a.click()
      a.remove()
    } catch (e) {
      pushToast('error', '导出失败: ' + (e instanceof Error ? e.message : String(e)))
    }
  }

  /**
   * 把选中的错题保存到当前错题库，并刷新错题库页面。
   */
  const doSaveToDb = async (targetProjectId, errorBankRef) => {
    if (!selectedIds.size) { pushToast('error', '请至少选择一道题目！'); return false }
    try {
      const projectId = targetProjectId || activeQuestionProjectId.value
      if (!projectId) { pushToast('error', '请先创建并选择一个错题库'); return false }
      const answers = questions.value
        .filter(q => selectedIds.has(q.uid) && (q.answer || q.user_answer))
        .map(q => ({ uid: q.uid, answer: q.answer || '', user_answer: q.user_answer || '' }))
      const data = await api.saveToDb(Array.from(selectedIds), answers, currentRunId.value, projectId, currentRecordId.value)
      await loadProjects()
      pushToast('success', data.message || '已导入错题库')
      errorBankRef?.value?.refresh()
      return true
    } catch (e) {
      pushToast('error', '导入失败: ' + (e instanceof Error ? e.message : String(e)))
      return false
    }
  }

  /**
   * 设置当前记录 ID（用于历史记录导入场景）。
   */
  const setCurrentRecordId = (id) => {
    currentRecordId.value = id
  }

  return {
    eraseEnabled, eraseLoading, eraseImages, eraseDone,
    ocrLoading, ocrPages, ocrDone,
    currentRunId, currentRecordId, setCurrentRecordId,
    startProcess, doErase, doOcr, doSplit, doExport, doSaveToDb,
    // 笔记本项目选择弹窗
    noteProjectDialogOpen, noteTargetProjectId, noteProjectSaving,
    noteProjects, closeNoteProjectDialog, confirmNoteOrganize,
  }
}
