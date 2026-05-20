import { computed, ref } from 'vue'
import * as api from '@/api/index.js'

/**
 * useProjects.js
 * 管理错题库项目与笔记本项目的全局列表和当前选中项。
 */
const STORAGE_KEYS = {
  question: 'active_question_project_id_v1',
  note: 'active_note_project_id_v1',
}

const projects = ref([])
const activeQuestionProjectId = ref(null)
const activeNoteProjectId = ref(null)
const loadingProjects = ref(false)

const questionProjects = computed(() => projects.value.filter(p => (p.project_type || 'question') === 'question'))
const noteProjects = computed(() => projects.value.filter(p => p.project_type === 'note'))
const activeQuestionProject = computed(() =>
  questionProjects.value.find(p => String(p.id) === String(activeQuestionProjectId.value)) || null
)
const activeNoteProject = computed(() =>
  noteProjects.value.find(p => String(p.id) === String(activeNoteProjectId.value)) || null
)

/**
 * 按项目类型、更新时间、ID 排序，确保列表展示稳定且最新项目靠前。
 */
function sortProjects(list) {
  return [...list].sort((a, b) => {
    const typeCompare = String(a.project_type || 'question').localeCompare(String(b.project_type || 'question'))
    if (typeCompare) return typeCompare
    const aTime = Date.parse(a.updated_at || a.created_at || '') || 0
    const bTime = Date.parse(b.updated_at || b.created_at || '') || 0
    if (aTime !== bTime) return bTime - aTime
    return Number(b.id || 0) - Number(a.id || 0)
  })
}

/**
 * 规范化项目类型，未知类型默认按错题库处理。
 */
function normalizeType(projectType) {
  return projectType === 'note' ? 'note' : 'question'
}

/**
 * 持久化当前选中的项目 ID，刷新页面后可以恢复。
 */
function persistActiveProject(id, projectType = 'question') {
  const key = STORAGE_KEYS[normalizeType(projectType)]
  try {
    if (id) localStorage.setItem(key, String(id))
    else localStorage.removeItem(key)
  } catch (_) { }
}

/**
 * 设置当前项目，并根据项目类型写入对应的选中状态。
 */
function setActiveProject(id, projectType) {
  const type = normalizeType(projectType || projects.value.find(p => String(p.id) === String(id))?.project_type)
  const value = id ? Number(id) : null
  if (type === 'note') activeNoteProjectId.value = value
  else activeQuestionProjectId.value = value
  persistActiveProject(value, type)
}

/**
 * 优先恢复本地保存的项目；保存项不存在时回退到列表第一项。
 */
function pickActiveProject(list, projectType) {
  let saved = null
  try { saved = localStorage.getItem(STORAGE_KEYS[projectType]) } catch (_) { }
  const savedExists = saved && list.some(p => String(p.id) === String(saved))
  return savedExists ? saved : (list[0]?.id || null)
}

/**
 * 从后端加载项目列表，并初始化错题库/笔记本各自的当前项目。
 */
async function loadProjects() {
  loadingProjects.value = true
  try {
    const list = await api.fetchProjects()
    projects.value = sortProjects(list.filter(p => !p.is_default))
    setActiveProject(pickActiveProject(questionProjects.value, 'question'), 'question')
    setActiveProject(pickActiveProject(noteProjects.value, 'note'), 'note')
    return projects.value
  } finally {
    loadingProjects.value = false
  }
}

/**
 * 创建项目后立即选中，供新建错题库或笔记本流程使用。
 */
async function createAndSelectProject(name, projectType = 'question') {
  const type = normalizeType(projectType)
  const project = await api.createProject({ name, project_type: type })
  projects.value = sortProjects([project, ...projects.value.filter(p => p.id !== project.id)])
  setActiveProject(project.id, type)
  return project
}

/**
 * 重命名项目，并把返回的新项目数据同步回本地列表。
 */
async function renameProject(projectId, name) {
  const project = await api.updateProject(projectId, { name })
  projects.value = sortProjects(projects.value.map(p => p.id === project.id ? project : p))
  return project
}

/**
 * 删除项目；如果删掉的是当前项目，则自动切换到同类型的下一项。
 */
async function removeProject(projectId) {
  const project = projects.value.find(p => p.id === projectId)
  const type = normalizeType(project?.project_type)
  await api.deleteProject(projectId)
  projects.value = projects.value.filter(p => p.id !== projectId)
  if (type === 'note' && String(activeNoteProjectId.value) === String(projectId)) {
    setActiveProject(noteProjects.value[0]?.id || null, 'note')
  }
  if (type === 'question' && String(activeQuestionProjectId.value) === String(projectId)) {
    setActiveProject(questionProjects.value[0]?.id || null, 'question')
  }
}

/**
 * 暴露项目列表、当前项目和项目增删改查动作。
 */
export function useProjects() {
  return {
    projects,
    questionProjects,
    noteProjects,
    activeProject: activeQuestionProject,
    activeProjectId: activeQuestionProjectId,
    activeQuestionProject,
    activeQuestionProjectId,
    activeNoteProject,
    activeNoteProjectId,
    loadingProjects,
    loadProjects,
    setActiveProject,
    createAndSelectProject,
    renameProject,
    removeProject,
  }
}
