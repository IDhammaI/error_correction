/**
 * API 调用层 — 集中管理所有 fetch 请求
 */

export async function fetchStatus() {
  const resp = await fetch('/api/status')
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data.status
  throw new Error((data && data.error) || '获取系统状态失败')
}

export async function cancelFile(fileKey) {
  const resp = await fetch('/api/cancel_file', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_key: fileKey }),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json().catch(() => null)
  if (data && data.success) return data
  throw new Error((data && data.error) || '撤销失败')
}

export function uploadFiles(formData, { onProgress, onSuccess, onError, onAbort }) {
  const xhr = new XMLHttpRequest()
  xhr.open('POST', '/api/upload', true)

  if (onProgress) {
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) onProgress(e.loaded / e.total)
    })
  }

  xhr.addEventListener('load', () => {
    let data = null
    try { data = JSON.parse(xhr.responseText) } catch (_) {}
    if (data && data.success) {
      onSuccess?.(data)
    } else {
      onError?.((data && data.error) || '文件处理失败')
    }
  })

  xhr.addEventListener('error', () => onError?.('上传失败: 网络错误'))
  xhr.addEventListener('abort', () => onAbort?.())

  xhr.send(formData)
  return xhr
}

export async function splitQuestions(modelProvider) {
  const resp = await fetch('/api/split', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_provider: modelProvider }),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data
  throw new Error((data && data.error) || '题目分割失败')
}

export async function exportQuestions(selectedIds) {
  const resp = await fetch('/api/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selected_ids: selectedIds }),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const data = await resp.json()
  if (data && data.success) return data
  throw new Error((data && data.error) || '导出失败')
}
