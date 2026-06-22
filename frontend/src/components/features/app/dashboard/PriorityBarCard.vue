<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { TooltipComponent, GridComponent } from 'echarts/components'
import { BarChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'
import BaseCard from '@/components/base/BaseCard.vue'

echarts.use([TooltipComponent, GridComponent, BarChart, CanvasRenderer])

const props = defineProps({
  items: { type: Array, default: () => [] },
  themeMode: { type: String, default: 'auto' },
  compact: { type: Boolean, default: false },
})

const chartRef = ref(null)
let chart = null
let resizeObserver = null
let themeObserver = null

const isDark = () => {
  if (props.themeMode === 'dark') return true
  if (props.themeMode === 'light') return false
  return typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
}

const toneColor = (tone) => {
  if (tone === 'rose') return '#f43f5e'
  if (tone === 'amber') return '#f59e0b'
  if (tone === 'blue') return '#3b82f6'
  if (tone === 'emerald') return '#10b981'
  return '#6366f1'
}

const getOption = () => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    borderWidth: 0,
    backgroundColor: isDark() ? 'rgba(20,20,24,0.94)' : 'rgba(15,23,42,0.92)',
    textStyle: { color: '#f8fafc', fontSize: 12 },
    formatter: (items) => {
      const item = items?.[0]
      if (!item) return ''
      return `${item.name}<br/>${item.value}${props.items[item.dataIndex]?.unit || ''}`
    },
  },
  grid: {
    left: props.compact ? 78 : 90,
    right: props.compact ? 8 : 20,
    top: props.compact ? 6 : 16,
    bottom: props.compact ? 0 : 10,
    containLabel: !props.compact,
  },
  xAxis: {
    type: 'value',
    axisLabel: {
      show: !props.compact,
      color: isDark() ? '#94a3b8' : '#64748b',
      fontSize: 11,
    },
    axisTick: { show: false },
    axisLine: { show: !props.compact },
    splitLine: { lineStyle: { color: isDark() ? 'rgba(148,163,184,0.10)' : 'rgba(148,163,184,0.18)' } },
  },
  yAxis: {
    type: 'category',
    data: props.items.map(item => item.title),
    axisLabel: {
      color: isDark() ? '#cbd5e1' : '#334155',
      fontSize: props.compact ? 11 : 12,
      fontWeight: 600,
      width: props.compact ? 72 : undefined,
      align: 'right',
      margin: props.compact ? 6 : 12,
      overflow: props.compact ? 'truncate' : undefined,
    },
    axisLine: { show: false },
    axisTick: { show: false },
  },
  series: [
    {
      type: 'bar',
      data: props.items.map(item => ({
        value: item.value,
        itemStyle: {
          color: toneColor(item.tone),
          borderRadius: [0, 6, 6, 0],
        },
      })),
      barWidth: props.compact ? 12 : 16,
      barCategoryGap: props.compact ? '34%' : '42%',
      showBackground: true,
      backgroundStyle: {
        color: isDark() ? 'rgba(255,255,255,0.05)' : 'rgba(148,163,184,0.10)',
        borderRadius: [0, 6, 6, 0],
      },
      label: {
        show: true,
        position: 'right',
        color: isDark() ? '#e2e8f0' : '#0f172a',
        fontWeight: 700,
        fontSize: props.compact ? 11 : 12,
        formatter: ({ value, dataIndex }) => `${value}${props.items[dataIndex]?.unit || ''}`,
      },
    },
  ],
})

const renderChart = async () => {
  if (!props.items.length) return
  await nextTick()
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption(getOption(), true)
  chart.resize()
}

watch(() => props.items, renderChart, { deep: true })

onMounted(() => {
  renderChart()
  if (chartRef.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => chart?.resize())
    resizeObserver.observe(chartRef.value)
  }
  if (typeof MutationObserver !== 'undefined' && typeof document !== 'undefined') {
    themeObserver = new MutationObserver(() => renderChart())
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  themeObserver?.disconnect()
  chart?.dispose()
  chart = null
})
</script>

<template>
  <BaseCard rounded="rounded-lg" padding="p-5" class="h-full flex flex-col">
    <div class="mb-5">
      <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400 dark:text-[#707783]">Priority</p>
      <h3 class="text-base font-semibold text-slate-900 dark:text-white">复习优先级</h3>
      <p class="mt-1 text-xs text-slate-500 dark:text-[#8a8f98]">按当前影响程度排序显示</p>
    </div>
    <div ref="chartRef" class="h-[360px] w-full flex-1"></div>
  </BaseCard>
</template>
