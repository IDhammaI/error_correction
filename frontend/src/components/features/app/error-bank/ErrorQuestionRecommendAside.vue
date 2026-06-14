<script setup>
/**
 * ErrorQuestionRecommendAside.vue
 * 错题库右侧同类题推荐栏。
 * ⚠️ 纯前端模拟实现，仅用于演示展示，后续将接入后端推荐算法。
 * 基于知识点重叠、学科、题型和内容相似度，纯前端筛选推荐相似题目。
 */
import { computed } from 'vue'
import BaseEmptyState from '@/components/base/BaseEmptyState.vue'
import BasePanel from '@/components/base/BasePanel.vue'
import BaseTag from '@/components/base/BaseTag.vue'
import { getQuestionSnippet } from '@/utils/index.js'

const props = defineProps({
  currentQuestion: { type: Object, default: null },
  allItems: { type: Array, default: () => [] },
})

const emit = defineEmits(['select-question'])

/**
 * 提取题目文本内容的分词
 */
const getTokens = (question) => {
  const blocks = question.content_json || []
  return blocks
    .filter(b => b.block_type === 'text')
    .map(b => b.content || '')
    .join(' ')
    .replace(/<[^>]+>/g, '')
    .split(/[\s,，。、；：！？""''（）\(\)]+/)
    .filter(t => t.length >= 2)
}

/**
 * 生成推荐理由
 */
const generateReasons = (matchedTags, current, candidate) => {
  const reasons = []
  if (matchedTags.length > 0) {
    reasons.push(`共同知识点：${matchedTags.slice(0, 2).join('、')}`)
  }
  if (current.subject === candidate.subject && current.subject) {
    reasons.push(`同属${current.subject}学科`)
  }
  if (current.question_type === candidate.question_type && current.question_type) {
    reasons.push(`同为${current.question_type}`)
  }
  return reasons.slice(0, 3)
}

/**
 * 计算两道题目的相似度（0-100）
 */
const computeSimilarity = (current, candidate) => {
  if (!current || !candidate || current.id === candidate.id) return null

  // 1. 知识点重叠（Jaccard相似度，权重0.5）
  const currentTags = new Set(current.knowledge_tags || [])
  const candidateTags = new Set(candidate.knowledge_tags || [])
  const intersection = new Set([...currentTags].filter(t => candidateTags.has(t)))
  const union = new Set([...currentTags, ...candidateTags])
  const tagSimilarity = union.size > 0 ? intersection.size / union.size : 0

  // 2. 学科匹配（权重0.2）
  const subjectSimilarity = current.subject === candidate.subject ? 1 : 0

  // 3. 题型匹配（权重0.15）
  const typeSimilarity = current.question_type === candidate.question_type ? 1 : 0

  // 4. 内容关键词重叠（权重0.15）
  const currentTokens = new Set(getTokens(current))
  const candidateTokens = new Set(getTokens(candidate))
  const tokenIntersection = new Set([...currentTokens].filter(t => candidateTokens.has(t)))
  const tokenUnion = new Set([...currentTokens, ...candidateTokens])
  const contentSimilarity = tokenUnion.size > 0 ? tokenIntersection.size / tokenUnion.size : 0

  // 加权计算总分
  const score = tagSimilarity * 0.5 + subjectSimilarity * 0.2 + typeSimilarity * 0.15 + contentSimilarity * 0.15

  return {
    question: candidate,
    similarity: Math.round(score * 100),
    matchedTags: [...intersection],
    matchReasons: generateReasons([...intersection], current, candidate),
  }
}

/**
 * 推荐题目列表（按相似度降序，最多5道）
 */
const recommended = computed(() => {
  if (!props.currentQuestion || !props.allItems.length) return []
  return props.allItems
    .map(item => computeSimilarity(props.currentQuestion, item))
    .filter(Boolean)
    .filter(r => r.similarity > 0)
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, 5)
})

/**
 * 相似度徽章颜色
 */
