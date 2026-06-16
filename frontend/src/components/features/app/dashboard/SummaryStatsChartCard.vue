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
  if (tone === 'blue') return '#3b82f6'
  if (tone === 'emerald') return '#10b981'
  if (tone === 'rose') return '#f43f5e'
  if (tone === 'slate') return '#64748b'
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
    left: 24,
    right: 16,
    top: 20,
    bottom: 30,
    containLabel: true,
  },
  xAxis: {
    type: 'category',
    data: props.items.map(item => item.label),
    axisLabel: { color: isDark() ? '#94a3b8' : '#64748b', fontSize: 11, interval: 0 },
    axisTick: { show: false },
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: isDark() ? '#94a3b8' : '#64748b', fontSize: 11 },
    splitLine: { lineStyle: { color: isDark() ? 'rgba(148,163,184,0.10)' : 'rgba(148,163,184,0.18)' } },
  },
  series: [
    {
      type: 'bar',
      barMaxWidth: 28,
      data: props.items.map(item => ({
        value: item.value,
        itemStyle: {
          color: toneColor(item.tone),
          borderRadius: [8, 8, 0, 0],
        },
      })),
      label: {
        show: true,
        position: 'top',
        color: isDark() ? '#e2e8f0' : '#0f172a',
        fontWeight: 700,
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
      <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400 dark:text-[#707783]">Overview</p>
      <h3 class="text-base font-semibold text-slate-900 dark:text-white">学习概览</h3>
      <p class="mt-1 text-xs text-slate-500 dark:text-[#8a8f98]">核心指标分布与当前水平</p>
    </div>
    <div ref="chartRef" class="h-[360px] w-full flex-1"></div>
  </BaseCard>
</template>
