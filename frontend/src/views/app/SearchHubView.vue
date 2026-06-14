<script setup>
/**
 * SearchHubView.vue
 * 库页面：Linear Projects 风格的项目列表。
 */
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseDropdown from '@/components/base/BaseDropdown.vue'
import BaseEmptyState from '@/components/base/BaseEmptyState.vue'
import BaseModal from '@/components/base/BaseModal.vue'
import BaseSearchInput from '@/components/base/BaseSearchInput.vue'
import BaseSegmented from '@/components/base/BaseSegmented.vue'
import ContentPanel from '@/components/features/app/layout/ContentPanel.vue'
import ErrorBankView from '@/views/app/ErrorBankView.vue'
import NoteView from '@/views/app/NoteView.vue'
import { useProjects } from '@/composables/useProjects.js'
import { useToast } from '@/composables/useToast.js'

defineProps({
  mode: { type: String, default: 'library' },
})

const { pushToast } = useToast()
const route = useRoute()
const router = useRouter()
const {
  projects,
  questionProjects,
  noteProjects,
  loadingProjects,
  loadProjects,
  setActiveProject,
  createAndSelectProject,
  renameProject,
  updateProjectMeta,
  removeProject,
} = useProjects()

const query = ref('')
const activeType = ref('all')
const actionMenuProjectId = ref(null)

const projectDialogOpen = ref(false)
const projectDialogMode = ref('create')
const projectDialogTarget = ref(null)
const projectType = ref('question')
const projectName = ref('')
const projectSummary = ref('')
const projectDescription = ref('')
const projectSaving = ref(false)

const renameDialogOpen = ref(false)
const renameTarget = ref(null)
const renameText = ref('')
const renameSaving = ref(false)

const deleteDialogOpen = ref(false)
const deleteTarget = ref(null)
const deleteSaving = ref(false)

const projectTypeOptions = computed(() => [
  { value: 'all', label: `全部 ${projects.value.length}` },
  { value: 'question', label: `错题库 ${questionProjects.value.length}` },
  { value: 'note', label: `笔记本 ${noteProjects.value.length}` },
])

const libraryStats = computed(() => {
  const totalQuestions = projects.value.reduce((sum, project) => sum + (project.question_count || 0), 0)
  const totalNotes = projects.value.reduce((sum, project) => sum + (project.note_count || 0), 0)
  return [
    { label: '全部项目', value: projects.value.length, icon: 'fa-box-archive', tone: 'accent' },
    { label: '错题库', value: questionProjects.value.length, icon: 'fa-database', tone: 'blue' },
    { label: '笔记本', value: noteProjects.value.length, icon: 'fa-book-open', tone: 'emerald' },
    { label: '总题目', value: totalQuestions, icon: 'fa-list-check', tone: 'amber' },
    { label: '总笔记', value: totalNotes, icon: 'fa-note-sticky', tone: 'orange' },
  ]
})

const editTypeOptions = [
  { value: 'question', label: '错题库' },
  { value: 'note', label: '笔记本' },
]

function decorateProject(project) {
  const type = project.project_type === 'note' ? 'note' : 'question'
  const count = type === 'note' ? (project.note_count || 0) : (project.question_count || 0)
  return {
    ...project,
    normalizedType: type,
    typeLabel: type === 'note' ? '笔记本' : '错题库',
    icon: type === 'note' ? 'fa-book-open' : 'fa-database',
    descriptionText: project.summary?.trim() || project.description?.trim() || '',
    count,
    updatedAt: project.updated_at || project.created_at,
  }
}

const allProjectRows = computed(() => projects.value.map(decorateProject))

const projectRows = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  return allProjectRows.value
    .filter((project) => activeType.value === 'all' || (project.project_type || 'question') === activeType.value)
    .filter((project) => {
      if (!keyword) return true
      return [
        project.name,
        project.description,
        project.project_type === 'note' ? '笔记本' : '错题库',
      ].filter(Boolean).join(' ').toLowerCase().includes(keyword)
    })
})

const activeLibraryProject = computed(() => {
  const id = route.params.subview
  if (!id) return null
  return allProjectRows.value.find(project =>
    String(project.id) === String(id) || String(project.public_id || '') === String(id),
  ) || null
})

