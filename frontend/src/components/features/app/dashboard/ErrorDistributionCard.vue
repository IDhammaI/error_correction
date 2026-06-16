<script setup>
import { nextTick, onBeforeUnmount, onMounted, watch, ref } from 'vue'
import * as echarts from 'echarts/core'
import { TooltipComponent, LegendComponent, GraphicComponent } from 'echarts/components'
import { PieChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'
import BaseCard from '@/components/base/BaseCard.vue'

echarts.use([TooltipComponent, LegendComponent, GraphicComponent, PieChart, CanvasRenderer])

const props = defineProps({
  items: { type: Array, default: () => [] },
  total: { type: Number, default: 0 },
})

const chartRef = ref(null)
let chart = null
let resizeObserver = null
let themeObserver = null

const isDark = () => typeof document !== 'undefined' && document.documentElement.classList.contains('dark')

const getOption = () => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'item',
    borderWidth: 0,
    backgroundColor: isDark() ? 'rgba(20,20,24,0.94)' : 'rgba(15,23,42,0.92)',
    textStyle: { color: '#f8fafc', fontSize: 12 },
    formatter: ({ name, value, percent }) => `${name}<br/>${value} 题 (${percent}%)`,
  },
  legend: {
    bottom: 0,
    left: 'center',
    itemWidth: 10,
    itemHeight: 10,
    icon: 'circle',
    textStyle: {
      color: isDark() ? '#94a3b8' : '#64748b',
      fontSize: 12,
      fontWeight: 600,
    },
    data: props.items.map(item => item.label),
  },
  graphic: [
    {
      type: 'text',
      left: 'center',
      top: '39%',
      style: {
        text: '错题总数',
        textAlign: 'center',
        fill: isDark() ? '#94a3b8' : '#94a3b8',
        fontSize: 12,
        fontWeight: 600,
      },
    },
    {
      type: 'text',
      left: 'center',
      top: '46%',
      style: {
        text: String(props.total || 0),
        textAlign: 'center',
        fill: isDark() ? '#f8fafc' : '#0f172a',
        fontSize: 30,
        fontWeight: 800,
      },
    },
    {
      type: 'text',
      left: 'center',
      top: '57%',
      style: {
        text: '题',
        textAlign: 'center',
        fill: isDark() ? '#94a3b8' : '#94a3b8',
        fontSize: 12,
        fontWeight: 600,
      },
    },
  ],
  series: [
    {
      type: 'pie',
      radius: ['54%', '74%'],
      center: ['50%', '42%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 6,
        borderColor: isDark() ? '#121214' : '#ffffff',
        borderWidth: 3,
      },
      label: {
        show: false,
      },
      emphasis: {
        scale: true,
        scaleSize: 6,
      },
      data: props.items.map(item => ({
        name: item.label,
        value: item.count,
        itemStyle: { color: item.color },
      })),
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

watch(() => [props.items, props.total], renderChart, { deep: true })

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
      <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400 dark:text-[#707783]">Distribution</p>
      <h3 class="text-base font-semibold text-slate-900 dark:text-white">错因分布</h3>
      <p class="mt-1 text-xs text-slate-500 dark:text-[#8a8f98]">按主要错误类型查看近期问题结构</p>
    </div>

    <div ref="chartRef" class="h-[360px] w-full flex-1"></div>
  </BaseCard>
</template>
