<script setup>
/**
 * HomeWorkflow.vue
 * 落地页工作流程展示
 */
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
  if (idx <= activeStep.value) {
    return 'wf-icon wf-icon--active w-12 h-12 rounded-xl flex items-center justify-center mb-4 text-white transition-all duration-500'
  }
  return 'w-12 h-12 rounded-xl flex items-center justify-center mb-4 bg-white/[0.04] text-white/25 border border-white/[0.06] transition-all duration-500'
}

function getStepContainerClass(idx) {
  if (idx === activeStep.value) {
    return 'relative p-4 rounded-lg cursor-pointer brand-btn transition-all duration-500 transform scale-105'
  }
  return 'relative p-4 rounded-lg cursor-pointer border border-transparent hover:bg-white/[0.03] hover:border-white/[0.05] transition-all duration-500'
}

function getStepTitleClass(idx) {
  if (idx === activeStep.value) return 'text-sm font-semibold mb-1 text-white/90'
  return 'text-sm font-semibold mb-1 text-white/40'
}

function getStepDescClass(idx) {
  if (idx === activeStep.value) return 'text-xs text-white/50'
  return 'text-xs text-white/25'
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
  <section id="workflow" class="relative z-10 py-24 overflow-hidden">
    <div class="reveal max-w-5xl mx-auto px-4 sm:px-6 relative z-10">
      <div class="text-center mb-16">
        <h2 class="reveal text-3xl font-semibold tracking-tight mb-4 text-transparent bg-clip-text animate-gradient-sweep" style="
            background-image: linear-gradient(to right, rgb(151, 137, 222) 0%, rgb(151, 137, 222) 20%, rgb(255, 255, 255) 50%, rgb(151, 137, 222) 80%, rgb(151, 137, 222) 100%);
            background-size: 200% auto;
          ">极简四步，自动运转</h2>
        <p class="text-white/40 text-sm">将原本需要耗费数小时的繁杂抄录，浓缩进点击之间。</p>
      </div>

      <div class="relative max-w-4xl mx-auto">
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-4 relative z-10">
          <div
            v-for="(s, i) in STEPS"
            :key="s.num"
            :class="getStepContainerClass(i)"
            :data-index="i"
            @click="onStepClick(i)"
          >
            <div class="flex flex-col items-center text-center">
              <div :class="getStepIconClass(i)" class="relative overflow-hidden">
                <span v-if="i <= activeStep" class="wf-icon__grid absolute inset-0 pointer-events-none"></span>
                <component :is="iconMap[s.icon]" class="relative w-5 h-5" />
              </div>
              <h4 :class="getStepTitleClass(i)">
                {{ s.title }}
              </h4>
              <p :class="getStepDescClass(i)">{{ s.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.wf-icon--active {
  background: linear-gradient(to bottom, rgba(129, 115, 223, 0.9), rgba(99, 87, 199, 0.9));
  box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.12);
}

.wf-icon__grid {
  background-image:
    linear-gradient(to right, rgba(255, 255, 255, 0.06) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-size: 8px 8px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
}
</style>