const isProjectDetail = computed(() => Boolean(route.params.subview))

const breadcrumbs = computed(() => {
  const root = { label: '库', icon: 'fa-box-archive', iconClass: 'accent-text', onClick: openLibraryRoot }
  if (!activeLibraryProject.value) return [root]
  return [root, { label: activeLibraryProject.value.name, icon: activeLibraryProject.value.icon }]
})

const projectDialogTitle = computed(() => projectDialogMode.value === 'edit' ? '编辑项目' : '新项目')
const projectDialogActionText = computed(() => {
  if (projectSaving.value) return projectDialogMode.value === 'edit' ? '保存中...' : '创建中...'
  return projectDialogMode.value === 'edit' ? '保存修改' : '创建项目'
})
const currentProjectTypeLabel = computed(() => projectType.value === 'note' ? '笔记本' : '错题库')

function formatDate(value) {
  if (!value) return 'No date'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'No date'
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function formatUpdated(value) {
  if (!value) return '暂无记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '暂无记录'
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const day = new Date(date)
  day.setHours(0, 0, 0, 0)
  const diffDays = Math.round((today - day) / 86400000)
  if (diffDays === 0) return '今天'
  if (diffDays === 1) return '昨天'
  if (diffDays > 1 && diffDays < 30) return `${diffDays} 天前`
  return formatDate(value)
}

function formatCount(project) {
  if (project.normalizedType === 'note') return `${project.count} 篇笔记`
  return `${project.count} 道题`
}

function resetProjectDialog() {
  projectDialogTarget.value = null
  projectType.value = 'question'
  projectName.value = ''
  projectSummary.value = ''
  projectDescription.value = ''
}

function projectRouteId(project) {
  return project.public_id || project.id
}

function openProject(project) {
  setActiveProject(project.id, project.normalizedType)
  router.push(`/app/library/${projectRouteId(project)}`)
}

function openLibraryRoot() {
  router.push('/app/library')
}

function openCreateDialog() {
  resetProjectDialog()
  projectDialogMode.value = 'create'
  projectDialogOpen.value = true
}

function openEditDialog(project) {
  projectDialogMode.value = 'edit'
  projectDialogTarget.value = project
  projectType.value = project.normalizedType
  projectName.value = project.name || ''
  projectSummary.value = project.summary || ''
  projectDescription.value = project.description || ''
  projectDialogOpen.value = true
  actionMenuProjectId.value = null
}

function closeProjectDialog() {
  if (projectSaving.value) return
  projectDialogOpen.value = false
  resetProjectDialog()
}

async function handleSaveProject() {
  const name = projectName.value.trim()
  if (!name || projectSaving.value) return

  projectSaving.value = true
  const summary = projectSummary.value.trim()
  const description = projectDescription.value.trim()
  try {
    if (projectDialogMode.value === 'edit') {
      await updateProjectMeta(projectDialogTarget.value.id, {
        name,
        summary,
        description,
      })
      pushToast('success', '项目已更新')
    } else {
      const project = await createAndSelectProject(name, projectType.value, description, summary)
      router.push(`/app/library/${projectRouteId(project)}`)
      pushToast('success', '项目已创建')
    }
    projectDialogOpen.value = false
    resetProjectDialog()
  } catch (error) {
    pushToast('error', error instanceof Error ? error.message : '保存项目失败')
  } finally {
    projectSaving.value = false
  }
}

function openRenameDialog(project) {
  renameTarget.value = project
  renameText.value = project.name || ''
  renameDialogOpen.value = true
  actionMenuProjectId.value = null
}

function closeRenameDialog() {
  if (renameSaving.value) return
  renameDialogOpen.value = false
  renameTarget.value = null
  renameText.value = ''
}

async function confirmRename() {
  const name = renameText.value.trim()
  if (!name || !renameTarget.value || renameSaving.value) return
  renameSaving.value = true
  try {
    await renameProject(renameTarget.value.id, name)
    pushToast('success', '项目已重命名')
    closeRenameDialog()
  } catch (error) {
    pushToast('error', error instanceof Error ? error.message : '重命名失败')
  } finally {
    renameSaving.value = false
  }
}

function openDeleteDialog(project) {
  deleteTarget.value = project
  deleteDialogOpen.value = true
  actionMenuProjectId.value = null
}

function closeDeleteDialog() {
  if (deleteSaving.value) return
  deleteDialogOpen.value = false
  deleteTarget.value = null
}

async function confirmDelete() {
  if (!deleteTarget.value || deleteSaving.value) return
  deleteSaving.value = true
  try {
    await removeProject(deleteTarget.value.id)
    pushToast('success', '项目已删除')
    closeDeleteDialog()
  } catch (error) {
    pushToast('error', error instanceof Error ? error.message : '删除项目失败')
  } finally {
    deleteSaving.value = false
  }
}

onMounted(() => {
  loadProjects().catch((error) => {
    pushToast('error', error instanceof Error ? error.message : '加载项目失败')
  })
})

watch(activeLibraryProject, (project) => {
  if (!project) return
  setActiveProject(project.id, project.normalizedType)
}, { immediate: true })
</script>

<template>
  <div class="h-full min-h-0">
    <ContentPanel
      title="库"
      :breadcrumbs="breadcrumbs"
    >
      <template #toolbar>
        <button
          v-if="!isProjectDetail"
          type="button"
          title="新建项目"
          class="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-md text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-[#62666d] dark:hover:bg-white/[0.04] dark:hover:text-[#8a8f98]"
          @click="openCreateDialog"
        >
          <i class="fa-solid fa-plus text-xs"></i>
        </button>
        <template v-else-if="activeLibraryProject">
          <button
            type="button"
            class="flex h-8 items-center gap-2 rounded-md px-3 text-xs font-medium text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-[#8a8f98] dark:hover:bg-white/[0.04] dark:hover:text-[#d0d6e0]"
            @click="openLibraryRoot"
          >
            <i class="fa-solid fa-arrow-left text-[11px]"></i>
            返回
          </button>
          <BaseButton size="sm" variant="primary" @click="openEditDialog(activeLibraryProject)">
            <i class="fa-solid fa-sliders"></i>
            修改信息
          </BaseButton>
        </template>
      </template>

      <div v-if="mode === 'library' && !isProjectDetail" class="flex h-full min-h-0 flex-col overflow-hidden rounded-lg">
        <div class="grid shrink-0 grid-cols-2 gap-2 border-b border-gray-200 px-4 py-3 dark:border-white/[0.06] md:grid-cols-5">
          <div
            v-for="stat in libraryStats"
            :key="stat.label"
            class="flex min-w-0 items-center gap-3 rounded-md border border-gray-200 bg-white/50 px-3 py-2 dark:border-white/[0.06] dark:bg-white/[0.025]"
          >
            <span
              class="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-sm"
              :class="[
                stat.tone === 'accent' ? 'bg-[rgb(var(--accent-rgb)/0.14)] text-[rgb(var(--accent-rgb))]' : '',
                stat.tone === 'blue' ? 'bg-blue-500/12 text-blue-400' : '',
                stat.tone === 'emerald' ? 'bg-emerald-500/12 text-emerald-400' : '',
                stat.tone === 'amber' ? 'bg-amber-500/12 text-amber-400' : '',
                stat.tone === 'orange' ? 'bg-orange-500/12 text-orange-400' : '',
              ]"
            >
              <i class="fa-solid" :class="stat.icon"></i>
            </span>
            <span class="min-w-0">
              <span class="block truncate text-xs font-medium text-gray-500 dark:text-[#8a8f98]">{{ stat.label }}</span>
              <span class="mt-0.5 block text-sm font-semibold text-gray-900 dark:text-[#f7f8f8]">{{ stat.value }}</span>
            </span>
          </div>
        </div>

        <div class="flex shrink-0 flex-col gap-3 border-b border-gray-200 px-4 py-3 dark:border-white/[0.06] lg:flex-row lg:items-center lg:justify-between">
          <div class="flex min-w-0 items-center gap-2">
            <BaseSegmented v-model="activeType" :options="projectTypeOptions" />
          </div>

          <div class="flex min-w-0 items-center gap-2">
            <BaseSearchInput v-model="query" class="w-64 max-w-full" placeholder="搜索项目" />
          </div>
        </div>

        <div class="project-row border-b border-gray-200 px-4 py-2 text-xs font-medium text-gray-500 dark:border-white/[0.06] dark:text-[#62666d]">
          <span>项目</span>
          <span>类型</span>
          <span>内容</span>
          <span>最近更新</span>
          <span></span>
        </div>

        <div class="min-h-0 flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="loadingProjects" class="space-y-0">
            <div
              v-for="i in 6"
              :key="i"
              class="project-row h-12 animate-pulse items-center border-b border-gray-200 px-4 dark:border-white/[0.06]"
            >
              <div class="mr-8 h-4 rounded bg-gray-100 dark:bg-white/[0.06]"></div>
              <div class="mr-8 h-4 rounded bg-gray-100 dark:bg-white/[0.06]"></div>
              <div class="mr-8 h-4 rounded bg-gray-100 dark:bg-white/[0.06]"></div>
              <div class="mr-8 h-4 rounded bg-gray-100 dark:bg-white/[0.06]"></div>
              <div class="h-4 rounded bg-gray-100 dark:bg-white/[0.06]"></div>
            </div>
          </div>

          <BaseEmptyState
            v-else-if="!projectRows.length"
            class="flex h-full min-h-[28rem] items-center justify-center"
            icon="fa-solid fa-box-archive"
            :title="query ? '没有找到匹配项目' : '还没有项目'"
            :description="query ? '换一个关键词，或切换项目类型范围。' : '创建错题库或笔记本后，会在这里显示。'"
          />

          <div
            v-for="project in projectRows"
            v-else
            :key="project.id"
            class="project-row group min-h-[3.75rem] w-full items-center border-b border-gray-200 px-4 text-left text-sm transition-colors hover:bg-gray-50 dark:border-white/[0.06] dark:hover:bg-white/[0.035]"
          >
            <button type="button" class="contents text-left" @click="openProject(project)">
              <span class="flex min-w-0 items-center gap-3 pr-4">
                <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-gray-100 text-gray-500 dark:bg-white/[0.06] dark:text-[#aeb6c2]">
                  <i class="fa-solid text-sm" :class="project.icon"></i>
                </span>
                <span class="min-w-0">
                  <span class="block min-w-0 truncate font-medium text-gray-900 dark:text-[#f7f8f8]">{{ project.name }}</span>
                  <span class="mt-0.5 block min-w-0 truncate text-xs text-gray-500 dark:text-[#62666d]">
                    {{ project.descriptionText || '暂无描述' }}
                  </span>
                </span>
              </span>
              <span>
                <span class="inline-flex h-6 items-center rounded-md bg-gray-100 px-2 text-xs font-medium text-gray-600 dark:bg-white/[0.06] dark:text-[#aeb6c2]">
                  {{ project.typeLabel }}
                </span>
              </span>
              <span class="text-gray-500 dark:text-[#8a8f98]">{{ formatCount(project) }}</span>
              <span class="text-gray-500 dark:text-[#8a8f98]">{{ formatUpdated(project.updatedAt) }}</span>
            </button>

            <span class="flex justify-end" @click.stop>
              <BaseDropdown
                :model-value="String(actionMenuProjectId) === String(project.id)"
                width="w-44"
                align="right"
                panelClass="rounded-lg border border-gray-200 bg-white p-1 shadow-xl dark:border-white/[0.08] dark:bg-[#1c1c1f]"
                @update:model-value="(open) => actionMenuProjectId = open ? project.id : null"
              >
                <template #trigger>
                  <button
                    type="button"
                    title="项目操作"
                    class="flex h-7 w-7 items-center justify-center rounded-md text-gray-400 opacity-0 transition-colors hover:bg-gray-100 hover:text-gray-700 group-hover:opacity-100 data-[open=true]:opacity-100 dark:text-[#62666d] dark:hover:bg-white/[0.06] dark:hover:text-[#d0d6e0]"
                    :data-open="String(actionMenuProjectId) === String(project.id)"
                  >
                    <i class="fa-solid fa-ellipsis text-[11px]"></i>
                  </button>
                </template>
                <template #default="{ close }">
                  <button class="project-menu-item" type="button" @click="close(); openRenameDialog(project)">
                    <i class="fa-solid fa-pen"></i>
                    重命名
                  </button>
                  <button class="project-menu-item" type="button" @click="close(); openEditDialog(project)">
                    <i class="fa-solid fa-sliders"></i>
                    修改信息
                  </button>
                  <div class="my-1 h-px bg-gray-200 dark:bg-white/[0.08]"></div>
                  <button class="project-menu-item project-menu-item--danger" type="button" @click="close(); openDeleteDialog(project)">
                    <i class="fa-solid fa-trash"></i>
                    删除
                  </button>
                </template>
              </BaseDropdown>
            </span>
          </div>
        </div>
      </div>

      <div v-else-if="mode === 'library'" class="flex h-full min-h-0 flex-col overflow-hidden">
        <div v-if="activeLibraryProject" class="flex h-full min-h-0 flex-col overflow-hidden">
          <NoteView v-if="activeLibraryProject.normalizedType === 'note'" embedded />
          <ErrorBankView v-else embedded />
        </div>
        <BaseEmptyState
          v-else
          class="flex h-full min-h-[28rem] items-center justify-center"
          icon="fa-solid fa-box-archive"
          title="项目不存在"
          description="这个项目可能已被删除，或当前账号没有访问权限。"
        />
      </div>

      <div v-else class="grid h-full place-items-center text-sm text-gray-500 dark:text-[#8a8f98]">
        搜索聊天已移至弹窗。
      </div>
    </ContentPanel>

    <BaseModal
      :open="projectDialogOpen"
      :title="projectDialogTitle"
      maxWidth="max-w-[64rem]"
      bodyClass="px-10 pb-8 pt-6"
      @close="closeProjectDialog"
    >
      <template #header="{ close }">
        <div class="flex h-14 items-center justify-between border-b border-gray-200 px-6 dark:border-white/[0.08]">
          <div class="flex min-w-0 items-center gap-2 text-sm font-semibold">
            <i class="fa-solid fa-box-archive shrink-0 text-sm accent-text"></i>
            <span class="truncate text-gray-900 dark:text-[#f7f8f8]">库</span>
            <i class="fa-solid fa-chevron-right text-[10px] text-gray-400 dark:text-[#62666d]"></i>
            <span class="truncate text-gray-900 dark:text-[#f7f8f8]">{{ projectDialogTitle }}</span>
          </div>
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-md text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-[#8a8f98] dark:hover:bg-white/[0.04] dark:hover:text-[#d0d6e0]"
            @click="close"
          >
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
      </template>

      <form class="flex min-h-[34rem] flex-col" @submit.prevent="handleSaveProject">
        <div class="flex-1 space-y-5">
          <input
            v-model="projectName"
            class="block w-full border-none bg-transparent p-0 text-3xl font-semibold text-gray-900 outline-none placeholder:text-gray-400 focus:ring-0 dark:text-[#f7f8f8] dark:placeholder:text-[#62666d]"
            placeholder="项目名称"
            maxlength="100"
            autofocus
          />

          <input
            v-model="projectSummary"
            class="block w-full border-none bg-transparent p-0 text-base text-gray-500 outline-none placeholder:text-gray-400 focus:ring-0 dark:text-[#8a8f98] dark:placeholder:text-[#62666d]"
            placeholder="添加一段简短摘要..."
            maxlength="200"
          />

          <div class="flex flex-wrap items-center gap-2 border-b border-gray-200 pb-5 dark:border-white/[0.08]">
            <BaseSegmented v-if="projectDialogMode === 'create'" v-model="projectType" :options="editTypeOptions" />
            <span
              v-else
              class="inline-flex h-7 items-center rounded-md bg-gray-100 px-3 text-xs font-medium text-gray-600 dark:bg-white/[0.06] dark:text-[#aeb6c2]"
            >
              {{ currentProjectTypeLabel }}
            </span>
          </div>

          <textarea
            v-model="projectDescription"
            class="min-h-[15rem] w-full resize-none border-none bg-transparent p-0 text-base leading-7 text-gray-700 outline-none placeholder:text-gray-400 focus:ring-0 dark:text-[#d0d6e0] dark:placeholder:text-[#62666d]"
            placeholder="写下描述、项目说明，或先收集一些想法..."
            maxlength="1000"
          ></textarea>
        </div>
      </form>
      <template #footer>
        <BaseButton variant="secondary" size="sm" :disabled="projectSaving" @click="closeProjectDialog">
          取消
        </BaseButton>
        <BaseButton
          variant="primary"
          size="sm"
          :disabled="projectSaving || !projectName.trim()"
          @click="handleSaveProject"
        >
          {{ projectDialogActionText }}
        </BaseButton>
      </template>
    </BaseModal>

    <BaseModal
      :open="renameDialogOpen"
      title="重命名项目"
      icon="fa-pen"
      iconBg="accent-bg-soft"
      iconClass="accent-text"
      maxWidth="max-w-[28rem]"
      bodyClass="px-6 pb-3 pt-1"
      @close="closeRenameDialog"
    >
      <form class="space-y-3" @submit.prevent="confirmRename">
        <input
          v-model="renameText"
          class="h-10 w-full rounded-lg border border-gray-200 bg-white px-3 text-sm text-gray-900 outline-none transition-colors focus:border-[rgb(var(--accent-rgb)/0.45)] dark:border-white/[0.08] dark:bg-white/[0.03] dark:text-[#f7f8f8]"
          placeholder="项目名称"
          maxlength="100"
          autofocus
        />
      </form>
      <template #footer>
        <BaseButton variant="secondary" size="sm" :disabled="renameSaving" @click="closeRenameDialog">
          取消
        </BaseButton>
        <BaseButton variant="primary" size="sm" :disabled="renameSaving || !renameText.trim()" @click="confirmRename">
          {{ renameSaving ? '保存中...' : '保存' }}
        </BaseButton>
      </template>
    </BaseModal>

    <BaseModal
      :open="deleteDialogOpen"
      title="删除项目"
      icon="fa-trash"
      iconBg="bg-rose-500/10"
      iconClass="text-rose-400"
      maxWidth="max-w-[28rem]"
      bodyClass="px-6 pb-3 pt-1"
      @close="closeDeleteDialog"
    >
      <p class="text-sm leading-6 text-gray-600 dark:text-[#aeb6c2]">
        确定删除“<span class="font-semibold text-gray-900 dark:text-[#f7f8f8]">{{ deleteTarget?.name }}</span>”吗？如果项目里已有题目或笔记，后端会阻止删除。
      </p>
      <template #footer>
        <BaseButton variant="secondary" size="sm" :disabled="deleteSaving" @click="closeDeleteDialog">
          取消
        </BaseButton>
        <BaseButton variant="primary" size="sm" :disabled="deleteSaving" @click="confirmDelete">
          {{ deleteSaving ? '删除中...' : '删除' }}
        </BaseButton>
      </template>
    </BaseModal>
  </div>
</template>

<style scoped>
.project-row {
  display: grid;
  grid-template-columns: minmax(16rem, 1fr) 8rem 8rem 9rem 2rem;
  column-gap: 1.5rem;
}

.project-menu-item {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 0.625rem;
  border-radius: 0.375rem;
  padding: 0.5rem 0.625rem;
  text-align: left;
  font-size: 0.8125rem;
  font-weight: 500;
  color: rgb(209 214 224);
  transition: background-color 0.16s ease, color 0.16s ease;
}

.project-menu-item:hover {
  background: rgb(255 255 255 / 0.06);
  color: #f7f8f8;
}

.project-menu-item i {
  width: 1rem;
  flex-shrink: 0;
  text-align: center;
  font-size: 0.75rem;
  color: #8a8f98;
}

.project-menu-item--danger {
  color: rgb(251 113 133);
}

.project-menu-item--danger:hover {
  background: rgb(244 63 94 / 0.12);
  color: rgb(253 164 175);
}

.project-menu-item--danger i {
  color: currentColor;
}

@media (max-width: 900px) {
  .project-row {
    grid-template-columns: minmax(0, 1fr) 6rem 4rem 2rem;
  }

  .project-row > :nth-child(4) {
    display: none;
  }
}
</style>
