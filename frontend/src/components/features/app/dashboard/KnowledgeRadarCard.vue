<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { TooltipComponent, LegendComponent, RadarComponent } from 'echarts/components'
import { RadarChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'
import BaseCard from '@/components/base/BaseCard.vue'

echarts.use([TooltipComponent, LegendComponent, RadarComponent, RadarChart, CanvasRenderer])

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

const indicatorMax = computed(() => {
  const max = Math.max(100, ...props.items.flatMap(item => [item.score || 0, item.average || 0]))
  return Math.ceil(max / 10) * 10
})

const getOption = () => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'item',
    borderWidth: 0,
    backgroundColor: isDark() ? 'rgba(20,20,24,0.94)' : 'rgba(15,23,42,0.92)',
    textStyle: { color: '#f8fafc', fontSize: 12 },
  },
  legend: {
    bottom: 0,
    left: 'center',
    itemWidth: 12,
    itemHeight: 8,
    textStyle: {
      color: isDark() ? '#94a3b8' : '#64748b',
      fontSize: 12,
      fontWeight: 600,
    },
    data: ['掌握度', '班级平均'],
  },
  radar: {
    center: ['50%', '44%'],
    radius: '62%',
    splitNumber: 5,
    axisName: {
      color: isDark() ? '#cbd5e1' : '#475569',
      fontSize: 11,
      fontWeight: 600,
    },
    splitLine: {
      lineStyle: {
        color: isDark() ? 'rgba(148,163,184,0.14)' : 'rgba(148,163,184,0.24)',
      },
    },
    splitArea: {
      areaStyle: {
        color: isDark()
          ? ['rgba(255,255,255,0.015)', 'rgba(255,255,255,0.025)']
          : ['rgba(248,250,252,0.66)', 'rgba(255,255,255,0.88)'],
      },
    },
    axisLine: {
      lineStyle: {
        color: isDark() ? 'rgba(148,163,184,0.16)' : 'rgba(148,163,184,0.22)',
      },
    },
    indicator: props.items.map(item => ({
      name: item.label,
      max: indicatorMax.value,
    })),
  },
  series: [
    {
      type: 'radar',
      symbol: 'none',
      lineStyle: {
        width: 2,
        color: 'rgba(34,197,94,0.8)',
        type: 'dashed',
      },
      areaStyle: {
        color: 'rgba(34,197,94,0.08)',
      },
      data: [
        {
          value: props.items.map(item => item.average || 0),
          name: '班级平均',
        },
      ],
    },
    {
      type: 'radar',
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 2.5,
        color: '#2563eb',
      },
      itemStyle: {
        color: '#2563eb',
      },
      areaStyle: {
        color: 'rgba(59,130,246,0.14)',
      },
      data: [
        {
          value: props.items.map(item => item.score || 0),
          name: '掌握度',
        },
      ],
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
      <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400 dark:text-[#707783]">Knowledge</p>
      <h3 class="text-base font-semibold text-slate-900 dark:text-white">知识点掌握</h3>
      <p class="mt-1 text-xs text-slate-500 dark:text-[#8a8f98]">当前掌握度与班级平均对比</p>
    </div>

    <div ref="chartRef" class="h-[360px] w-full"></div>
  </BaseCard>
</template>
