<script setup>
/**
 * NoteView.vue
 * 笔记库工作台：顶部筛选 + 统计卡片 + 左侧列表 + 中间详情 + 右侧信息栏。
 */
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as api from '@/api/index.js'
import { getNotePreviewText } from '@/utils/index.js'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseStat from '@/components/base/BaseStat.vue'
import ContentPanel from '@/components/features/app/layout/ContentPanel.vue'
import NoteDetailPanel from '@/components/features/app/notes/NoteDetailPanel.vue'
import NoteInsightAside from '@/components/features/app/notes/NoteInsightAside.vue'
import NoteListPanel from '@/components/features/app/notes/NoteListPanel.vue'
import NoteToolbar from '@/components/features/app/notes/NoteToolbar.vue'
import { useProjects } from '@/composables/useProjects.js'
import { useToast } from '@/composables/useToast.js'

defineProps({
  embedded: { type: Boolean, default: false },
})

const router = useRouter()
const { pushToast } = useToast()
const { activeNoteProjectId, noteProjects } = useProjects()

const notes = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const isDeleting = ref(false)
const filterPanelOpen = ref(false)

const selectedNote = ref(null)
const editing = ref(false)
const editTitle = ref('')
const editContent = ref('')

const filters = reactive({
  subject: [],
  tag: [],
  keyword: '',
})
const subjects = ref([])
const tagNames = ref([])

const hasNoteProject = computed(() => noteProjects.value.length > 0)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))
const notesWithPreview = computed(() => notes.value.map(note => ({
  ...note,
  preview: getNotePreviewText(note.content_markdown || '', 130),
})))
const selectedTags = computed(() => {
  const s = new Set()
  for (const tag of filters.tag || []) s.add(tag)
  return s
})
const activeNoteTags = computed(() => selectedNote.value?.knowledge_tags || [])
const sourceImages = computed(() => selectedNote.value?.source_images || [])

const statsCards = computed(() => [
  { label: '全部笔记', value: total.value, suffix: '条', hint: '当前笔记本', icon: 'fa-book-open', tone: 'accent' },
  { label: '当前页', value: notes.value.length, suffix: '条', hint: `第 ${page.value} 页`, icon: 'fa-list-ul', tone: 'blue' },
  { label: '学科', value: subjects.value.length, suffix: '类', hint: '可筛选学科', icon: 'fa-layer-group', tone: 'emerald' },
  { label: '知识点', value: tagNames.value.length, suffix: '个', hint: '当前筛选范围', icon: 'fa-tags', tone: 'amber' },
  { label: '原图', value: sourceImages.value.length, suffix: '张', hint: selectedNote.value ? '选中笔记' : '未选择', icon: 'fa-image', tone: 'orange' },
])

const toggleTagSelect = (tag) => {
  const next = new Set(filters.tag || [])
  if (next.has(tag)) next.delete(tag)
  else next.add(tag)
  filters.tag = [...next]
}

const resetFilters = () => {
  filters.subject = []
  filters.tag = []
  filters.keyword = ''
  page.value = 1
  loadNotes()
}

async function loadNotes() {
  if (!activeNoteProjectId.value) {
    notes.value = []
    total.value = 0
    selectedNote.value = null
    editing.value = false
    loading.value = false
    return
  }
  loading.value = true
  try {
    const data = await api.fetchNotes({
      page: page.value,
      limit: pageSize.value,
      subject: filters.subject?.length ? filters.subject : undefined,
      knowledge_tag: filters.tag?.length ? filters.tag : undefined,
      keyword: filters.keyword || undefined,
      project_id: activeNoteProjectId.value || undefined,
    })
    notes.value = data.items
    total.value = data.total

    if (!notes.value.length) {
      selectedNote.value = null
      editing.value = false
      return
    }

    const nextActiveId = selectedNote.value?.id
    if (nextActiveId && notes.value.some(note => String(note.id) === String(nextActiveId))) {
      loadNoteDetail(nextActiveId)
    } else {
      openNote(notes.value[0])
    }
  } catch (e) {
    pushToast('error', e.message)
  } finally {
    loading.value = false
  }
}

async function loadFilterOptions() {
  if (!activeNoteProjectId.value) {
    subjects.value = []
    return
  }
  try {
    subjects.value = await api.fetchNoteSubjects(activeNoteProjectId.value)
  } catch (_) { }
}

async function loadTags() {
  if (!activeNoteProjectId.value) {
    tagNames.value = []
    return
  }
  try {
    tagNames.value = await api.fetchNoteTagNames(filters.subject?.length === 1 ? filters.subject[0] : undefined, activeNoteProjectId.value)
  } catch (_) { }
}

