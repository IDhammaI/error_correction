<script setup>
/**
 * NoteListPanel.vue
 * 笔记库左侧列表面板。
 */
import BaseButton from '@/components/base/BaseButton.vue'
import BaseEmptyState from '@/components/base/BaseEmptyState.vue'
import BasePagination from '@/components/base/BasePagination.vue'
import BaseTag from '@/components/base/BaseTag.vue'

defineProps({
  notes: { type: Array, default: () => [] },
  total: { type: Number, default: 0 },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 10 },
  totalPages: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
  selectedNoteId: { type: [String, Number, null], default: null },
  hasNoteProject: { type: Boolean, default: false },
})

const emit = defineEmits(['refresh', 'create-note', 'open-note', 'page-change'])

const isActiveNote = (note, selectedNoteId) => String(note?.id) === String(selectedNoteId)

const formatDate = (iso) => {
  if (!iso) return '暂无日期'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '暂无日期'
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
</script>

<template>
  <section class="flex min-h-0 flex-col overflow-hidden rounded-xl border border-gray-200 bg-white/80 dark:border-white/[0.07] dark:bg-white/[0.035]">
    <header class="flex shrink-0 items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-white/[0.06]">
      <div>
        <h3 class="text-sm font-bold text-gray-900 dark:text-[#f7f8f8]">笔记列表</h3>
        <p class="text-xs text-gray-500 dark:text-[#8a8f98]">共 {{ total }} 条，当前第 {{ page }} 页</p>
      </div>
      <button
        class="flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-700 dark:border-white/[0.07] dark:text-[#8a8f98] dark:hover:bg-white/[0.06] dark:hover:text-[#d0d6e0]"
        title="刷新"
        @click="emit('refresh')"
      >
        <i class="fa-solid fa-rotate-right text-xs"></i>
      </button>
    </header>

    <div class="min-h-0 flex-1 overflow-y-auto p-4 custom-scrollbar">
      <div v-if="loading && !notes.length" class="space-y-3">
        <div v-for="i in 4" :key="i" class="h-28 animate-pulse rounded-xl bg-gray-100 dark:bg-white/[0.04]"></div>
      </div>

      <BaseEmptyState
        v-else-if="!loading && !notes.length"
        icon="fa-solid fa-book-open"
        :title="hasNoteProject ? '还没有笔记' : '还没有笔记本'"
        :description="hasNoteProject ? '上传手写笔记或板书照片，AI 自动整理为结构化知识点' : '先在左侧创建一个笔记本，再录入笔记'"
      >
        <BaseButton variant="primary" size="sm" @click="emit('create-note')">
          <i class="fa-solid fa-plus"></i> 录入新笔记
        </BaseButton>
      </BaseEmptyState>

      <div v-else class="space-y-3">
        <article
          v-for="(note, idx) in notes"
          :key="note.id"
          class="group grid cursor-pointer grid-cols-[auto,1fr] overflow-hidden rounded-xl border bg-white/70 transition-all hover:border-[rgb(var(--accent-rgb)/0.45)] hover:bg-white dark:bg-white/[0.025] dark:hover:bg-white/[0.045]"
          :class="isActiveNote(note, selectedNoteId)
            ? 'accent-border shadow-[0_0_0_1px_rgb(var(--accent-rgb)/0.18)] dark:bg-[rgb(var(--accent-rgb)/0.08)]'
            : 'border-gray-200 dark:border-white/[0.07]'"
          @click="emit('open-note', note)"
        >
          <div class="flex w-14 flex-col items-center justify-center border-r border-gray-200 dark:border-white/[0.06]">
            <span
              class="flex h-8 w-8 items-center justify-center rounded-full text-sm font-black text-white"
              :class="isActiveNote(note, selectedNoteId) ? 'accent-bg' : 'bg-violet-500/80'"
            >
              {{ idx + 1 + (page - 1) * pageSize }}
            </span>
            <span class="mt-2 text-[10px] text-gray-400 dark:text-[#62666d]">笔记</span>
          </div>

          <div class="min-w-0 p-4">
            <div class="mb-2 flex flex-wrap items-center gap-1.5">
              <BaseTag v-if="note.subject" tone="accent">{{ note.subject }}</BaseTag>
              <BaseTag v-for="tag in (note.knowledge_tags || []).slice(0, 2)" :key="tag">{{ tag }}</BaseTag>
            </div>
            <div class="mb-2 flex min-w-0 items-start justify-between gap-3">
              <h3 class="min-w-0 truncate text-sm font-semibold text-gray-900 dark:text-[#f7f8f8]">{{ note.title }}</h3>
              <span class="shrink-0 text-xs text-gray-400 dark:text-[#62666d]">{{ formatDate(note.updated_at || note.created_at) }}</span>
            </div>
            <p class="line-clamp-2 text-sm font-medium leading-relaxed text-gray-700 dark:text-[#d0d6e0]">
              {{ note.preview }}
            </p>
          </div>
        </article>
      </div>
    </div>

    <footer v-if="totalPages > 1" class="shrink-0 border-t border-gray-200 p-3 dark:border-white/[0.06]">
      <BasePagination :page="page" :total-pages="totalPages" @change="(p) => emit('page-change', p)" />
    </footer>
  </section>
</template>
