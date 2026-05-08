import { computed, ref } from 'vue'
import * as api from '@/api.js'

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

function normalizeType(projectType) {
  return projectType === 'note' ? 'note' : 'question'
}

function persistActiveProject(id, projectType = 'question') {
  const key = STORAGE_KEYS[normalizeType(projectType)]
  try {
    if (id) localStorage.setItem(key, String(id))
    else localStorage.removeItem(key)
  } catch (_) { }
}

function setActiveProject(id, projectType) {
  const type = normalizeType(projectType || projects.value.find(p => String(p.id) === String(id))?.project_type)
  const value = id ? Number(id) : null
  if (type === 'note') activeNoteProjectId.value = value
  else activeQuestionProjectId.value = value
  persistActiveProject(value, type)
}

function pickActiveProject(list, projectType) {
  let saved = null
  try { saved = localStorage.getItem(STORAGE_KEYS[projectType]) } catch (_) { }
  const savedExists = saved && list.some(p => String(p.id) === String(saved))
  return savedExists ? saved : (list[0]?.id || null)
}

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

async function createAndSelectProject(name, projectType = 'question') {
  const type = normalizeType(projectType)
  const project = await api.createProject({ name, project_type: type })
  projects.value = sortProjects([project, ...projects.value.filter(p => p.id !== project.id)])
  setActiveProject(project.id, type)
  return project
}

async function renameProject(projectId, name) {
  const project = await api.updateProject(projectId, { name })
  projects.value = sortProjects(projects.value.map(p => p.id === project.id ? project : p))
  return project
}

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
