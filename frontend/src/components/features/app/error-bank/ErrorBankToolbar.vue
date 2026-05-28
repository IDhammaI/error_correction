<script setup>
/**
 * ErrorBankToolbar.vue
 * 错题库顶部筛选与视图操作栏。
 */
import BaseSearchInput from '@/components/base/BaseSearchInput.vue'
import BaseSelect from '@/components/base/BaseSelect.vue'
import BaseSearchableSelect from '@/components/base/BaseSearchableSelect.vue'

defineProps({
  filters: { type: Object, required: true },
  reviewStatusOptions: { type: Array, default: () => [] },
  tagNames: { type: Array, default: () => [] },
  questionTypes: { type: Array, default: () => [] },
  subjects: { type: Array, default: () => [] },
})
</script>

<template>
  <div class="flex shrink-0 flex-wrap items-center gap-3">
    <BaseSearchInput
      v-model="filters.keyword"
      class="min-w-[16rem] max-w-sm flex-1"
      placeholder="搜索题目、知识点、题号..."
    />

    <BaseSelect v-model="filters.review_status" :options="reviewStatusOptions" placeholder="全部状态" width-class="w-32" />
    <BaseSearchableSelect
      v-model="filters.knowledge_tag"
      :options="tagNames"
      placeholder="全部知识点"
      search-placeholder="搜索知识点"
      width-class="w-40"
      dropdown-align="right"
      multiple
    />
    <BaseSearchableSelect
      v-model="filters.question_type"
      :options="questionTypes"
      placeholder="全部题型"
      search-placeholder="搜索题型"
      width-class="w-36"
      dropdown-align="right"
      multiple
    />
    <BaseSearchableSelect
      v-model="filters.subject"
      :options="subjects"
      placeholder="全部学科"
      search-placeholder="搜索学科"
      width-class="w-36"
      multiple
    />

  </div>
</template>
