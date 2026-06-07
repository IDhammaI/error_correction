<script setup>
/**
 * ErrorLearningAside.vue
 * 错题库右侧学习分析栏。
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import 'echarts-wordcloud'
import BaseButton from '@/components/base/BaseButton.vue'
import BasePanel from '@/components/base/BasePanel.vue'

echarts.use([TooltipComponent, CanvasRenderer])

const props = defineProps({
  knowledgeTags: { type: Array, default: () => [] },
  errorPatternRows: { type: Array, default: () => [] },
  aiSummary: { type: String, default: '' },
  aiLoading: { type: Boolean, default: false },
})

const emit = defineEmits(['request-analysis'])

const chartRef = ref(null)
let chart = null
let resizeObserver = null

const cloudColors = ['#34d399', '#60a5fa', '#facc15', '#a78bfa', '#fb7185', '#22d3ee', '#fb923c', '#cbd5e1']

/**
 * 错因类型模板库
 * 每种错因类型包含症状和修正建议的模板，支持 {tag}/{tag1}/{tag2} 占位符
 */
const ERROR_TYPE_PROFILES = [
  {
    type: '概念混淆',
    symptoms: [
      '将 {tag1} 与 {tag2} 的定义条件混淆，未区分两者的适用范围。',
      '对 {tag} 的核心概念理解偏差，套用了错误的解题框架。',
    ],
    suggestions: [
      '对比整理 {tag} 与易混淆概念的定义差异，制作对照表。',
      '重做 2-3 道以 {tag} 为核心的选择题，重点识别概念边界。',
    ],
    confidenceRange: [0.72, 0.88],
  },
  {
    type: '公式误用',
    symptoms: [
      '{tag} 相关公式记混或用错，代入了不匹配的变量。',
      '在 {tag} 的计算中，未注意公式的前提条件。',
    ],
    suggestions: [
      '整理 {tag} 涉及的核心公式，标注每个公式的适用条件。',
      '做 3 道变形题，训练识别题目条件与公式的对应关系。',
    ],
    confidenceRange: [0.68, 0.85],
  },
  {
    type: '审题遗漏',
    symptoms: [
      '忽略了题干中关于 {tag} 的关键限定条件。',
      '跳读导致遗漏了题目中的隐含条件或单位换算。',
    ],
    suggestions: [
      '审题时逐句圈画关键词，尤其是限定词、单位和否定词。',
      '训练"读题-画关键信息-列条件"的三步审题习惯。',
    ],
    confidenceRange: [0.75, 0.92],
  },
  {
    type: '计算错误',
    symptoms: [
      '{tag} 的推导过程正确，但在中间步骤出现计算失误。',
      '运算过程中符号处理不当，导致最终结果偏离。',
    ],
    suggestions: [
      '分步书写计算过程，每步结果单独验算。',
      '整理易错运算类型（如正负号、括号展开），建立个人检查清单。',
    ],
    confidenceRange: [0.82, 0.95],
  },
  {
    type: '知识点遗忘',
    symptoms: [
      '对 {tag} 的基础定理/公式记忆模糊，解题时无法快速调用。',
      '缺乏对 {tag} 相关知识体系的整体回顾。',
    ],
    suggestions: [
      '针对 {tag} 做一次完整知识点回顾，重新推导核心公式。',
      '制作 {tag} 的思维导图，建立知识脉络。',
    ],
    confidenceRange: [0.65, 0.80],
  },
  {
    type: '解题思路错误',
    symptoms: [
      '面对 {tag} 相关问题时，选择了低效或错误的切入点。',
      '缺乏从题目条件到 {tag} 解法的逻辑推演能力。',
    ],
    suggestions: [
      '总结 {tag} 常见题型的解题模板，归纳通用思路。',
      '对比正确解法和自己的思路，分析偏差产生的环节。',
    ],
    confidenceRange: [0.60, 0.78],
  },
]

