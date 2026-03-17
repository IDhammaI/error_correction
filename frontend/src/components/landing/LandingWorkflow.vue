<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { UploadCloud, BrainCircuit, Sparkles, FileDown } from 'lucide-vue-next'

const STEPS = [
  { icon: 'upload-cloud', num: '01', title: '上传试卷',   desc: '支持PDF/多图并行处理',  delay: 0 },
  { icon: 'brain-circuit', num: '02', title: 'AI 解析拆题', desc: '智能排版与图文切分',    delay: 150 },
  { icon: 'sparkles',     num: '03', title: '纠错与打标', desc: '公式还原与知识点关联',   delay: 300 },
  { icon: 'file-down',    num: '04', title: '一键导出',   desc: '生成 Markdown/PDF',      delay: 450 },
]

const iconMap = {
  'upload-cloud': UploadCloud,
  'brain-circuit': BrainCircuit,
  sparkles: Sparkles,
  'file-down': FileDown,
}

const activeStep = ref(0)
let intervalId = null

function startStepInterval() {
  intervalId = setInterval(() => {
    activeStep.value = (activeStep.value + 1) % STEPS.length
  }, 3000)
}

function onStepClick(idx) {
  clearInterval(intervalId)
  activeStep.value = idx
  startStepInterval()
}

function getStepIconClass(idx) {
  if (idx === activeStep.value) {
    return 'step-icon w-16 h-16 rounded-xl flex items-center justify-center mb-6 relative bg-blue-600 text-white shadow-md shadow-blue-500/30 dark:bg-gradient-to-br dark:from-indigo-500 dark:to-indigo-600 dark:shadow-[0_0_20px_rgba(99,102,241,0.4)]'
  } else if (idx < activeStep.value) {
    return 'step-icon w-16 h-16 rounded-xl flex items-center justify-center mb-6 relative bg-blue-600 text-white shadow-md dark:bg-gradient-to-br dark:from-indigo-500 dark:to-indigo-600 dark:shadow-[0_0_20px_rgba(99,102,241,0.4)]'
  }
  return 'step-icon w-16 h-16 rounded-xl flex items-center justify-center mb-6 relative bg-slate-200 text-slate-500 border border-slate-200 dark:bg-white/5 dark:text-slate-500 dark:border-white/10'
}

function getStepContainerClass(idx) {
  if (idx === activeStep.value) {
    return 'workflow-step relative p-6 rounded-2xl cursor-pointer bg-white border border-blue-500 shadow-md scale-105 dark:bg-transparent dark:glass-panel dark:border-indigo-500/50 dark:shadow-[0_0_30px_rgba(99,102,241,0.15)]'
  }
  return 'workflow-step relative p-6 rounded-2xl cursor-pointer bg-transparent border border-transparent hover:bg-slate-100 dark:hover:bg-white/5'
}

function getStepTitleClass(idx) {
  if (idx === activeStep.value) return 'step-title text-xl font-bold mb-2 text-slate-900 dark:text-white'
  return 'step-title text-xl font-bold mb-2 text-slate-500 dark:text-slate-400'
}

function getStepDescClass(idx) {
  if (idx === activeStep.value) return 'step-desc text-sm text-blue-600 dark:text-indigo-200'
  return 'step-desc text-sm text-slate-500 dark:text-slate-500'
}

function getProgressWidth() {
  return `${(activeStep.value / (STEPS.length - 1)) * 100}%`
}

onMounted(() => {
  startStepInterval()
})

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

<template>
  <!-- 工作流演示区 -->
  <section id="workflow" class="relative z-10 min-h-screen flex flex-col justify-center py-24 overflow-hidden bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 dark:from-[#0A0A0F] dark:via-slate-950 dark:to-[#0A0A0F]">
    <!-- 装饰光晕 -->
    <div class="pointer-events-none absolute inset-0 z-0">
      <div class="absolute top-1/4 left-[-10%] w-[500px] h-[500px] rounded-full bg-indigo-600/10 blur-[140px]"></div>
      <div class="absolute bottom-1/4 right-[-10%] w-[400px] h-[400px] rounded-full bg-cyan-600/10 blur-[120px]"></div>
    </div>
    <div class="reveal relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-20">
        <h2 class="text-3xl md:text-4xl font-bold mb-6 text-white">极简四步，自动运转</h2>
        <p class="text-slate-400 text-base">将原本需要耗费数小时的繁杂抄录，浓缩进点击之间。</p>
      </div>

      <div class="relative max-w-5xl mx-auto">
        <div class="hidden lg:block absolute top-1/2 left-[10%] right-[10%] h-0.5 bg-white/8 -translate-y-1/2 z-0 rounded-full">
          <div
            id="progress-bar"
            class="absolute top-0 left-0 h-full bg-blue-500 dark:bg-gradient-to-r dark:from-cyan-500 dark:via-indigo-500 dark:to-indigo-500 shadow-blue-500/50 dark:shadow-indigo-500/50 transition-all duration-700 ease-in-out"
            :style="{ width: getProgressWidth() }"
          ></div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-4 gap-8 relative z-10">
          <div
            v-for="(s, i) in STEPS"
            :key="s.num"
            :class="getStepContainerClass(i)"
            :data-index="i"
            @click="onStepClick(i)"
          >
            <div class="flex flex-col items-center text-center">
              <div :class="getStepIconClass(i)">
                <div
                  class="step-ping absolute inset-0 rounded-2xl bg-indigo-400 animate-ping opacity-20"
                  :class="i === activeStep ? '' : 'hidden'"
                ></div>
                <component :is="iconMap[s.icon]" class="w-6 h-6" />
              </div>
              <h4 :class="getStepTitleClass(i)">
                <span class="text-blue-500 dark:text-indigo-500 mr-2 font-mono text-sm">{{ s.num }}</span> {{ s.title }}
              </h4>
              <p :class="getStepDescClass(i)">{{ s.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
