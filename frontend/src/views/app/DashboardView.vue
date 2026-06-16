<script setup>
/**
 * DashboardView.vue
 * 纯前端 mock 数据面板，不依赖后端接口。
 */
import { computed, nextTick, ref } from 'vue'
import ContentPanel from '@/components/features/app/layout/ContentPanel.vue'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import BaseSelect from '@/components/base/BaseSelect.vue'
import KnowledgeRadarCard from '@/components/features/app/dashboard/KnowledgeRadarCard.vue'
import ErrorDistributionCard from '@/components/features/app/dashboard/ErrorDistributionCard.vue'
import PriorityBarCard from '@/components/features/app/dashboard/PriorityBarCard.vue'
import LearningTrendCard from '@/components/features/app/dashboard/LearningTrendCard.vue'
import KnowledgeCompareCard from '@/components/features/app/dashboard/KnowledgeCompareCard.vue'
import SummaryStatsChartCard from '@/components/features/app/dashboard/SummaryStatsChartCard.vue'
import { useToast } from '@/composables/useToast.js'

const subjectOptions = ['数学', '物理']
const selectedSubject = ref('数学')
const { pushToast } = useToast()
const exportSheetRef = ref(null)
const isExporting = ref(false)

const MOCK_DASHBOARDS = {
  数学: {
    headline: 'AI越来越懂这个学生',
    subtitle: '持续积累错题、错因与知识点变化，生成个性化复习路径。',
    student: {
      name: '张同学',
      tag: '初二-数学',
      stage: '第二阶段',
      updatedAt: '2024-05-20',
      mastery: 78,
    },
    trend: [56, 60, 63, 62, 68, 71, 69, 74, 72, 78],
    radar: [
      { label: '有理数与运算', score: 85, average: 76 },
      { label: '方程与不等式', score: 70, average: 72 },
      { label: '函数初步', score: 65, average: 68 },
      { label: '几何图形', score: 75, average: 70 },
      { label: '数据与概率', score: 60, average: 66 },
      { label: '统计与图表', score: 80, average: 73 },
    ],
    errorTotal: 128,
    errorDistribution: [
      { label: '概念不清', count: 45, percent: 35, color: '#3b82f6', icon: 'fa-circle-question' },
      { label: '审题失误', count: 38, percent: 30, color: '#22c55e', icon: 'fa-file-pen' },
      { label: '计算错误', count: 26, percent: 20, color: '#f59e0b', icon: 'fa-calculator' },
      { label: '步骤缺失', count: 19, percent: 15, color: '#ef4444', icon: 'fa-list-check' },
    ],
    errorInsight: '概念理解是主要薄弱环节，建议加强基础概念学习与巩固。',
    priorities: [
      {
        title: '高频错题',
        value: 28,
        unit: '题',
        description: '近期反复出错的题目',
        tone: 'rose',
        icon: 'fa-fire',
      },
      {
        title: '薄弱知识点',
        value: 6,
        unit: '个',
        description: '掌握度低于 70% 的知识点',
        tone: 'amber',
        icon: 'fa-book-open',
      },
      {
        title: '订正未完成',
        value: 15,
        unit: '题',
        description: '未订正或订正不完整的题目',
        tone: 'blue',
        icon: 'fa-clipboard-check',
      },
    ],
    priorityTip: '建议优先复习高频错题，其次攻克薄弱知识点，并及时完成错题订正。',
    summaryStats: [
      { label: '累计错题', value: 128, unit: '题', tone: 'accent', icon: 'fa-layer-group' },
      { label: '待复习', value: 42, unit: '题', tone: 'blue', icon: 'fa-clock' },
      { label: '已掌握', value: 73, unit: '题', tone: 'emerald', icon: 'fa-circle-check' },
      { label: '本周提升', value: 12, unit: '%', tone: 'slate', icon: 'fa-bolt' },
    ],
    timeline: [
      { title: '第一次作业', description: '收集学习数据\n记录初始学情', tone: 'blue', icon: 'fa-pen-to-square' },
      { title: '阶段复习', description: '分析错因分布\n生成复习建议', tone: 'emerald', icon: 'fa-book-open-reader' },
      { title: '月度报告', description: '总结学习变化\n调整学习策略', tone: 'accent', icon: 'fa-chart-column' },
      { title: '能力变化', description: '追踪能力提升\n见证成长进步', tone: 'emerald', icon: 'fa-arrow-trend-up' },
    ],
  },
  物理: {
    headline: 'AI越来越懂这个学生',
    subtitle: '基于阶段作业、错因和知识点表现，生成可视化复习建议。',
    student: {
      name: '张同学',
      tag: '初二-物理',
      stage: '第一阶段',
      updatedAt: '2024-05-18',
      mastery: 72,
    },
    trend: [48, 52, 58, 57, 61, 64, 63, 67, 70, 72],
    radar: [
      { label: '力与运动', score: 82, average: 74 },
      { label: '压强浮力', score: 68, average: 70 },
      { label: '机械功', score: 64, average: 67 },
      { label: '光学', score: 76, average: 72 },
      { label: '电学基础', score: 58, average: 66 },
      { label: '实验探究', score: 73, average: 71 },
    ],
    errorTotal: 96,
    errorDistribution: [
      { label: '模型混淆', count: 31, percent: 32, color: '#3b82f6', icon: 'fa-circle-question' },
      { label: '审题失误', count: 24, percent: 25, color: '#22c55e', icon: 'fa-file-pen' },
      { label: '公式误用', count: 23, percent: 24, color: '#f59e0b', icon: 'fa-calculator' },
      { label: '步骤缺失', count: 18, percent: 19, color: '#ef4444', icon: 'fa-list-check' },
    ],
    errorInsight: '电学基础和公式迁移是当前主要卡点，建议多做同模型对比练习。',
    priorities: [
      {
        title: '高频错题',
        value: 21,
        unit: '题',
        description: '近期反复做错的受力分析题',
        tone: 'rose',
        icon: 'fa-fire',
      },
      {
        title: '薄弱知识点',
        value: 4,
        unit: '个',
        description: '电学与机械功仍需重点回看',
        tone: 'amber',
        icon: 'fa-book-open',
      },
      {
        title: '订正未完成',
        value: 9,
        unit: '题',
        description: '实验题订正记录不完整',
        tone: 'blue',
        icon: 'fa-clipboard-check',
      },
    ],
    priorityTip: '建议先完成电学专题复盘，再推进实验题订正与高频错题强化。',
    summaryStats: [
      { label: '累计错题', value: 96, unit: '题', tone: 'accent', icon: 'fa-layer-group' },
      { label: '待复习', value: 27, unit: '题', tone: 'blue', icon: 'fa-clock' },
      { label: '已掌握', value: 54, unit: '题', tone: 'emerald', icon: 'fa-circle-check' },
      { label: '本周提升', value: 8, unit: '%', tone: 'slate', icon: 'fa-bolt' },
    ],
    timeline: [
      { title: '第一次作业', description: '收集学情样本\n形成基础画像', tone: 'blue', icon: 'fa-pen-to-square' },
      { title: '阶段复习', description: '聚焦薄弱模块\n形成训练建议', tone: 'emerald', icon: 'fa-book-open-reader' },
      { title: '月度报告', description: '整理能力变化\n给出复习重点', tone: 'accent', icon: 'fa-chart-column' },
      { title: '能力变化', description: '跟踪掌握走势\n持续优化节奏', tone: 'emerald', icon: 'fa-arrow-trend-up' },
    ],
  },
}

