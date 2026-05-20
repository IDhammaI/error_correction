/**
 * 系统配置 API。
 *
 * 包含模型选项、应用配置、管理员系统配置和运行状态。
 */
import { assertJsonSuccess } from './client.js'

/** 获取可选模型列表，用于设置页和工作台模型选择。 */
export async function fetchModelOptions() {
  const resp = await fetch('/api/models/options')
  return assertJsonSuccess(resp, '获取模型选项失败')
}

/** 获取普通应用配置，返回后端 config 字段。 */
export async function fetchAppConfig() {
  const resp = await fetch('/api/config')
  const data = await assertJsonSuccess(resp, '获取配置失败')
  return data.config
}

/** 更新普通应用配置，适用于用户可编辑的配置项。 */
export async function updateAppConfig(config) {
  const resp = await fetch('/api/config', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  return assertJsonSuccess(resp, '更新配置失败')
}

/** 获取管理员级系统配置，通常用于更高权限的配置面板。 */
export async function fetchAdminSystemConfig() {
  const resp = await fetch('/api/admin/system-config')
  const data = await assertJsonSuccess(resp, '获取系统配置失败')
  return data.config
}

/** 更新管理员级系统配置。 */
export async function updateAdminSystemConfig(config) {
  const resp = await fetch('/api/admin/system-config', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  return assertJsonSuccess(resp, '更新系统配置失败')
}

/** 获取后端运行状态和模型配置状态。 */
export async function fetchStatus() {
  const resp = await fetch('/api/status')
  const data = await assertJsonSuccess(resp, '获取系统状态失败')
  return data.status
}