async function openNote(note) {
  if (!note?.id) return
  editing.value = false
  loadNoteDetail(note.id)
}

async function loadNoteDetail(id) {
  if (isDeleting.value) return
  try {
    selectedNote.value = await api.fetchNote(id)
  } catch (e) {
    if (!isDeleting.value) {
      pushToast('error', '无法加载笔记数据，请检查网络或笔记是否存在')
      closeDetail()
    }
  }
}

function closeDetail() {
  selectedNote.value = null
  editing.value = false
}

function startEdit() {
  if (!selectedNote.value) return
  editTitle.value = selectedNote.value.title
  editContent.value = selectedNote.value.content_markdown
  editing.value = true
}

function cancelEdit() {
  editing.value = false
}

async function saveEdit() {
  try {
    const updated = await api.updateNote(selectedNote.value.id, {
      title: editTitle.value,
      content_markdown: editContent.value,
    })
    selectedNote.value = updated
    editing.value = false
    pushToast('success', '已保存')
    loadNotes()
  } catch (e) {
    pushToast('error', e.message)
  }
}

async function doDelete(noteId) {
  isDeleting.value = true
  try {
    await api.deleteNote(noteId)
    pushToast('success', '笔记删除成功')
    closeDetail()
    loadNotes()
  } catch (e) {
    if (e.status === 404 || e.message?.includes('不存在')) {
      closeDetail()
      loadNotes()
    } else {
      pushToast('error', e.message)
    }
  } finally {
    isDeleting.value = false
  }
}

function goToWorkspace() {
  router.push('/app/workspace?mode=note')
}

onMounted(() => {
  loadNotes()
  loadFilterOptions()
  loadTags()
})

watch([page, () => filters.subject, () => filters.tag], () => {
  page.value === 1 ? loadNotes() : (page.value = 1)
})

watch(() => filters.subject, () => {
  filters.tag = []
  loadTags()
})

watch(activeNoteProjectId, () => {
  filters.subject = []
  filters.tag = []
  page.value = 1
  selectedNote.value = null
  editing.value = false
  loadNotes()
  loadFilterOptions()
  loadTags()
})

let keywordTimer = null
watch(() => filters.keyword, () => {
  clearTimeout(keywordTimer)
  keywordTimer = setTimeout(() => {
    page.value = 1
    loadNotes()
  }, 500)
})
</script>

<template>
  <component :is="embedded ? 'div' : ContentPanel" :title="embedded ? undefined : '笔记库'"
    :class="embedded ? 'flex h-full min-h-0 flex-col overflow-hidden p-4' : ''">
    <template v-if="!embedded" #toolbar>
      <BaseButton size="sm" variant="primary" @click="goToWorkspace">
        <i class="fa-solid fa-plus"></i>
        录入笔记
      </BaseButton>
    </template>

    <div class="flex h-full min-h-0 flex-col gap-4 overflow-hidden">
      <NoteToolbar v-model:filter-panel-open="filterPanelOpen" :filters="filters" :subjects="subjects"
        :tag-names="tagNames" :selected-tags="selectedTags" :total="total" @toggle-tag="toggleTagSelect"
        @reset="resetFilters" />

      <div class="grid shrink-0 grid-cols-2 gap-3 lg:grid-cols-5">
        <BaseStat v-for="card in statsCards" :key="card.label" :label="card.label" :value="card.value"
          :suffix="card.suffix" :hint="card.hint" :icon="card.icon" :tone="card.tone" />
      </div>

      <div
        class="grid min-h-0 flex-1 gap-4 xl:grid-cols-[minmax(24rem,0.95fr)_minmax(30rem,1.25fr)_minmax(16rem,0.55fr)]">
        <NoteListPanel :notes="notesWithPreview" :total="total" :page="page" :page-size="pageSize"
          :total-pages="totalPages" :loading="loading" :selected-note-id="selectedNote?.id"
          :has-note-project="hasNoteProject" @refresh="loadNotes" @create-note="goToWorkspace" @open-note="openNote"
          @page-change="(p) => { page = p }" />

        <NoteDetailPanel v-model:edit-title="editTitle" v-model:edit-content="editContent" :note="selectedNote"
          :knowledge-tags="activeNoteTags" :editing="editing" @start-edit="startEdit" @save-edit="saveEdit"
          @cancel-edit="cancelEdit" @delete-note="doDelete" @close-detail="closeDetail" />

        <NoteInsightAside :note="selectedNote" :knowledge-tags="activeNoteTags" :source-images="sourceImages" />
      </div>
    </div>
  </component>
</template>