const panelData = computed(() => MOCK_DASHBOARDS[selectedSubject.value] || MOCK_DASHBOARDS.数学)

const masteryProgress = computed(() => panelData.value.student.mastery)
const trendDelta = computed(() => {
  const series = panelData.value.trend
  return series[series.length - 1] - series[series.length - 2]
})

const trendPoints = computed(() => {
  const values = panelData.value.trend
  const width = 250
  const height = 64
  const max = Math.max(...values)
  const min = Math.min(...values)
  const range = Math.max(1, max - min)
  return values.map((value, index) => {
    const x = (index / (values.length - 1)) * width
    const y = height - (((value - min) / range) * (height - 10) + 5)
    return `${x},${y}`
  }).join(' ')
})

const waitForExportLayout = async () => {
  await nextTick()
  await nextTick()
  await new Promise(resolve => window.setTimeout(resolve, 600))
}

const handleExportPdf = async () => {
  if (isExporting.value) return

  try {
    isExporting.value = true
    await waitForExportLayout()

    if (!exportSheetRef.value) {
      throw new Error('PDF 导出区域尚未准备好')
    }

    const [{ default: html2canvas }, { jsPDF }] = await Promise.all([
      import('html2canvas'),
      import('jspdf'),
    ])

    const target = exportSheetRef.value
    const canvas = await html2canvas(target, {
      backgroundColor: '#ffffff',
      scale: 2,
      useCORS: true,
      width: target.scrollWidth,
      height: target.scrollHeight,
      windowWidth: target.scrollWidth,
      windowHeight: target.scrollHeight,
    })

    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
      compress: true,
    })

    pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, 210, 297, undefined, 'FAST')

    const fileName = `学习画像面板-${selectedSubject.value}-六图.pdf`
    pdf.save(fileName)
    pushToast('success', `已导出 ${fileName}`)
  } catch (error) {
    pushToast('error', error instanceof Error ? error.message : '导出 PDF 失败')
  } finally {
    isExporting.value = false
  }
}

