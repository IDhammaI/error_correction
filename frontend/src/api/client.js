/**
 * API 公共客户端工具。
 *
 * 后端接口统一返回 success/error/code/quota 等业务字段，本文件负责把
 * HTTP 错误和业务失败统一转换成前端可识别的 Error 对象。
 */
/** 创建带 HTTP 状态、业务错误码和额度信息的统一错误对象。 */
function createApiError(message, { status, code, quota } = {}) {
  const error = new Error(message || '请求失败')
  error.status = status ?? null
  error.code = code ?? null
  error.quota = quota ?? null
  return error
}

/** 从后端错误响应中提取可展示的错误消息，没有业务消息时使用兜底文案。 */
function getErrorMessage(data, fallback, status) {
  return (data && (data.error || data.message)) || fallback || `HTTP ${status}`
}

/** 组装模型调用请求体，兼容默认模型、自定义 provider 和额外业务参数。 */
export function buildModelBody(modelProvider, modelName, providerSource, providerId, extra = {}) {
  const body = { model_provider: modelProvider, ...extra }
  if (modelName) body.model_name = modelName
  if (providerSource) body.provider_source = providerSource
  if (providerId) body.provider_id = providerId
  return body
}

/** 创建网络层错误，供 XHR error 事件复用统一错误结构。 */
export function createNetworkError(message, detail) {
  return createApiError(message, detail)
}

/** 安全读取 JSON 响应，避免非 JSON 错误页导致二次异常。 */
export async function readJsonSafely(resp) {
  // 后端异常或空响应体可能不是合法 JSON，调用方仍需要拿到统一错误。
  return resp.json().catch(() => null)
}

/** 校验 fetch 响应和后端 success 字段，失败时抛出统一错误对象。 */
export async function assertJsonSuccess(resp, fallbackMessage) {
  const data = await readJsonSafely(resp)
  if (!resp.ok) {
    throw createApiError(getErrorMessage(data, fallbackMessage, resp.status), {
      status: resp.status,
      code: data?.code,
      quota: data?.quota,
    })
  }
  if (data && data.success) return data
  throw createApiError(getErrorMessage(data, fallbackMessage, resp.status), {
    status: resp.status,
    code: data?.code,
    quota: data?.quota,
  })
}

/** 统一处理 XHR 返回的 JSON 结果，把成功和失败分发给调用方回调。 */
export function handleXhrJsonResult(xhr, data, fallbackMessage, onSuccess, onError) {
  // 上传类接口使用 XHR，成功判断仍复用后端的 success 字段。
  if (xhr.status >= 200 && xhr.status < 300 && data?.success) {
    onSuccess?.(data)
    return
  }
  onError?.(createApiError(getErrorMessage(data, fallbackMessage, xhr.status), {
    status: xhr.status,
    code: data?.code,
    quota: data?.quota,
  }))
}
