import { assertJsonSuccess } from './client.js'

export async function fetchModelOptions() {
  const resp = await fetch('/api/models/options')
  return assertJsonSuccess(resp, 'Failed to fetch model options')
}

export async function updateModelSelection(optionId) {
  const resp = await fetch('/api/models/selection', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ option_id: optionId }),
  })
  return assertJsonSuccess(resp, 'Failed to save model selection')
}

export async function fetchAppConfig() {
  const resp = await fetch('/api/config')
  const data = await assertJsonSuccess(resp, 'Failed to fetch config')
  return data.config
}

export async function updateAppConfig(config) {
  const resp = await fetch('/api/config', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  return assertJsonSuccess(resp, 'Failed to update config')
}

export async function fetchAdminSystemConfig() {
  const resp = await fetch('/api/admin/system-config')
  const data = await assertJsonSuccess(resp, 'Failed to fetch system config')
  return data.config
}

export async function updateAdminSystemConfig(config) {
  const resp = await fetch('/api/admin/system-config', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  return assertJsonSuccess(resp, 'Failed to update system config')
}

export async function fetchStatus() {
  const resp = await fetch('/api/status')
  const data = await assertJsonSuccess(resp, 'Failed to fetch system status')
  return data.status
}