const similarityBadgeClass = (similarity) => {
  if (similarity >= 80) return 'bg-emerald-500/15 text-emerald-300'
  if (similarity >= 60) return 'bg-amber-500/15 text-amber-300'
  return 'bg-gray-500/15 text-gray-400'
}
</script>

<template>
  <aside class="hidden min-h-0 flex-col xl:flex">
    <div class="shrink-0">
      <BasePanel :scroll-body="false" body-class="p-4">
        <div class="mb-3 flex items-center justify-between gap-3">
          <h3 class="text-sm font-bold text-gray-900 dark:text-[#f7f8f8]">
            <i class="fa-solid fa-shuffle mr-1.5 text-blue-400"></i>
            同类题推荐
          </h3>
          <span class="text-xs text-gray-500 dark:text-[#8a8f98]">{{ recommended.length }} 道</span>
        </div>
        <p class="text-xs leading-5 text-gray-500 dark:text-[#8a8f98]">
          基于当前题目的知识点、学科和题型，智能推荐相似题目。
        </p>
        <p class="mt-2 inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-600 dark:bg-amber-400/10 dark:text-amber-400">
          <i class="fa-solid fa-flask"></i>
          纯前端模拟，仅展示
        </p>
      </BasePanel>
    </div>

    <div class="min-h-0 flex-1 space-y-3 overflow-y-auto custom-scrollbar py-3">
      <div v-if="!currentQuestion" class="rounded-xl bg-white/85 p-4 text-sm leading-6 text-gray-500 shadow-sm shadow-black/[0.03] dark:bg-white/[0.04] dark:text-[#8a8f98] dark:shadow-black/20">
        请先选择一道题目，这里会展示相似的题目推荐。
      </div>

      <div v-else-if="!recommended.length" class="rounded-xl bg-white/85 p-4 shadow-sm shadow-black/[0.03] dark:bg-white/[0.04] dark:shadow-black/20">
        <BaseEmptyState
          icon="fa-regular fa-face-meh"
          title="暂无同类题"
          description="当前错题库中没有找到相似的题目，可以继续录入更多题目。"
        />
      </div>

      <button
        v-for="item in recommended"
        :key="item.question.id"
        v-else
        type="button"
        class="w-full rounded-xl bg-white/85 p-4 text-left shadow-sm shadow-black/[0.03] transition-colors hover:bg-white hover:shadow-md dark:bg-white/[0.04] dark:hover:bg-white/[0.07] dark:shadow-black/20"
        @click="emit('select-question', item.question)"
      >
        <div class="mb-2 flex items-center justify-between gap-2">
          <span
            class="rounded-full px-2.5 py-0.5 text-xs font-bold"
            :class="similarityBadgeClass(item.similarity)"
          >
            {{ item.similarity }}%
          </span>
          <i class="fa-solid fa-arrow-right text-[10px] text-gray-400 dark:text-[#62666d]"></i>
        </div>

        <p class="text-sm leading-6 text-gray-700 dark:text-[#d0d6e0]">
          {{ getQuestionSnippet(item.question, 120, '暂无题干内容') }}
        </p>

        <div v-if="item.question.knowledge_tags?.length" class="mt-2 flex flex-wrap gap-1.5">
          <BaseTag
            v-for="tag in item.question.knowledge_tags.slice(0, 3)"
            :key="tag"
            :tone="item.matchedTags.includes(tag) ? 'accent' : undefined"
          >
            {{ tag }}
          </BaseTag>
        </div>

        <div v-if="item.matchReasons.length" class="mt-2.5 flex flex-wrap gap-1.5">
          <span
            v-for="reason in item.matchReasons"
            :key="reason"
            class="rounded-full bg-[rgb(var(--accent-rgb)/0.10)] px-2 py-0.5 text-[11px] font-medium text-[rgb(var(--accent-hover-rgb))]"
          >
            {{ reason }}
          </span>
        </div>
      </button>
    </div>
  </aside>
</template>