</script>

<template>
  <ContentPanel title="学习画像面板">
    <template #toolbar>
      <BaseSelect
        v-model="selectedSubject"
        :options="subjectOptions"
        placeholder="选择学科"
        width-class="min-w-[140px]"
      />
      <BaseButton variant="primary" size="sm" :disabled="isExporting" @click="handleExportPdf">
        <i class="fa-regular fa-file-pdf"></i>
        {{ isExporting ? '导出中...' : '导出为 PDF' }}
      </BaseButton>
    </template>

    <div class="mx-auto flex w-full max-w-[1480px] flex-col gap-4 pb-4">
      <BaseCard rounded="rounded-lg" padding="p-6" class="overflow-hidden panel-shell">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div class="flex min-w-0 items-center gap-4">
              <div
                class="h-12 w-12 shrink-0 rounded-full relative overflow-hidden flex items-center justify-center text-white text-lg font-bold shadow-sm"
                style="background: linear-gradient(to bottom, rgb(var(--accent-rgb) / 0.9), rgb(var(--accent-strong-rgb) / 0.9)); box-shadow: inset 0 1px 0 0 rgba(255,255,255,0.12);"
              >
                <span class="absolute inset-0 pointer-events-none"
                  style="background-image: linear-gradient(to right, rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.06) 1px, transparent 1px); background-size: 8px 8px; mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%); -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);"></span>
                <span class="relative z-10">{{ panelData.student.name?.[0] || '?' }}</span>
              </div>
              <div class="min-w-0">
                <div class="flex flex-wrap items-center gap-3">
                  <h2 class="text-2xl font-black text-slate-900 dark:text-white">{{ panelData.student.name }}</h2>
                  <span class="rounded-full border border-[rgb(var(--accent-rgb)/0.20)] bg-[rgb(var(--accent-rgb)/0.10)] px-2.5 py-1 text-xs font-semibold text-[rgb(var(--accent-strong-rgb))] dark:text-[rgb(var(--accent-hover-rgb))]">
                    {{ panelData.student.tag }}
                  </span>
                </div>
                <div class="mt-2 flex flex-wrap gap-5 text-sm text-slate-500 dark:text-[#8a8f98]">
                  <span class="inline-flex items-center gap-2 rounded-full bg-slate-100/80 px-3 py-1 dark:bg-white/[0.04]">
                    <i class="fa-regular fa-compass"></i>
                    学习阶段：{{ panelData.student.stage }}
                  </span>
                  <span class="inline-flex items-center gap-2 rounded-full bg-slate-100/80 px-3 py-1 dark:bg-white/[0.04]">
                    <i class="fa-regular fa-clock"></i>
                    更新时间：{{ panelData.student.updatedAt }}
                  </span>
                </div>
              </div>
            </div>

            <div class="rounded-lg border border-slate-200/70 bg-white/80 px-4 py-3 dark:border-white/[0.08] dark:bg-white/[0.04]">
              <div class="flex items-center justify-between gap-4">
                <div>
                  <p class="text-xs font-medium text-slate-400 dark:text-[#707783]">综合掌握度</p>
                  <p class="mt-1 text-2xl font-bold text-slate-900 dark:text-white">
                    {{ masteryProgress }}/100
                  </p>
                </div>
                <div class="min-w-[250px]">
                  <svg viewBox="0 0 250 64" class="h-16 w-full">
                    <polyline
                      :points="trendPoints"
                      fill="none"
                      stroke="rgb(var(--accent-rgb))"
                      stroke-width="3.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                  <div class="mt-1 flex justify-end">
                    <span class="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-300">
                      <i class="fa-solid fa-arrow-trend-up"></i>
                      +{{ trendDelta }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
      </BaseCard>

      <div class="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <KnowledgeRadarCard :items="panelData.radar" />
        <ErrorDistributionCard :items="panelData.errorDistribution" :total="panelData.errorTotal" />
        <PriorityBarCard :items="panelData.priorities" />
        <LearningTrendCard :trend="panelData.trend" />
        <KnowledgeCompareCard :items="panelData.radar" />
        <SummaryStatsChartCard :items="panelData.summaryStats" />
      </div>

    </div>

    <div class="pdf-export-stage" aria-hidden="true">
      <div ref="exportSheetRef" class="pdf-export-sheet">
        <div class="pdf-export-head">
          <div>
            <p class="pdf-export-eyebrow">Learning Portrait</p>
            <h2 class="pdf-export-title">学习画像面板</h2>
          </div>
          <div class="pdf-export-meta">
            <span><span class="pdf-export-meta-text">{{ selectedSubject }}</span></span>
            <span><span class="pdf-export-meta-text">{{ panelData.student.name }}</span></span>
          </div>
        </div>

        <div class="pdf-export-grid">
          <KnowledgeRadarCard :items="panelData.radar" theme-mode="light" />
          <ErrorDistributionCard :items="panelData.errorDistribution" :total="panelData.errorTotal" theme-mode="light" />
          <PriorityBarCard :items="panelData.priorities" theme-mode="light" compact />
          <LearningTrendCard :trend="panelData.trend" theme-mode="light" />
          <KnowledgeCompareCard :items="panelData.radar" theme-mode="light" />
          <SummaryStatsChartCard :items="panelData.summaryStats" theme-mode="light" />
        </div>
      </div>
    </div>
  </ContentPanel>
</template>

<style scoped>
.panel-shell {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 250, 252, 0.88));
}