/**
 * 根据知识点标签确定性生成错因分析
 * 使用标签字符串长度作为哈希种子，确保同一题目每次生成相同的分析
 */
const generateMockAnalysis = (tags) => {
  const safeTags = tags.length ? tags : ['基础知识']
  const tagHash = safeTags.join('').length

  // 根据哈希值确定错因类型数量（2-3种）
  const typeCount = 2 + (tagHash % 2)

  // 确定性洗牌选择错因类型
  const shuffled = [...ERROR_TYPE_PROFILES].sort((a, b) => {
    return (a.type.length + tagHash) % 3 - (b.type.length + tagHash) % 3
  })
  const selectedTypes = shuffled.slice(0, typeCount)

  // 填充模板占位符
  const fillTemplate = (template) => {
    return template
      .replace('{tag}', safeTags[0])
      .replace('{tag1}', safeTags[0])
      .replace('{tag2}', safeTags[1] || safeTags[0])
  }

  const primary = selectedTypes[0]
  const confidence = primary.confidenceRange[0] +
    (tagHash % 100) / 100 * (primary.confidenceRange[1] - primary.confidenceRange[0])

  return {
    knowledge_points: safeTags,
    error_types: selectedTypes.map(t => t.type),
    error_symptoms: selectedTypes.map(t =>
      fillTemplate(t.symptoms[tagHash % t.symptoms.length])
    ),
    correction_suggestions: selectedTypes.slice(0, 2).map(t =>
      fillTemplate(t.suggestions[0])
    ),
    confidence: Math.round(confidence * 100) / 100,
  }
}

const mistakeAnalysis = computed(() => generateMockAnalysis(props.knowledgeTags))

const wordCloudData = computed(() => mistakeAnalysis.value.knowledge_points.slice(0, 12).map((tag, index) => ({
  name: tag,
  value: Math.max(18, 100 - index * 9),
})))

const confidencePercent = computed(() => Math.round((mistakeAnalysis.value.confidence || 0) * 100))

const getWordCloudOption = () => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'item',
    borderWidth: 0,
    backgroundColor: 'rgba(20,20,24,0.92)',
    textStyle: { color: '#f7f8f8', fontSize: 12 },
    formatter: ({ name }) => name,
  },
  series: [{
    type: 'wordCloud',
    shape: 'circle',
    width: '96%',
    height: '92%',
    left: 'center',
    top: 'center',
    sizeRange: [12, 25],
    rotationRange: [-18, 18],
    rotationStep: 6,
    gridSize: 6,
    drawOutOfBound: false,
    shrinkToFit: true,
    textStyle: {
      fontFamily: 'ui-sans-serif, system-ui, sans-serif',
      fontWeight: 700,
      color: ({ dataIndex }) => cloudColors[dataIndex % cloudColors.length],
      textShadowBlur: 12,
      textShadowColor: 'rgba(16,185,129,0.18)',
    },
    emphasis: {
      focus: 'self',
      textStyle: {
        textShadowBlur: 16,
        textShadowColor: 'rgba(16,185,129,0.45)',
      },
    },
    data: wordCloudData.value,
  }],
})

const renderWordCloud = async () => {
  if (!wordCloudData.value.length) return
  await nextTick()
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption(getWordCloudOption(), true)
  chart.resize()
}

watch(wordCloudData, () => {
  if (wordCloudData.value.length) renderWordCloud()
  else if (chart) chart.clear()
}, { deep: true })

onMounted(() => {
  renderWordCloud()
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => chart?.resize())
    resizeObserver.observe(chartRef.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chart?.dispose()
  chart = null
})
</script>

