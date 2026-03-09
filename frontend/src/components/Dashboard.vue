<script setup>
import { ref, onMounted, onUpdated, watch, nextTick, onBeforeUnmount } from 'vue'

const props = defineProps({
  theme: { type: String, default: 'light' },
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['toggle-theme', 'go-workspace'])

// ================== 图表逻辑 ==================
const trendChartCanvas = ref(null)
const causeChartCanvas = ref(null)
let trendChartInstance = null
let causeChartInstance = null

const initOrUpdateCharts = async () => {
  await nextTick()
  if (!window.Chart || !trendChartCanvas.value || !causeChartCanvas.value) return

  const isDark = props.theme === 'dark'
  const textColor = isDark ? 'rgba(255, 255, 255, 0.6)' : 'rgba(15, 23, 42, 0.6)'
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(15, 23, 42, 0.05)'
  const tooltipBg = isDark ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.9)'
  const tooltipText = isDark ? '#fff' : '#0f172a'

  // 1. 趋势图
  if (trendChartInstance) trendChartInstance.destroy()
  trendChartInstance = new window.Chart(trendChartCanvas.value, {
    type: 'line',
    data: {
      labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
      datasets: [
        {
          label: '新增录入',
          data: [3, 5, 2, 8, 4, 12, 5],
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          borderWidth: 2,
          tension: 0.4,
          fill: true,
          pointBackgroundColor: '#ef4444'
        },
        {
          label: '复习掌握',
          data: [1, 2, 4, 3, 6, 8, 10],
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          borderWidth: 2,
          tension: 0.4,
          fill: true,
          pointBackgroundColor: '#10b981'
        }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: textColor, usePointStyle: true, boxWidth: 6 }, position: 'top' },
        tooltip: { backgroundColor: tooltipBg, titleColor: tooltipText, bodyColor: tooltipText, borderColor: gridColor, borderWidth: 1 }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: textColor } },
        y: { grid: { color: gridColor }, ticks: { color: textColor, stepSize: 4 } }
      }
    }
  })

  // 2. 环形图
  if (causeChartInstance) causeChartInstance.destroy()
  causeChartInstance = new window.Chart(causeChartCanvas.value, {
    type: 'doughnut',
    data: {
      labels: ['概念不清', '粗心计算', '公式混淆', '未知错因'],
      datasets: [{
        data: [45, 25, 20, 10],
        backgroundColor: ['#6366f1', '#f59e0b', '#ec4899', isDark ? '#334155' : '#cbd5e1'],
        borderWidth: 0,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '75%',
      plugins: {
        legend: { position: 'right', labels: { color: textColor, usePointStyle: true, boxWidth: 8 } },
        tooltip: { backgroundColor: tooltipBg, titleColor: tooltipText, bodyColor: tooltipText, borderColor: gridColor, borderWidth: 1 }
      }
    }
  })
}

watch(() => props.theme, initOrUpdateCharts)
watch(() => props.visible, (val) => {
  if (val) {
    nextTick(() => {
      initOrUpdateCharts()
      if (window.lucide) window.lucide.createIcons()
    })
  }
})

// ================== AI 分析弹窗与打字机动画逻辑 ==================
const aiModalOpen = ref(false)
const aiLoading = ref(false)
const aiResultVisible = ref(false)

const typedText1 = ref('')
const typedText3 = ref('')
const showCursor1 = ref(false)
const showCursor3 = ref(false)
const stepVisibility = ref([false, false, false])

let typingTimeout = null

const fullText1 = "你错误地将周期的公式混淆了。正弦函数的周期公式是 T = 2π/ω，而不是 π/ω。你可能因为题目给了最小正周期为 π，直接导致计算时漏掉了系数 2。"
const fullText3 = "建议复习《三角函数图像与性质》章节，重点巩固 T=2π/ω 的推导过程。我已经为你生成了 3 道只变动系数的同类题，点击下方按钮可以开始挑战。"

const typeString = (fullStr, targetRef, cursorRef, callback) => {
  let i = 0
  cursorRef.value = true
  const typeChar = () => {
    if (i < fullStr.length) {
      targetRef.value += fullStr.charAt(i)
      i++
      typingTimeout = setTimeout(typeChar, 25)
    } else {
      cursorRef.value = false
      if (callback) callback()
    }
  }
  typeChar()
}

const openAiAnalysisModal = () => {
  // 重置状态
  aiLoading.value = true
  aiResultVisible.value = false
  typedText1.value = ''
  typedText3.value = ''
  stepVisibility.value = [false, false, false]
  aiModalOpen.value = true

  // 模拟加载 1.5s
  setTimeout(() => {
    aiLoading.value = false
    aiResultVisible.value = true
    
    // 启动顺序动画
    typeString(fullText1, typedText1, showCursor1, () => {
      // 逐个显示步骤
      stepVisibility.value.forEach((_, idx) => {
        setTimeout(() => { stepVisibility.value[idx] = true }, idx * 400)
      })
      // 步骤显示完后显示总结
      setTimeout(() => {
        typeString(fullText3, typedText3, showCursor3, null)
      }, stepVisibility.value.length * 400 + 200)
    })
  }, 1500)
}

const closeAiAnalysisModal = () => {
  clearTimeout(typingTimeout)
  aiModalOpen.value = false
}

// 刷新 Lucide 图标和 MathJax
onMounted(() => {
  if (window.lucide) window.lucide.createIcons()
  initOrUpdateCharts()
  if (window.MathJax) window.MathJax.typesetPromise()
})
onUpdated(() => {
  if (window.lucide) window.lucide.createIcons()
})
onBeforeUnmount(() => {
  clearTimeout(typingTimeout)
  if (trendChartInstance) trendChartInstance.destroy()
  if (causeChartInstance) causeChartInstance.destroy()
})
</script>

<template>
  <div class="relative min-h-screen text-slate-900 transition-colors duration-500 dark:text-slate-300">
    <!-- 动态背景环境光 (组件内隔离) -->
    <div class="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      <div class="absolute -right-[10%] top-[-10%] h-[50vw] w-[50vw] rounded-full bg-blue-300/20 mix-blend-multiply blur-[120px] transition-colors duration-1000 dark:bg-indigo-600/10 dark:mix-blend-screen"></div>
      <div class="absolute -left-[10%] bottom-[-10%] h-[40vw] w-[40vw] rounded-full bg-cyan-200/30 mix-blend-multiply blur-[100px] transition-colors duration-1000 dark:bg-fuchsia-600/10 dark:mix-blend-screen"></div>
    </div>

    <!-- 导航栏 -->
    <nav class="glass-panel fixed top-0 z-40 w-full transition-all duration-300">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="flex h-16 items-center justify-between">
          <div class="flex items-center gap-6">
            <!-- 返回官网 -->
            <a href="index.html" class="flex items-center gap-3 transition-opacity hover:opacity-80">
              <div class="rounded-lg bg-blue-600 p-2 dark:bg-gradient-to-br dark:from-indigo-500 dark:to-purple-600">
                <i data-lucide="book-open" class="h-5 w-5 text-white"></i>
              </div>
              <span class="tracking-wide text-xl font-bold text-slate-800 dark:text-slate-200">我的题库</span>
            </a>
            <div class="hidden items-center rounded-full border border-slate-300/50 bg-slate-200/50 px-4 py-1.5 md:flex dark:border-white/10 dark:bg-white/5">
              <i data-lucide="search" class="mr-2 h-4 w-4 text-slate-400"></i>
              <input type="text" placeholder="搜索知识点、题型..." class="w-48 border-none bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400 dark:text-slate-300 dark:placeholder:text-slate-500">
            </div>
          </div>
          <div class="flex items-center gap-4">
            <!-- 昼夜切换 -->
            <button @click="(e) => emit('toggle-theme', e.currentTarget)" class="rounded-full p-2 text-slate-500 transition-colors hover:bg-slate-200 dark:text-slate-400 dark:hover:bg-white/10">
              <i data-lucide="sun" class="h-5 w-5" :class="theme === 'dark' ? 'hidden' : 'block'"></i>
              <i data-lucide="moon" class="h-5 w-5" :class="theme === 'dark' ? 'block' : 'hidden'"></i>
            </button>
            <div class="h-8 w-8 cursor-pointer rounded-full border-2 border-white bg-gradient-to-r from-cyan-500 to-blue-500 shadow-sm dark:border-slate-800"></div>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主要内容区 -->
    <main class="relative z-10 mx-auto flex max-w-7xl gap-8 px-4 pb-12 pt-24 sm:px-6 lg:px-8">
      
      <!-- 左侧边栏 -->
      <aside class="hidden w-64 shrink-0 space-y-8 lg:block">
        <div>
          <!-- 切换回工作台的按钮 -->
          <button @click="emit('go-workspace')" class="group relative mb-6 inline-flex h-12 w-full">
            <div class="absolute -inset-px rounded-xl bg-gradient-to-r from-blue-500 to-indigo-500 opacity-0 blur-md transition-all duration-500 group-hover:opacity-100 dark:opacity-50"></div>
            <span class="relative flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 font-bold text-white shadow-md transition-colors hover:bg-blue-700 dark:border dark:border-indigo-500/30 dark:bg-slate-900 dark:text-indigo-300 dark:shadow-none dark:hover:bg-slate-800">
              <i data-lucide="plus" class="h-5 w-5"></i> 录入新错题
            </span>
          </button>
          
          <h3 class="mb-4 px-2 text-xs font-bold uppercase tracking-wider text-slate-400">学科筛选</h3>
          <ul class="space-y-1">
            <li><a href="#" class="flex items-center justify-between rounded-lg bg-blue-50 px-3 py-2 font-medium text-blue-700 dark:bg-white/10 dark:text-white"><span class="flex items-center gap-2"><i data-lucide="function-square" class="h-4 w-4"></i> 数学</span> <span class="rounded-full bg-blue-200 px-2 py-0.5 text-xs text-blue-800 dark:bg-white/20 dark:text-slate-300">128</span></a></li>
            <li><a href="#" class="flex items-center justify-between rounded-lg px-3 py-2 text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/5"><span class="flex items-center gap-2"><i data-lucide="atom" class="h-4 w-4"></i> 物理</span> <span class="rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-600 dark:bg-white/5 dark:text-slate-500">45</span></a></li>
            <li><a href="#" class="flex items-center justify-between rounded-lg px-3 py-2 text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/5"><span class="flex items-center gap-2"><i data-lucide="flask-conical" class="h-4 w-4"></i> 化学</span> <span class="rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-600 dark:bg-white/5 dark:text-slate-500">32</span></a></li>
          </ul>
        </div>
        
        <div>
          <h3 class="mb-4 px-2 text-xs font-bold uppercase tracking-wider text-slate-400">智能标签</h3>
          <div class="flex flex-wrap gap-2 px-2">
            <span class="cursor-pointer rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600 transition-colors hover:border-blue-400 dark:border-white/10 dark:bg-white/5 dark:text-slate-300">解析几何</span>
            <span class="cursor-pointer rounded-full border border-blue-300 bg-blue-50 px-3 py-1 text-xs text-blue-700 transition-colors dark:border-indigo-500/50 dark:bg-indigo-500/10 dark:text-indigo-300">三角函数</span>
            <span class="cursor-pointer rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600 transition-colors hover:border-blue-400 dark:border-white/10 dark:bg-white/5 dark:text-slate-300">粗心计算</span>
          </div>
        </div>
      </aside>

      <!-- 右侧：核心数据与列表区 -->
      <div class="flex-1 space-y-6">
        
        <!-- 数据看板（示例数据） -->
        <div class="mb-2 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-400">
          <i data-lucide="info" class="h-3.5 w-3.5"></i>
          以下为示例数据，真实数据功能即将上线（Coming Soon）
        </div>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div class="glass-panel rounded-2xl border border-slate-200 p-5 dark:border-white/5">
            <div class="mb-1 flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">待复习错题 <i data-lucide="clock-4" class="h-4 w-4 text-orange-500"></i></div>
            <div class="text-3xl font-bold text-slate-800 dark:text-white">12 <span class="ml-1 text-sm font-normal text-slate-400">道</span></div>
          </div>
          <div class="glass-panel rounded-2xl border border-slate-200 p-5 dark:border-white/5">
            <div class="mb-1 flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">本周新增 <i data-lucide="trending-up" class="h-4 w-4 text-blue-500"></i></div>
            <div class="text-3xl font-bold text-slate-800 dark:text-white">+8 <span class="ml-1 text-sm font-normal text-slate-400">道</span></div>
          </div>
          <div class="glass-panel rounded-2xl border border-slate-200 p-5 dark:border-white/5">
            <div class="mb-1 flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">已掌握移除 <i data-lucide="check-circle-2" class="h-4 w-4 text-emerald-500"></i></div>
            <div class="text-3xl font-bold text-slate-800 dark:text-white">45 <span class="ml-1 text-sm font-normal text-slate-400">道</span></div>
          </div>
        </div>

        <div class="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div class="glass-panel rounded-2xl border border-slate-200 p-5 lg:col-span-2 dark:border-white/5">
            <div class="mb-4 flex items-center justify-between">
              <h3 class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300"><i data-lucide="activity" class="h-4 w-4 text-indigo-500"></i> 错题攻克趋势</h3>
            </div>
            <div class="relative w-full h-[220px]"><canvas ref="trendChartCanvas"></canvas></div>
          </div>
          <div class="glass-panel rounded-2xl border border-slate-200 p-5 dark:border-white/5">
            <div class="mb-4 flex items-center justify-between">
              <h3 class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300"><i data-lucide="pie-chart" class="h-4 w-4 text-fuchsia-500"></i> 核心错因分布</h3>
            </div>
            <div class="relative flex w-full justify-center h-[220px]"><canvas ref="causeChartCanvas"></canvas></div>
          </div>
        </div>

        <!-- 详细列表 -->
        <div class="mt-8 flex items-center justify-between border-b border-slate-200 pb-4 dark:border-white/10">
          <h2 class="text-xl font-bold text-slate-800 dark:text-slate-200">详细错题记录</h2>
          <div class="flex gap-2">
            <button class="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-600 transition-colors hover:bg-slate-50 dark:border-white/10 dark:bg-[#0A0A0F] dark:text-slate-300 dark:hover:bg-white/5">
              <i data-lucide="download" class="h-4 w-4"></i> 导出重练卷
            </button>
          </div>
        </div>

        <!-- 卡片 1 -->
        <div class="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:shadow-md dark:border-white/10 dark:bg-[#0A0A0F] dark:hover:border-indigo-500/50">
          <div class="mb-4 flex items-start justify-between">
            <div class="flex gap-2">
              <span class="rounded border border-blue-200 bg-blue-100 px-2.5 py-1 text-xs font-semibold text-blue-700 dark:border-blue-500/20 dark:bg-blue-500/10 dark:text-blue-400">数学</span>
              <span class="rounded border border-indigo-200 bg-indigo-100 px-2.5 py-1 text-xs font-semibold text-indigo-700 dark:border-indigo-500/20 dark:bg-indigo-500/10 dark:text-indigo-400">三角函数</span>
            </div>
            <span class="flex items-center gap-1 text-xs text-slate-400"><i data-lucide="clock" class="h-3 w-3"></i> 2024-03-24</span>
          </div>
          
          <div class="prose max-w-none mb-6 dark:prose-invert">
            <p class="font-medium text-slate-800 dark:text-slate-200">12. 已知函数 $f(x) = \sin(\omega x + \frac{\pi}{6}) (\omega > 0)$ 的最小正周期为 $\pi$，则 $f(\frac{\pi}{4}) =$</p>
            <div class="mt-2 space-y-1 pl-4 text-slate-600 dark:text-slate-400">
              <p>A. $\frac{1}{2}$ &nbsp;&nbsp;&nbsp; B. $\frac{\sqrt{3}}{2}$ &nbsp;&nbsp;&nbsp; C. $-\frac{1}{2}$ &nbsp;&nbsp;&nbsp; D. $-\frac{\sqrt{3}}{2}$</p>
            </div>
          </div>

          <div class="mb-6 flex gap-4 rounded-lg border border-red-100 bg-red-50 p-3 dark:border-red-500/10 dark:bg-red-500/5">
            <div class="flex-1">
              <span class="mb-1 block text-xs font-bold uppercase text-red-500">我的作答</span>
              <p class="text-sm text-slate-700 dark:text-slate-300">选 A，代入公式算错了符号。</p>
            </div>
            <div class="flex-1 border-l border-red-200 pl-4 dark:border-red-500/20">
              <span class="mb-1 block text-xs font-bold uppercase text-emerald-500">标准答案</span>
              <p class="text-sm text-slate-700 dark:text-slate-300">选 B</p>
            </div>
          </div>

          <div class="flex items-center justify-between border-t border-slate-100 pt-4 dark:border-white/5">
            <button class="tooltip text-slate-500 transition-colors hover:text-red-500" title="标为未掌握"><i data-lucide="flag" class="h-5 w-5"></i></button>
            <button @click="openAiAnalysisModal" class="flex transform items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 px-5 py-2 text-sm font-bold text-white shadow-md shadow-indigo-500/25 transition-all hover:from-indigo-600 hover:to-purple-700 active:scale-95">
              <i data-lucide="sparkles" class="h-4 w-4"></i> AI 深度错因分析
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- AI 分析弹窗 -->
    <Teleport to="body">
      <div v-if="aiModalOpen" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity dark:bg-black/60" @click="closeAiAnalysisModal"></div>
        <div class="relative flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl transition-all dark:border-indigo-500/30 dark:bg-[#0F111A]">
          <!-- 头部 -->
          <div class="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-6 py-4 dark:border-white/5 dark:bg-[#0A0A0F]">
            <div class="flex items-center gap-2">
              <div class="rounded-md bg-indigo-500 p-1.5"><i data-lucide="brain-circuit" class="h-4 w-4 text-white"></i></div>
              <h3 class="font-bold text-slate-800 dark:text-slate-200">AI 智能分析报告</h3>
            </div>
            <button @click="closeAiAnalysisModal" class="text-slate-400 transition-colors hover:text-slate-600 dark:hover:text-white"><i data-lucide="x" class="h-5 w-5"></i></button>
          </div>
          
          <div class="flex-1 overflow-y-auto p-6 text-sm text-slate-700 space-y-6 dark:text-slate-300">
            <!-- Loading -->
            <div v-if="aiLoading" class="flex flex-col items-center justify-center py-12">
              <div class="relative mb-4 h-16 w-16">
                <div class="absolute inset-0 rounded-full border-4 border-indigo-500/20"></div>
                <div class="absolute inset-0 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
                <i data-lucide="sparkles" class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 transform text-indigo-500 h-6 w-6"></i>
              </div>
              <p class="animate-pulse font-mono text-indigo-600 dark:text-indigo-400">DeepSeek Agent 正在解析解题逻辑...</p>
            </div>
            
            <!-- Result -->
            <div v-if="aiResultVisible" class="space-y-6">
              <div class="rounded-xl border border-red-100 bg-red-50 p-4 dark:border-red-500/20 dark:bg-red-500/5">
                <h4 class="mb-2 flex items-center gap-2 font-bold text-red-600 dark:text-red-400"><i data-lucide="target" class="h-4 w-4"></i> 核心错因诊断</h4>
                <p class="leading-relaxed">
                  {{ typedText1 }}<span v-if="showCursor1" class="text-indigo-500 animate-pulse">▋</span>
                </p>
              </div>
              <div>
                <h4 class="mb-3 flex items-center gap-2 font-bold text-slate-800 dark:text-white"><i data-lucide="list-checks" class="h-4 w-4 text-indigo-500"></i> 正确解题路径</h4>
                <div class="space-y-3 border-l-2 border-indigo-500/30 pl-4">
                  <div v-if="stepVisibility[0]" class="transition-all duration-500"><span class="mr-2 rounded bg-indigo-100 px-1.5 text-xs text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-400">Step 1</span>由周期公式 $T = \frac{2\pi}{\omega}$ 且 $T = \pi$。</div>
                  <div v-if="stepVisibility[1]" class="mt-2 transition-all duration-500"><span class="mr-2 rounded bg-indigo-100 px-1.5 text-xs text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-400">Step 2</span>解得 $\omega = 2$。函数为 $f(x) = \sin(2x + \frac{\pi}{6})$。</div>
                  <div v-if="stepVisibility[2]" class="mt-2 transition-all duration-500"><span class="mr-2 rounded bg-indigo-100 px-1.5 text-xs text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-400">Step 3</span>将 $x = \frac{\pi}{4}$ 代入得 $f(\frac{\pi}{4}) = \frac{\sqrt{3}}{2}$。</div>
                </div>
              </div>
              <div class="rounded-xl border border-indigo-100 bg-indigo-50 p-4 dark:border-indigo-500/20 dark:bg-indigo-500/5">
                <h4 class="mb-2 flex items-center gap-2 font-bold text-indigo-700 dark:text-indigo-300"><i data-lucide="lightbulb" class="h-4 w-4"></i> 举一反三建议</h4>
                <p class="leading-relaxed">
                  {{ typedText3 }}<span v-if="showCursor3" class="text-indigo-500 animate-pulse">▋</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.glass-panel {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
.dark .glass-panel {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: none;
}
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
.dark ::-webkit-scrollbar-thumb { background: #334155; }
</style>