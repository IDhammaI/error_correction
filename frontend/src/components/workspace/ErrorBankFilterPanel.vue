<script setup>
/**
 * ErrorBankFilterPanel.vue
 * 错题库筛选侧边栏
 */
import BaseSelect from '@/components/base/BaseSelect.vue'

const props = defineProps({
  filters: Object,
  subjects: Array,
  questionTypes: Array,
  tagNames: Array,
  selectedTags: Set,
})

const emit = defineEmits(['close', 'toggle-tag'])
</script>

<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between">
      <span class="text-xs font-medium text-slate-700 dark:text-[#f7f8f8]">筛选设置</span>
      <button @click="emit('close')" class="text-slate-400 hover:text-slate-600 dark:text-[#62666d] dark:hover:text-[#8a8f98] transition-colors">
        <i class="fa-solid fa-xmark text-xs"></i>
      </button>
    </div>

    <div>
      <label class="mb-1.5 block text-xs font-medium text-slate-500 dark:text-[#62666d]">学科</label>
      <BaseSelect v-model="filters.subject" :options="subjects" placeholder="全部学科" />
    </div>

    <div>
      <label class="mb-1.5 block text-xs font-medium text-slate-500 dark:text-[#62666d]">题型</label>
      <BaseSelect v-model="filters.question_type" :options="questionTypes" placeholder="全部题型" />
    </div>

    <div>
      <label class="mb-1.5 block text-xs font-medium text-slate-500 dark:text-[#62666d]">复习状态</label>
      <BaseSelect v-model="filters.review_status" :options="['待复习', '复习中', '已掌握']" placeholder="全部状态" />
    </div>

    <div v-if="tagNames?.length">
      <label class="mb-1.5 block text-xs font-medium text-slate-500 dark:text-[#62666d]">知识点</label>
      <div class="flex flex-wrap gap-1.5">
        <button v-for="tag in tagNames" :key="tag"
          @click="emit('toggle-tag', tag)"
          class="rounded-md px-2 py-0.5 text-xs font-medium transition-all"
          :class="selectedTags?.has(tag)
            ? 'bg-indigo-500 text-white dark:bg-[rgb(129,115,223)]'
            : 'border border-slate-200 bg-white text-slate-600 hover:text-slate-800 hover:border-slate-300 hover:bg-slate-50 dark:border-white/[0.06] dark:bg-white/[0.02] dark:text-[#62666d] dark:hover:text-[#8a8f98] dark:hover:border-white/[0.1] dark:hover:bg-white/[0.04]'"
        >{{ tag }}</button>
      </div>
    </div>
  </div>
</template>
