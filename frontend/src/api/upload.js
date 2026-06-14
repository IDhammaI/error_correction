/**
 * 上传处理流程 API。
 *
 * 覆盖文件上传、擦除预处理、OCR、题目分割、导出和保存到错题库。
 */
import { assertJsonSuccess, buildModelBody, createNetworkError, handleXhrJsonResult } from './client.js'

/** 从当前上传会话中撤销指定文件。 */
export async function cancelFile(fileKey) {
  const resp = await fetch('/api/cancel_file', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_key: fileKey }),
  })
  return assertJsonSuccess(resp, '撤销失败')
}

/** 重置后端上传会话，清理本轮上传和处理状态。 */
export async function resetUploadSession() {
  const resp = await fetch('/api/upload/reset', {
    method: 'POST',
  })
  return assertJsonSuccess(resp, '重置上传会话失败')
}

/** 上传文件并通过回调返回进度、成功、失败和取消状态。 */
export function uploadFiles(formData, { onProgress, onSuccess, onError, onAbort }) {
  // 文件上传需要进度回调，fetch 目前无法稳定提供上传进度，因此保留 XHR。
  const xhr = new XMLHttpRequest()
  xhr.open('POST', '/api/upload', true)

  if (onProgress) {
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) onProgress(e.loaded / e.total)
    })
  }

  xhr.addEventListener('load', () => {
    let data = null
    try { data = JSON.parse(xhr.responseText) } catch (_) { }
    handleXhrJsonResult(xhr, data, '文件处理失败', onSuccess, onError)
  })

  xhr.addEventListener('error', () => onError?.(createNetworkError('上传失败: 网络错误')))
  xhr.addEventListener('abort', () => onAbort?.())

  xhr.send(formData)
  return xhr
}

/** 执行擦除预处理，生成后续 OCR 使用的中间图片。 */
export async function runErase() {
  const resp = await fetch('/api/erase', { method: 'POST' })
  return assertJsonSuccess(resp, '擦除失败')
}

/** 执行 OCR 识别，将上传图片转换为可供分题的文本结构。 */
export async function runOcr() {
  const resp = await fetch('/api/ocr', { method: 'POST' })
  return assertJsonSuccess(resp, 'OCR 执行失败')
}

/** 调用大模型执行题目分割，模型参数按当前选择透传。 */
export async function splitQuestions(modelProvider, modelName, providerSource, providerId) {
  const resp = await fetch('/api/split', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(buildModelBody(modelProvider, modelName, providerSource, providerId)),
  })
  return assertJsonSuccess(resp, '题目分割失败')
}

/** 导出当前分割结果中选中的题目。 */
export async function exportQuestions(selectedIds, runId) {
  const body = { selected_ids: selectedIds }
  if (runId) body.run_id = runId
  const resp = await fetch('/api/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return assertJsonSuccess(resp, '导出失败')
}

/** 将选中的分割题目和答案保存到错题库。 */
export async function saveToDb(selectedIds, answers = [], runId, projectId) {
  const body = { selected_ids: selectedIds, answers }
  if (runId) body.run_id = runId
  if (projectId) body.project_id = projectId
  const resp = await fetch('/api/save-to-db', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return assertJsonSuccess(resp, '导入错题库失败')
}
