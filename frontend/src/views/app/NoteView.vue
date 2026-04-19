<script setup>
import { ref, watch, computed, nextTick, onMounted } from 'vue'
import * as api from '@/api.js'
import { renderMarkdown, typesetMath } from '@/utils.js'
import ContentPanel from '@/components/workspace/ContentPanel.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import BaseGhostButton from '@/components/base/BaseGhostButton.vue'
import BaseButton from '@/components/base/BaseButton.vue'
import SearchInput from '@/components/base/SearchInput.vue'
import BaseSelect from '@/components/base/BaseSelect.vue'
import EmptyState from '@/components/base/EmptyState.vue'
import { useToast } from '@/composables/useToast.js'
import { useSystemStatus } from '@/composables/useSystemStatus.js'
import { useAuth } from '@/composables/useAuth.js'

const QUOTA_EXCEEDED_CODE = 'DAILY_FREE_QUOTA_EXCEEDED'

const { pushToast } = useToast()
const { selectedProvider, selectedModel } = useSystemStatus()
const { setQuotaSnapshot, refreshCurrentUser } = useAuth()

const noteContentRef = ref(null)

// ---- 状态 ----
const notes = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))
const loading = ref(false)
const creating = ref(false)
const createProgress = ref(0)

// 筛选
const filterSubject = ref('')
const filterTag = ref('')
const filterKeyword = ref('')
const subjects = ref([])
const tagNames = ref([])

// 加载筛选选项
async function loadFilterOptions() {
  try {
    const subjectData = await api.fetchSubjects()
    subjects.value = subjectData.subjects || []
  } catch (_) {}
}

// 详情/编辑
const selectedNote = ref(null)
const editing = ref(false)
const editTitle = ref('')
const editContent = ref('')

