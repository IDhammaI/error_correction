<script setup>
/**
 * NoteToolbar.vue
 * 笔记库顶部筛选工具栏。
 */
import BaseSearchInput from '@/components/base/BaseSearchInput.vue'
import BaseSearchableSelect from '@/components/base/BaseSearchableSelect.vue'
import ViewSettingsPopover from '@/components/features/app/shared/ViewSettingsPopover.vue'

defineProps({
  filters: { type: Object, required: true },
  subjects: { type: Array, default: () => [] },
  tagNames: { type: Array, default: () => [] },
  selectedTags: { type: Set, required: true },
  total: { type: Number, default: 0 },
  filterPanelOpen: { type: Boolean, default: false },
})

const emit = defineEmits([
  'update:filterPanelOpen',
  'toggle-tag',
  'reset',
])
</script>

<template>
  <div class="relative z-20 flex shrink-0 flex-wrap items-center gap-2">
    <BaseSearchInput v-model="filters.keyword" placeholder="搜索笔记..." class="w-64" />
    <BaseSearchableSelect
      v-model="filters.subject"
      :options="subjects"
      placeholder="全部学科"
      search-placeholder="搜索学科"
      width-class="w-36"
      multiple
    />
    <BaseSearchableSelect
      v-model="filters.tag"
      :options="tagNames"
      placeholder="全部知识点"
      search-placeholder="搜索知识点"
      width-class="w-40"
      dropdown-align="right"
      multiple
    />

    <div class="ml-auto flex items-center gap-2">
      <button
        class="flex h-9 w-9 items-center justify-center rounded-md border transition-colors"
        :class="filterPanelOpen ? 'accent-bg-soft accent-text accent-border' : 'border-gray-200 bg-white text-gray-500 hover:bg-gray-50 hover:text-gray-700 dark:border-white/[0.06] dark:bg-white/[0.03] dark:text-[#8a8f98] dark:hover:bg-white/[0.06] dark:hover:text-[#d0d6e0]'"
        title="筛选设置"
        @click.stop="emit('update:filterPanelOpen', !filterPanelOpen)"
      >
        <i class="fa-solid fa-sliders text-xs"></i>
      </button>
      <ViewSettingsPopover
        :model-value="filterPanelOpen"
        :filters="filters"
        :subjects="subjects"
        :tag-names="tagNames"
        :selected-tags="selectedTags"
        :show-review-status="false"
        :show-question-type="false"
        @update:model-value="(value) => emit('update:filterPanelOpen', value)"
        @toggle-tag="(tag) => emit('toggle-tag', tag)"
        @reset="emit('reset')"
      />
      <span class="text-xs text-gray-500 dark:text-[#8a8f98]">共 {{ total }} 条笔记</span>
    </div>
  </div>
</template>
