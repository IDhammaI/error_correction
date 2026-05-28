<script setup>
/**
 * ErrorQuestionFinderAside.vue
 * Natural-language question finder for the error bank.
 */
import { onBeforeUnmount, ref, watch } from 'vue'
import * as api from '@/api/index.js'
import BasePanel from '@/components/base/BasePanel.vue'
import BaseSearchInput from '@/components/base/BaseSearchInput.vue'
import { getQuestionSnippet } from '@/utils/index.js'

const props = defineProps({
  projectId: { type: [String, Number, null], default: null },
})

const emit = defineEmits(['select-question', 'error'])

const query = ref('')
const searching = ref(false)
const searched = ref(false)
const results = ref([])
let searchTimer = null
let requestSeq = 0

const examples = [
  '找那道关于二次函数顶点坐标的题',
  '上次做错的三角函数图像平移选择题',
  '答案里提到样本方差的统计题',
]

const runSearch = async () => {
  const text = query.value.trim()
  if (!text) {
    searched.value = false
    results.value = []
    return
  }

  const seq = ++requestSeq
  searching.value = true
  searched.value = true
  try {
    const data = await api.findQuestionsByDescription(text, {
      projectId: props.projectId,
      limit: 8,
    })
    if (seq === requestSeq) results.value = data.items || []
  } catch (error) {
    if (seq === requestSeq) {
      results.value = []
      emit('error', error)
    }
  } finally {
    if (seq === requestSeq) searching.value = false
  }
}

const scheduleSearch = () => {
  if (searchTimer) window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(runSearch, 420)
}

const applyExample = (example) => {
  query.value = example
  runSearch()
}

watch(query, scheduleSearch)
watch(() => props.projectId, runSearch)

onBeforeUnmount(() => {
  if (searchTimer) window.clearTimeout(searchTimer)
})
</script>

<template>
  <aside class="hidden min-h-0 flex-col gap-4 overflow-y-auto custom-scrollbar xl:flex">
    <BasePanel :scroll-body="false" body-class="p-4">
      <h3 class="mb-3 text-sm font-bold text-gray-900 dark:text-[#f7f8f8]">AI 找题</h3>
      <div class="flex gap-2">
        <BaseSearchInput
          v-model="query"
          class="min-w-0 flex-1"
          icon="fa-solid fa-wand-magic-sparkles"
          placeholder="描述你想找的题..."
        />
        <button
          type="button"
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-[rgb(var(--accent-rgb))] text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="searching || !query.trim()"
          @click="runSearch"
        >
          <i class="fa-solid" :class="searching ? 'fa-spinner animate-spin' : 'fa-arrow-right'"></i>
        </button>
      </div>
      <p class="mt-3 text-xs leading-5 text-gray-500 dark:text-[#8a8f98]">
        可以描述题干片段、知识点、题型、答案印象或做题场景，系统会在当前错题库里找最像的题。
      </p>
    </BasePanel>

    <BasePanel :scroll-body="false" body-class="p-4">
      <h3 class="mb-3 text-sm font-bold text-gray-900 dark:text-[#f7f8f8]">可以这样问</h3>
      <div class="space-y-2">
        <button
          v-for="example in examples"
          :key="example"
          type="button"
          class="w-full rounded-md bg-white/70 px-3 py-2 text-left text-xs leading-5 text-gray-600 transition-colors hover:bg-white dark:bg-white/[0.035] dark:text-[#b8bec8] dark:hover:bg-white/[0.065]"
          @click="applyExample(example)"
        >
          {{ example }}
        </button>
      </div>
    </BasePanel>

    <BasePanel :scroll-body="false" body-class="p-4">
      <div class="mb-3 flex items-center justify-between gap-3">
        <h3 class="text-sm font-bold text-gray-900 dark:text-[#f7f8f8]">匹配结果</h3>
        <span v-if="searched" class="text-xs text-gray-500 dark:text-[#8a8f98]">{{ results.length }} 条</span>
      </div>

      <div v-if="!query.trim()" class="rounded-md bg-white/70 p-4 text-sm leading-6 text-gray-500 dark:bg-white/[0.035] dark:text-[#8a8f98]">
        输入一句话后，这里会展示最可能的题目。
      </div>

      <div v-else-if="searching" class="space-y-2">
        <div v-for="i in 3" :key="i" class="h-24 animate-pulse rounded-md bg-white/70 dark:bg-white/[0.04]"></div>
      </div>

      <div v-else-if="results.length" class="space-y-2">
        <button
          v-for="result in results"
          :key="result.id"
          type="button"
          class="w-full rounded-md bg-white/70 p-3 text-left transition-colors hover:bg-white dark:bg-white/[0.035] dark:hover:bg-white/[0.065]"
          @click="emit('select-question', result)"
        >
          <div class="mb-2 flex items-center justify-between gap-3">
            <span class="text-xs font-bold accent-text">匹配度 {{ result.match_score || 0 }}%</span>
            <i class="fa-solid fa-arrow-right text-[10px] text-gray-400 dark:text-[#62666d]"></i>
          </div>
          <p class="line-clamp-2 text-sm leading-6 text-gray-700 dark:text-[#d0d6e0]">
            {{ getQuestionSnippet(result, 96, '暂无题干内容') }}
          </p>
          <div v-if="result.match_reasons?.length" class="mt-2 flex flex-wrap gap-1.5">
            <span
              v-for="reason in result.match_reasons"
              :key="reason"
              class="rounded-full bg-[rgb(var(--accent-rgb)/0.10)] px-2 py-0.5 text-[11px] font-medium text-[rgb(var(--accent-hover-rgb))]"
            >
              {{ reason }}
            </span>
          </div>
        </button>
      </div>

      <div v-else class="rounded-md bg-white/70 p-4 text-sm leading-6 text-gray-500 dark:bg-white/[0.035] dark:text-[#8a8f98]">
        没找到合适题目，可以换个描述，或加入学科、题型、答案片段再试。
      </div>
    </BasePanel>
  </aside>
</template>
