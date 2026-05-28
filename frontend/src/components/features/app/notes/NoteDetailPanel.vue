<script setup>
/**
 * NoteDetailPanel.vue
 * 笔记库中间详情与编辑面板。
 */
import { nextTick, ref, watch } from 'vue'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseEmptyState from '@/components/base/BaseEmptyState.vue'
import BasePopconfirm from '@/components/base/BasePopconfirm.vue'
import BaseTag from '@/components/base/BaseTag.vue'
import { renderMarkdown, typesetMath } from '@/utils/index.js'

const props = defineProps({
  note: { type: Object, default: null },
  knowledgeTags: { type: Array, default: () => [] },
  editing: { type: Boolean, default: false },
  editTitle: { type: String, default: '' },
  editContent: { type: String, default: '' },
})

const emit = defineEmits([
  'start-edit',
  'save-edit',
  'cancel-edit',
  'delete-note',
  'close-detail',
  'update:editTitle',
  'update:editContent',
])

const noteContentRef = ref(null)

const typesetContent = async () => {
  if (!props.note || props.editing) return
  await nextTick()
  window.setTimeout(() => {
    if (noteContentRef.value) typesetMath(noteContentRef.value)
  }, 100)
}

watch(() => [props.note?.id, props.note?.content_markdown, props.editing], typesetContent, { immediate: true })
</script>

<template>
  <section class="flex min-h-0 flex-col overflow-hidden rounded-xl border border-gray-200 bg-white/80 dark:border-white/[0.07] dark:bg-white/[0.035]">
    <template v-if="note">
      <header class="flex shrink-0 items-center justify-between border-b border-gray-200 px-5 py-3 dark:border-white/[0.06]">
        <div class="min-w-0">
          <div class="mb-1 flex flex-wrap items-center gap-2">
            <BaseTag v-if="note.subject" tone="accent">{{ note.subject }}</BaseTag>
            <BaseTag v-for="tag in knowledgeTags.slice(0, 3)" :key="tag">{{ tag }}</BaseTag>
          </div>
          <h3 class="truncate text-base font-bold text-gray-900 dark:text-[#f7f8f8]">
            {{ note.title }} <span class="ml-2 text-xs font-medium text-gray-400">ID: {{ note.id }}</span>
          </h3>
        </div>
        <div class="flex items-center gap-2">
          <button
            v-if="!editing"
            class="flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-700 dark:border-white/[0.07] dark:text-[#8a8f98] dark:hover:bg-white/[0.06] dark:hover:text-[#d0d6e0]"
            title="编辑笔记"
            @click="emit('start-edit')"
          >
            <i class="fa-solid fa-pen text-xs"></i>
          </button>
          <BasePopconfirm title="删除这条笔记？" description="删除后将从当前笔记本永久移除。" confirm-text="删除" danger @confirm="emit('delete-note', note.id)">
            <button
              class="flex h-9 w-9 items-center justify-center rounded-lg border border-rose-500/20 text-rose-500 transition-colors hover:bg-rose-50 dark:border-white/[0.07] dark:text-rose-400 dark:hover:bg-rose-500/10"
              title="删除笔记"
            >
              <i class="fa-solid fa-trash-can text-xs"></i>
            </button>
          </BasePopconfirm>
        </div>
      </header>

      <div class="min-h-0 flex-1 overflow-y-auto p-5 custom-scrollbar">
        <div v-if="editing" class="space-y-4">
          <div>
            <label class="mb-2 block text-xs font-bold text-gray-500 dark:text-[#8a8f98]">标题</label>
            <input
              :value="editTitle"
              class="h-11 w-full rounded-xl border border-gray-200 bg-white/70 px-4 text-sm font-bold text-gray-900 outline-none transition-all focus:border-[rgb(var(--accent-rgb)/0.45)] focus:ring-2 focus:ring-[rgb(var(--accent-rgb)/0.16)] dark:border-white/[0.08] dark:bg-white/[0.03] dark:text-[#f7f8f8]"
              @input="emit('update:editTitle', $event.target.value)"
            />
          </div>
          <div>
            <label class="mb-2 block text-xs font-bold text-gray-500 dark:text-[#8a8f98]">内容（Markdown）</label>
            <textarea
              :value="editContent"
              rows="18"
              class="w-full resize-none rounded-xl border border-gray-200 bg-white/70 p-4 font-mono text-sm leading-7 text-gray-800 outline-none transition-all focus:border-[rgb(var(--accent-rgb)/0.45)] focus:ring-2 focus:ring-[rgb(var(--accent-rgb)/0.16)] dark:border-white/[0.08] dark:bg-white/[0.03] dark:text-[#d0d6e0]"
              @input="emit('update:editContent', $event.target.value)"
            ></textarea>
          </div>
        </div>

        <article
          v-else
          ref="noteContentRef"
          class="prose prose-slate max-w-none dark:prose-invert prose-headings:text-slate-900 dark:prose-headings:text-white prose-p:leading-relaxed prose-a:text-[rgb(var(--accent-rgb))] prose-pre:bg-slate-50 dark:prose-pre:bg-slate-900 prose-pre:border prose-pre:border-slate-200/60 dark:prose-pre:border-white/10"
          v-html="renderMarkdown(note.content_markdown || '')"
        ></article>
      </div>

      <footer class="flex shrink-0 flex-wrap items-center gap-3 border-t border-gray-200 px-5 py-4 dark:border-white/[0.06]">
        <template v-if="editing">
          <BaseButton size="sm" variant="primary" @click="emit('save-edit')">
            <i class="fa-solid fa-check"></i>
            保存修改
          </BaseButton>
          <BaseButton size="sm" variant="secondary" @click="emit('cancel-edit')">取消</BaseButton>
        </template>
        <template v-else>
          <BaseButton size="sm" variant="secondary" @click="emit('start-edit')">
            <i class="fa-solid fa-pen"></i>
            编辑笔记
          </BaseButton>
          <BaseButton size="sm" variant="secondary" @click="emit('close-detail')">
            <i class="fa-solid fa-list"></i>
            返回列表
          </BaseButton>
        </template>
      </footer>
    </template>

    <BaseEmptyState v-else icon="fa-solid fa-book-open-reader" title="请选择一条笔记" description="从左侧列表选择笔记后，这里会展示整理后的 Markdown 内容。" />
  </section>
</template>
