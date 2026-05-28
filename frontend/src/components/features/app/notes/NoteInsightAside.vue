<script setup>
/**
 * NoteInsightAside.vue
 * 笔记库右侧知识点、元信息与原图预览栏。
 */
import BaseTag from '@/components/base/BaseTag.vue'

defineProps({
  note: { type: Object, default: null },
  knowledgeTags: { type: Array, default: () => [] },
  sourceImages: { type: Array, default: () => [] },
})

const formatDate = (iso) => {
  if (!iso) return '暂无日期'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '暂无日期'
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
</script>

<template>
  <aside class="hidden min-h-0 flex-col gap-4 overflow-y-auto custom-scrollbar xl:flex">
    <section class="rounded-xl border border-gray-200 bg-white/80 p-4 dark:border-white/[0.07] dark:bg-white/[0.035]">
      <h3 class="mb-4 text-sm font-bold text-gray-900 dark:text-[#f7f8f8]">知识点</h3>
      <div class="flex flex-wrap gap-2">
        <BaseTag v-for="tag in knowledgeTags" :key="tag">{{ tag }}</BaseTag>
        <span v-if="!knowledgeTags.length" class="text-xs text-gray-500 dark:text-[#8a8f98]">暂无知识点标签</span>
      </div>
    </section>

    <section class="rounded-xl border border-gray-200 bg-white/80 p-4 dark:border-white/[0.07] dark:bg-white/[0.035]">
      <h3 class="mb-3 text-sm font-bold text-gray-900 dark:text-[#f7f8f8]">笔记信息</h3>
      <div class="space-y-3 text-sm text-gray-600 dark:text-[#b8bec8]">
        <div class="flex items-center justify-between gap-3">
          <span class="text-gray-400 dark:text-[#62666d]">更新时间</span>
          <span>{{ formatDate(note?.updated_at || note?.created_at) }}</span>
        </div>
        <div class="flex items-center justify-between gap-3">
          <span class="text-gray-400 dark:text-[#62666d]">来源图片</span>
          <span>{{ sourceImages.length }} 张</span>
        </div>
        <div class="flex items-center justify-between gap-3">
          <span class="text-gray-400 dark:text-[#62666d]">所属学科</span>
          <span>{{ note?.subject || '未标注' }}</span>
        </div>
      </div>
    </section>

    <section class="rounded-xl border border-gray-200 bg-white/80 p-4 dark:border-white/[0.07] dark:bg-white/[0.035]">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900 dark:text-[#f7f8f8]">原始图片</h3>
        <span class="text-xs text-gray-400 dark:text-[#62666d]">{{ sourceImages.length }} 张</span>
      </div>
      <div v-if="sourceImages.length" class="space-y-3">
        <img
          v-for="(src, idx) in sourceImages.slice(0, 3)"
          :key="idx"
          :src="'/uploads/' + src.split(/[\\/]/).pop()"
          class="max-h-44 w-full rounded-xl border border-gray-200 object-contain dark:border-white/[0.08]"
          @error="$event.target.style.display = 'none'"
        />
      </div>
      <div v-else class="flex h-28 items-center justify-center rounded-xl border border-dashed border-gray-200 text-xs text-gray-400 dark:border-white/[0.08] dark:text-[#62666d]">
        暂无原始图片
      </div>
    </section>
  </aside>
</template>
