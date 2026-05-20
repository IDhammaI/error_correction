/**
 * 项目管理 API。
 *
 * 负责错题与笔记所属项目的列表、创建、更新和删除。
 */
import { assertJsonSuccess } from './client.js'

/** 获取当前用户的项目列表。 */
export async function fetchProjects() {
  const resp = await fetch('/api/projects')
  const data = await assertJsonSuccess(resp, '获取项目列表失败')
  return data.projects || []
}

/** 创建项目，并返回新建的 project 对象。 */
export async function createProject(payload) {
  const resp = await fetch('/api/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const data = await assertJsonSuccess(resp, '创建项目失败')
  return data.project
}

/** 更新项目名称或其它项目元数据。 */
export async function updateProject(projectId, payload) {
  const resp = await fetch(`/api/projects/${encodeURIComponent(projectId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const data = await assertJsonSuccess(resp, '更新项目失败')
  return data.project
}

/** 删除指定项目，后端负责处理关联数据约束。 */
export async function deleteProject(projectId) {
  const resp = await fetch(`/api/projects/${encodeURIComponent(projectId)}`, {
    method: 'DELETE',
  })
  return assertJsonSuccess(resp, '删除项目失败')
}
