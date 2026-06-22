<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { TooltipComponent, GridComponent } from 'echarts/components'
import { LineChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'
import BaseCard from '@/components/base/BaseCard.vue'

echarts.use([TooltipComponent, GridComponent, LineChart, CanvasRenderer])

const props = defineProps({
  trend: { type: Array, default: () => [] },
  themeMode: { type: String, default: 'auto' },
})

const chartRef = ref(null)
let chart = null
let resizeObserver = null
let themeObserver = null
let renderRetryTimer = null

const isDark = () => {
  if (props.themeMode === 'dark') return true
  if (props.themeMode === 'light') return false
  return typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
}

const getOption = () => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    borderWidth: 0,
    backgroundColor: isDark() ? 'rgba(20,20,24,0.94)' : 'rgba(15,23,42,0.92)',
    textStyle: { color: '#f8fafc', fontSize: 12 },
  },
  grid: {
    left: 20,
    right: 16,
    top: 16,
    bottom: 24,
    containLabel: true,
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: props.trend.map((_, index) => `第${index + 1}次`),
    axisLine: { lineStyle: { color: isDark() ? 'rgba(148,163,184,0.18)' : 'rgba(148,163,184,0.24)' } },
    axisLabel: { color: isDark() ? '#94a3b8' : '#64748b', fontSize: 11 },
    axisTick: { show: false },
  },
  yAxis: {
    type: 'value',
    splitNumber: 4,
    axisLabel: { color: isDark() ? '#94a3b8' : '#64748b', fontSize: 11 },
    splitLine: { lineStyle: { color: isDark() ? 'rgba(148,163,184,0.10)' : 'rgba(148,163,184,0.18)' } },
  },
  series: [
    {
      data: props.trend,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: { width: 3, color: '#2563eb' },
      itemStyle: { color: '#2563eb', borderWidth: 2, borderColor: '#ffffff' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(59,130,246,0.26)' },
            { offset: 1, color: 'rgba(59,130,246,0.02)' },
          ],
        },
      },
    },
  ],
})

const renderChart = async () => {
  if (!props.trend.length) return
  await nextTick()
  if (!chartRef.value) return
  await new Promise(resolve => requestAnimationFrame(resolve))
  if (chartRef.value.clientHeight === 0 || chartRef.value.clientWidth === 0) {
    if (renderRetryTimer) window.clearTimeout(renderRetryTimer)
    renderRetryTimer = window.setTimeout(() => {
      renderRetryTimer = null
      renderChart()
    }, 80)
    return
  }
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption(getOption(), true)
  chart.resize()
}

watch(() => props.trend, renderChart, { deep: true })

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
  if (renderRetryTimer) window.clearTimeout(renderRetryTimer)
  resizeObserver?.disconnect()
  themeObserver?.disconnect()
  chart?.dispose()
  chart = null
})
</script>

<template>
  <BaseCard rounded="rounded-lg" padding="p-5" class="h-full flex flex-col">
    <div class="mb-5">
      <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400 dark:text-[#707783]">Trend</p>
      <h3 class="text-base font-semibold text-slate-900 dark:text-white">学习趋势</h3>
      <p class="mt-1 text-xs text-slate-500 dark:text-[#8a8f98]">最近学习状态变化走势</p>
    </div>
    <div ref="chartRef" class="w-full flex-1 min-h-[360px]" style="height: 360px;"></div>
  </BaseCard>
</template>