<template>
  <aside class="hidden min-h-0 flex-col gap-4 overflow-y-auto custom-scrollbar xl:flex">
    <BasePanel :scroll-body="false" body-class="p-4">
      <h3 class="mb-4 text-sm font-bold text-gray-900 dark:text-[#f7f8f8]">错题知识点</h3>
      <div v-if="wordCloudData.length" class="relative h-32 overflow-hidden rounded-xl bg-white/70 shadow-inner shadow-black/[0.03] dark:bg-white/[0.035] dark:shadow-black/20">
        <div class="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(16,185,129,0.16),transparent_58%)]"></div>
        <div ref="chartRef" class="relative h-full w-full"></div>
      </div>
      <div v-else class="grid h-32 place-items-center rounded-xl bg-white/70 text-xs text-gray-500 shadow-inner shadow-black/[0.03] dark:bg-white/[0.035] dark:text-[#8a8f98] dark:shadow-black/20">
        <div class="text-center">
          <i class="fa-solid fa-tags mb-2 block text-lg text-gray-400 dark:text-[#62666d]"></i>
          暂无知识点标签
        </div>
      </div>
    </BasePanel>

    <BasePanel :scroll-body="false" body-class="p-4">
      <h3 class="mb-4 text-sm font-bold text-gray-900 dark:text-[#f7f8f8]">错因分析</h3>
      <div class="space-y-4">
        <div>
          <p class="mb-2 text-xs font-medium text-gray-500 dark:text-[#8a8f98]">错因类型</p>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="type in mistakeAnalysis.error_types"
              :key="type"
              class="rounded-lg bg-rose-500/12 px-2.5 py-1 text-xs font-semibold text-rose-300"
            >
              {{ type }}
            </span>
          </div>
        </div>

        <div>
          <p class="mb-2 text-xs font-medium text-gray-500 dark:text-[#8a8f98]">错误表现</p>
          <div class="space-y-2">
            <div
              v-for="(symptom, idx) in mistakeAnalysis.error_symptoms"
              :key="idx"
              class="rounded-xl bg-white/70 p-3 text-sm leading-6 text-gray-600 shadow-inner shadow-black/[0.03] dark:bg-white/[0.035] dark:text-[#b8bec8] dark:shadow-black/20"
            >
              <span class="mr-1 font-bold text-rose-400">{{ idx + 1 }}.</span>
              {{ symptom }}
            </div>
          </div>
        </div>

        <div>
          <div class="mb-1.5 flex items-center justify-between text-xs">
            <span class="font-medium text-gray-500 dark:text-[#8a8f98]">AI 置信度</span>
            <span class="font-bold text-emerald-300">{{ confidencePercent }}%</span>
          </div>
          <div class="h-1.5 overflow-hidden rounded-full bg-gray-100 dark:bg-white/[0.06]">
            <div class="h-full rounded-full bg-emerald-400" :style="{ width: confidencePercent + '%' }"></div>
          </div>
        </div>
      </div>
    </BasePanel>

    <BasePanel :scroll-body="false" body-class="p-4">
      <h3 class="mb-3 text-sm font-bold text-gray-900 dark:text-[#f7f8f8]">修正建议</h3>
      <div class="space-y-2 text-sm text-gray-600 dark:text-[#b8bec8]">
        <div
          v-for="suggestion in mistakeAnalysis.correction_suggestions"
          :key="suggestion"
          class="flex gap-2 rounded-xl bg-white/70 p-3 leading-6 shadow-inner shadow-black/[0.03] dark:bg-white/[0.035] dark:shadow-black/20"
        >
          <i class="fa-solid fa-circle-check mt-1 text-xs text-blue-400"></i>
          <span>{{ suggestion }}</span>
        </div>
      </div>
      <BaseButton class="mt-5 w-full" size="sm" variant="primary" :disabled="aiLoading" @click="emit('request-analysis')">
        <i class="fa-solid" :class="aiLoading ? 'fa-circle-notch fa-spin' : 'fa-wand-magic-sparkles'"></i>
        {{ aiLoading ? '分析中...' : '重新生成分析' }}
      </BaseButton>
    </BasePanel>
  </aside>
</template>
