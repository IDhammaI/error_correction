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

const mockMistakeAnalysis = {
  knowledge_points: ['圆锥体积', '立体几何', '统计', '样本方差', '假设检验'],
  error_types: ['概念混淆', '公式误用', '审题遗漏'],
  error_symptoms: ['把题目中的处理效应与样本差异混在一起判断。'],
  correction_suggestions: [
    '先复习统计量、样本方差和假设检验的适用条件。',
    '补做 3-5 道同类统计推断题，重点训练变量含义识别。',
    '解题时先圈出实验对象、处理方式和待比较指标。',
  ],
  confidence: 0.82,
}

const mistakeAnalysis = computed(() => ({
  ...mockMistakeAnalysis,
  knowledge_points: props.knowledgeTags.length ? props.knowledgeTags : mockMistakeAnalysis.knowledge_points,
}))

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
    <BasePanel body-class="max-h-72 p-4">
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

    <BasePanel body-class="max-h-72 p-4">
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
          <div class="rounded-xl bg-white/70 p-3 text-sm leading-6 text-gray-600 shadow-inner shadow-black/[0.03] dark:bg-white/[0.035] dark:text-[#b8bec8] dark:shadow-black/20">
            {{ mistakeAnalysis.error_symptoms[0] }}
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

    <BasePanel body-class="max-h-72 p-4">
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
