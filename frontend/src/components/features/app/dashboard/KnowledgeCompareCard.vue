<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { BarChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'
import BaseCard from '@/components/base/BaseCard.vue'

echarts.use([TooltipComponent, LegendComponent, GridComponent, BarChart, CanvasRenderer])

const props = defineProps({
  items: { type: Array, default: () => [] },
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

const formatAxisLabel = (label) => String(label || '').replace(/(.{4})/g, '$1\n').trim()

const getOption = () => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    borderWidth: 0,
    backgroundColor: isDark() ? 'rgba(20,20,24,0.94)' : 'rgba(15,23,42,0.92)',
    textStyle: { color: '#f8fafc', fontSize: 12 },
  },
  legend: {
    bottom: 0,
    left: 'center',
    textStyle: {
      color: isDark() ? '#94a3b8' : '#64748b',
      fontSize: 12,
      fontWeight: 600,
    },
  },
  grid: {
    left: 24,
    right: 16,
    top: 20,
    bottom: 40,
    containLabel: true,
  },
  xAxis: {
    type: 'category',
    data: props.items.map(item => item.label),
    axisLabel: {
      color: isDark() ? '#94a3b8' : '#64748b',
      fontSize: props.themeMode === 'light' ? 10 : 11,
      interval: 0,
      rotate: props.themeMode === 'light' ? 0 : 18,
      formatter: formatAxisLabel,
    },
    axisTick: { show: false },
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: isDark() ? '#94a3b8' : '#64748b', fontSize: 11 },
    splitLine: { lineStyle: { color: isDark() ? 'rgba(148,163,184,0.10)' : 'rgba(148,163,184,0.18)' } },
  },
  series: [
    {
      name: '掌握度',
      type: 'bar',
      barMaxWidth: 18,
      itemStyle: { color: '#2563eb', borderRadius: [6, 6, 0, 0] },
      data: props.items.map(item => item.score || 0),
    },
    {
      name: '班级平均',
      type: 'bar',
      barMaxWidth: 18,
      itemStyle: { color: 'rgba(34,197,94,0.78)', borderRadius: [6, 6, 0, 0] },
      data: props.items.map(item => item.average || 0),
    },
  ],
})

const renderChart = async () => {
  if (!props.items.length) return
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
      <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400 dark:text-[#707783]">Compare</p>
      <h3 class="text-base font-semibold text-slate-900 dark:text-white">知识点对比</h3>
      <p class="mt-1 text-xs text-slate-500 dark:text-[#8a8f98]">知识点掌握度与平均水平对比</p>
    </div>
    <div ref="chartRef" class="h-[360px] w-full flex-1"></div>
  </BaseCard>
</template>