.dark .panel-shell {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.035));
}

.pdf-export-stage {
  position: fixed;
  left: -9999px;
  top: 0;
  pointer-events: none;
  opacity: 0;
}

.pdf-export-sheet {
  width: 210mm;
  height: 297mm;
  padding: 6mm 6mm 5mm;
  box-sizing: border-box;
  overflow: hidden;
  background: #ffffff;
  color: #0f172a;
}

.pdf-export-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 4mm;
}

.pdf-export-eyebrow {
  margin: 0;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #64748b;
}

.pdf-export-title {
  margin: 4px 0 0;
  font-size: 22px;
  line-height: 1.15;
  font-weight: 800;
  color: #0f172a;
}

.pdf-export-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.pdf-export-meta span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 20px;
  padding: 0;
  font-size: 12px;
  font-weight: 600;
  color: #334155;
}

.pdf-export-meta-text {
  display: block;
  line-height: 1;
  text-align: center;
  white-space: nowrap;
}

.pdf-export-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: repeat(3, minmax(0, 1fr));
  gap: 3mm;
  height: calc(100% - 23mm);
  align-items: stretch;
}

.pdf-export-grid :deep(.rounded-lg) {
  border-radius: 12px;
}

.pdf-export-grid :deep(.h-full) {
  height: 100% !important;
}

.pdf-export-grid :deep(.bg-white\/85),
.pdf-export-grid :deep(.dark\:bg-white\/\[0\.04\]) {
  background: #ffffff !important;
}

.pdf-export-grid :deep(.shadow-sm),
.pdf-export-grid :deep(.dark\:shadow-black\/20) {
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08) !important;
}

.pdf-export-grid :deep(.hover\:bg-white),
.pdf-export-grid :deep(.dark\:hover\:bg-white\/\[0\.065\]) {
  background: #ffffff !important;
}

.pdf-export-grid :deep(.h-\[360px\]) {
  height: 228px !important;
  min-height: 228px !important;
}

.pdf-export-grid :deep(.min-h-\[360px\]) {
  min-height: 228px !important;
}

.pdf-export-grid :deep(.p-5) {
  padding: 14px !important;
}

.pdf-export-grid :deep(.mb-5) {
  margin-bottom: 10px !important;
}

.pdf-export-grid :deep(h3) {
  font-size: 14px !important;
}

.pdf-export-grid :deep(.text-base) {
  font-size: 14px !important;
  line-height: 1.35 !important;
}

.pdf-export-grid :deep(.text-xs) {
  font-size: 10px !important;
  line-height: 1.4 !important;
}

.pdf-export-grid :deep(.text-\[11px\]) {
  font-size: 10px !important;
}

.pdf-export-grid :deep(.text-slate-900),
.pdf-export-grid :deep(.dark\:text-white) {
  color: #0f172a !important;
}

.pdf-export-grid :deep(.text-slate-500),
.pdf-export-grid :deep(.text-slate-400),
.pdf-export-grid :deep(.dark\:text-\[\#8a8f98\]),
.pdf-export-grid :deep(.dark\:text-\[\#707783\]) {
  color: #64748b !important;
}
</style>