// ---- 加载笔记列表 ----
async function loadNotes() {
  loading.value = true
  try {
    const data = await api.fetchNotes({
      page: page.value,
      limit: pageSize.value,
      subject: filterSubject.value || undefined,
      knowledge_tag: filterTag.value || undefined,
      keyword: filterKeyword.value || undefined,
    })
    notes.value = data.items
    total.value = data.total
  } catch (e) {
    pushToast('error', e.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => { loadNotes(); loadFilterOptions() })
watch([page, filterSubject, filterTag], () => { page.value === 1 ? loadNotes() : (page.value = 1) })

let keywordTimer = null
watch(filterKeyword, () => {
  clearTimeout(keywordTimer)
  keywordTimer = setTimeout(() => { page.value = 1; loadNotes() }, 500)
})

// ---- 上传笔记 ----
const fileInput = ref(null)

function triggerUpload() {
  fileInput.value?.click()
}

function handleFiles(e) {
  const files = e.target.files
  if (!files?.length) return

  creating.value = true
  createProgress.value = 0

  const formData = new FormData()
  for (const f of files) formData.append('files', f)
  formData.append('model_provider', selectedProvider.value)
  if (selectedModel.value) formData.append('model_name', selectedModel.value)

  api.createNote(formData, {
    onProgress: (ratio) => { createProgress.value = Math.round(ratio * 50) },
    onSuccess: async (data) => {
      creating.value = false
      createProgress.value = 100
      await refreshCurrentUser().catch(() => {})
      pushToast('success', '笔记整理完成')
      loadNotes()
      if (data.note) selectedNote.value = data.note
    },
    onError: (error) => {
      creating.value = false
      createProgress.value = 0
      if (error?.quota) setQuotaSnapshot(error.quota)
      if (error?.code === QUOTA_EXCEEDED_CODE) {
        pushToast('error', error.message || '今日免费体验次数已用完')
        return
      }
      pushToast('error', error instanceof Error ? error.message : String(error))
    },
  })

  let fakeProgress = 50
  const timer = setInterval(() => {
    if (!creating.value) { clearInterval(timer); return }
    fakeProgress = Math.min(fakeProgress + 2, 95)
    createProgress.value = fakeProgress
  }, 500)

  e.target.value = ''
}


// ---- 详情 ----
async function openNote(note) {
  try {
    const full = await api.fetchNote(note.id)
    selectedNote.value = full
    // 等 DOM 完全更新后渲染 LaTeX 公式（nextTick + 延迟，确保过渡动画完成）
    await nextTick()
    setTimeout(() => {
      if (noteContentRef.value) typesetMath(noteContentRef.value)
    }, 100)
  } catch (e) {
    pushToast('error', e.message)
  }
}

function closeDetail() {
  selectedNote.value = null
  editing.value = false
}

// ---- 编辑 ----
function startEdit() {
  editTitle.value = selectedNote.value.title
  editContent.value = selectedNote.value.content_markdown
  editing.value = true
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
    await nextTick()
    setTimeout(() => {
      if (noteContentRef.value) typesetMath(noteContentRef.value)
    }, 100)
  } catch (e) {
    pushToast('error', e.message)
  }
}

// ---- 删除 ----
async function doDelete(noteId) {
  if (!confirm('确认删除这条笔记？')) return
  try {
    await api.deleteNote(noteId)
    pushToast('success', '已删除')
    if (selectedNote.value?.id === noteId) closeDetail()
    loadNotes()
  } catch (e) {
    pushToast('error', e.message)
  }
}
</script>

<template>
  <ContentPanel title="笔记库">
    <template #toolbar>
      <button @click="triggerUpload" class="flex h-7 items-center gap-1.5 rounded-md border border-gray-200 dark:border-white/[0.06] bg-white dark:bg-white/[0.03] px-2.5 text-xs font-medium text-gray-500 dark:text-[#8a8f98] hover:bg-gray-50 dark:hover:bg-white/[0.06] hover:text-gray-700 dark:hover:text-[#d0d6e0] transition-colors" title="录入新笔记">
        <i class="fa-solid fa-plus text-[10px]"></i> 录入
      </button>
    </template>
  <div class="relative h-full overflow-y-auto custom-scrollbar flex flex-col">
    <div class="relative z-10 flex-1 flex flex-col">
      
      <!-- List View -->
      <div v-if="!selectedNote" class="relative flex-1 flex flex-col">
        <input ref="fileInput" type="file" multiple accept="image/*" class="hidden" @change="handleFiles" />

        <!-- 筛选栏（对齐错题库风格） -->
        <div class="relative z-20 mb-4 flex items-center gap-2 flex-wrap">
          <!-- 搜索框 -->
          <div class="relative">
            <i class="fa-solid fa-magnifying-glass pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-xs text-gray-400 dark:text-[#62666d] transition-colors"></i>
            <input
              v-model="filterKeyword"
              type="text"
              placeholder="搜索笔记..."
              class="h-8 w-52 rounded-md border border-gray-200 dark:border-white/[0.08] bg-white dark:bg-white/[0.02] pl-8 pr-3 text-xs font-medium text-gray-900 dark:text-[#f7f8f8] placeholder-gray-400 dark:placeholder-[#62666d] outline-none transition-colors hover:border-gray-300 dark:hover:border-white/[0.12] focus:border-indigo-500 dark:focus:border-white/[0.15]"
            />
          </div>
          
          <BaseSelect v-model="filterSubject" :options="subjects" placeholder="全部学科" class="h-8 w-32" />
          <BaseSelect v-model="filterTag" :options="tagNames" placeholder="全部知识点" class="h-8 w-32" />
          
          <button
            v-if="filterSubject || filterTag"
            @click="filterSubject = ''; filterTag = ''"
            class="text-xs text-gray-500 dark:text-[#62666d] hover:text-rose-500 dark:hover:text-rose-400 transition-colors ml-2"
          >清除筛选</button>

          <div class="ml-auto flex items-center text-xs text-gray-500 dark:text-[#8a8f98]">
            共 {{ total }} 条笔记
          </div>
        </div>
          <!-- 进度条 -->
          <div v-if="creating" class="mb-4">
            <div class="h-1 rounded-full bg-gray-200 dark:bg-white/[0.06]">
              <div class="h-full rounded-full bg-indigo-500 dark:bg-[rgb(129,115,223)] transition-all duration-300" :style="{ width: createProgress + '%' }"></div>
            </div>
            <p class="mt-1 text-xs text-gray-500 dark:text-[#62666d]">OCR 识别 + AI 整理中... {{ createProgress }}%</p>
          </div>

        <!-- Notes Grid -->
        <div class="relative flex-1 flex flex-col">
          <EmptyState
            v-if="!loading && notes.length === 0"
            icon="fa-solid fa-book-open"
            title="还没有笔记"
            description="上传手写笔记或板书照片，AI 自动整理为结构化知识点"
          >
            <BaseButton @click="triggerUpload" variant="primary" size="sm">
              <i class="fa-solid fa-plus"></i> 录入新笔记
            </BaseButton>
          </EmptyState>

          <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <BaseCard
              v-for="note in notes"
              :key="note.id"
              @click="openNote(note)"
              class="group cursor-pointer"
              padding="p-4"
            >
              <h3 class="mb-2 text-sm font-medium text-gray-900 dark:text-[#f7f8f8] line-clamp-2">{{ note.title }}</h3>
              <p class="mb-3 text-xs text-gray-500 dark:text-[#8a8f98] line-clamp-3">
                {{ note.content_markdown?.replace(/[#*`>\-]/g, '').slice(0, 120) }}...
              </p>
              <div class="flex flex-wrap items-center gap-2">
                <span v-if="note.subject" class="rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-600 dark:bg-[rgb(129,115,223)]/10 dark:text-[rgb(145,132,235)]">{{ note.subject }}</span>
                <span v-for="tag in (note.knowledge_tags || []).slice(0, 3)" :key="tag" class="rounded-md border border-gray-200 px-2 py-0.5 text-xs text-gray-500 dark:border-white/[0.06] dark:text-[#8a8f98]">{{ tag }}</span>
                <span class="ml-auto text-xs text-gray-400 dark:text-[#62666d]">{{ note.updated_at?.slice(0, 10) }}</span>
              </div>
            </BaseCard>
          </div>

          <!-- 分页 -->
          <div v-if="totalPages > 1" class="mt-8 flex justify-center gap-2">
            <button
              v-for="p in totalPages"
              :key="p"
              @click="page = p"
              class="size-8 rounded-md text-xs font-medium transition-all"
              :class="p === page ? 'bg-indigo-500 text-white shadow-sm dark:brand-btn dark:text-[#f7f8f8]' : 'border border-gray-200 bg-white text-gray-500 hover:bg-gray-50 hover:text-gray-700 dark:border-white/[0.06] dark:bg-transparent dark:text-[#8a8f98] dark:hover:bg-white/[0.04]'"
            >
              {{ p }}
            </button>
          </div>
        </div>
      </div>

      <!-- Detail View -->
      <div v-else class="relative flex-1 flex flex-col">
        <!-- 详情工具栏 -->
        <div class="mb-6 flex items-center justify-between">
          <h3 class="text-base font-medium text-gray-900 dark:text-[#f7f8f8]">{{ selectedNote.title }}</h3>
          <div class="flex items-center gap-2">
            <button @click="closeDetail" class="inline-flex items-center gap-2 rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-800 dark:border-white/[0.08] dark:bg-white/[0.02] dark:text-[#d0d6e0] dark:hover:bg-white/[0.05] transition-colors">
              <i class="fa-solid fa-arrow-left text-[10px]"></i> 返回
            </button>
            <button v-if="!editing" @click="startEdit" class="inline-flex items-center gap-2 rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-800 dark:border-white/[0.08] dark:bg-white/[0.02] dark:text-[#d0d6e0] dark:hover:bg-white/[0.05] transition-colors">
              <i class="fa-solid fa-pen text-[10px]"></i> 编辑
            </button>
            <button @click="doDelete(selectedNote.id)" class="inline-flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-100 hover:text-red-700 dark:border-white/[0.08] dark:bg-white/[0.02] dark:text-rose-400 dark:hover:bg-rose-500/10 transition-colors">
              <i class="fa-solid fa-trash text-[10px]"></i> 删除
            </button>
          </div>
        </div>

        <!-- Tags Row -->
        <div class="mb-6 flex flex-wrap items-center gap-2">
          <span v-if="selectedNote.subject" class="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300">{{ selectedNote.subject }}</span>
          <span v-for="tag in selectedNote.knowledge_tags" :key="tag" class="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600 dark:bg-white/[0.06] dark:text-slate-300">{{ tag }}</span>
        </div>

        <BaseCard padding="p-8">
          <!-- Edit Mode -->
          <div v-if="editing" class="space-y-4">
            <div>
              <label class="mb-2 block text-[11px] font-black uppercase tracking-widest text-slate-500">标题</label>
              <input v-model="editTitle" class="w-full rounded-xl border border-slate-200/60 bg-white/60 px-4 h-12 text-lg font-bold outline-none focus:border-emerald-300 focus:ring-2 focus:ring-emerald-500/20 dark:border-white/10 dark:bg-white/[0.03] dark:text-white" />
            </div>
            <div>
              <label class="mb-2 block text-[11px] font-black uppercase tracking-widest text-slate-500">内容 (Markdown)</label>
              <textarea v-model="editContent" rows="15" class="w-full rounded-xl border border-slate-200/60 bg-white/60 p-4 font-mono text-sm leading-relaxed outline-none focus:border-emerald-300 focus:ring-2 focus:ring-emerald-500/20 custom-scrollbar dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-200"></textarea>
            </div>
            <div class="flex gap-3 pt-4">
              <button @click="saveEdit" class="btn-primary h-10 px-8 shadow-md shadow-emerald-500/20">
                <i class="fa-solid fa-check mr-2"></i>保存修改
              </button>
              <BaseGhostButton @click="editing = false">取消</BaseGhostButton>
            </div>
          </div>

          <!-- View Mode -->
          <div v-else ref="noteContentRef">
            <article class="prose prose-slate max-w-none dark:prose-invert prose-headings:text-slate-900 dark:prose-headings:text-white prose-p:leading-relaxed prose-a:text-emerald-600 prose-pre:bg-slate-50 dark:prose-pre:bg-slate-900 prose-pre:border prose-pre:border-slate-200/60 dark:prose-pre:border-white/10" v-html="renderMarkdown(selectedNote.content_markdown || '')"></article>
          </div>
        </BaseCard>

        <!-- Original Images -->
        <div v-if="selectedNote.source_images?.length && !editing" class="mt-8">
          <h3 class="mb-4 text-sm font-black uppercase tracking-widest text-slate-500">
            <i class="fa-solid fa-image mr-2"></i>原始笔记图片
          </h3>
          <div class="grid gap-4 sm:grid-cols-2">
            <BaseCard v-for="(src, idx) in selectedNote.source_images" :key="idx" padding="p-2" class="overflow-hidden">
              <img
                :src="'/images/' + src.split('/imgs/').pop() || src"
                class="w-full rounded-xl cursor-pointer hover:opacity-90 transition-opacity"
                @error="$event.target.style.display='none'"
              />
            </BaseCard>
          </div>
        </div>
      </div>
    </div>
  </div>
  </ContentPanel>
</template>
