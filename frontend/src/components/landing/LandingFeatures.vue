<script setup>
import { Camera, Cpu, Database, BrainCircuit, Sparkles, Layers } from 'lucide-vue-next'

const FEATURES = [
  {
    icon: 'camera',
    topLine: 'via-cyan-400/50',
    title: '极速录入，告别手抄',
    desc: '支持 PDF/多图并行处理。单文件最高 50MB，将几十页试卷秒变结构化数据，把时间留给思考。',
    delay: 0,
  },
  {
    icon: 'cpu',
    topLine: 'via-indigo-400/50',
    title: '双引擎 OCR 极致精准',
    desc: 'PaddleOCR + DeepSeek/文心一言 双重保障。自动纠错并完美还原复杂数学公式及变量下标。',
    delay: 80,
  },
  {
    icon: 'database',
    topLine: 'via-violet-400/50',
    title: '智能图谱与一键导出',
    desc: 'AI 自动提取知识点标签。自由剔除无用题目，一键导出排版精美的 Markdown / PDF 错题本。',
    delay: 160,
  },
  {
    icon: 'brain-circuit',
    topLine: 'via-emerald-400/50',
    title: 'LangGraph Agent 拆题',
    desc: '基于 LangGraph 的多步骤 Agent 流水线，智能识别题目边界、拆分子问题，精度超越单次 LLM 调用。',
    delay: 240,
  },
  {
    icon: 'sparkles',
    topLine: 'via-rose-400/50',
    title: 'LaTeX 公式无损还原',
    desc: '深度理解数学符号语义，自动将手写或印刷公式转换为标准 LaTeX，支持分式、积分、矩阵等复杂结构。',
    delay: 320,
  },
  {
    icon: 'layers',
    topLine: 'via-blue-300/50',
    title: '多科目知识点打标',
    desc: '覆盖数学、物理、化学、英语等主流学科。每道题自动关联知识点树，构建可视化个人薄弱点图谱。',
    delay: 400,
  },
]

const iconMap = {
  camera: Camera,
  cpu: Cpu,
  database: Database,
  'brain-circuit': BrainCircuit,
  sparkles: Sparkles,
  layers: Layers,
}
</script>

<template>
  <!-- 核心功能区 -->
  <section id="features" class="relative overflow-hidden min-h-screen flex flex-col justify-center py-24 rounded-t-3xl bg-gradient-to-br from-blue-600 via-indigo-600 to-indigo-700 dark:from-indigo-950 dark:via-[#0A0A0F] dark:to-slate-950 shadow-[0_-12px_60px_rgba(0,0,0,0.35)]">
    <!-- 装饰光晕 -->
    <div class="pointer-events-none absolute inset-0 z-0">
      <div class="absolute top-[-15%] left-[-8%] h-[500px] w-[500px] rounded-full bg-blue-400/20 dark:bg-indigo-500/10 blur-[130px]"></div>
      <div class="absolute bottom-[-10%] right-[-5%] h-[400px] w-[400px] rounded-full bg-indigo-300/20 dark:bg-blue-600/10 blur-[100px]"></div>
      <div class="absolute inset-0 opacity-[0.04]" style="background-image: linear-gradient(rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.6) 1px, transparent 1px); background-size: 40px 40px;"></div>
    </div>

    <div class="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="mb-12 text-center">
        <h2 class="reveal mb-6 text-3xl font-bold text-white">驱动学习效率的 <span class="text-blue-200 dark:text-indigo-300">核心引擎</span></h2>
        <p class="reveal mx-auto max-w-2xl text-base text-blue-100/80 dark:text-slate-400">不仅是简单的图像识别，而是真正理解学科内在逻辑的 AI 智能体系统。</p>
      </div>
      <div class="grid gap-6 md:grid-cols-3">
        <div
          v-for="f in FEATURES"
          :key="f.title"
          class="reveal group relative overflow-hidden rounded-3xl border border-white/15 bg-white/10 backdrop-blur-md p-8 hover:-translate-y-2 hover:bg-white/15 hover:border-white/25 transition-all duration-300"
          :style="f.delay ? `transition-delay:${f.delay}ms` : ''"
        >
          <div :class="`absolute inset-x-0 -top-px mx-auto h-px w-1/2 bg-gradient-to-r from-transparent ${f.topLine} to-transparent opacity-60 group-hover:opacity-100 transition-opacity duration-300`"></div>
          <div class="relative z-10">
            <div class="mb-6 flex h-14 w-14 items-center justify-center rounded-xl border border-white/20 bg-white/15 text-white shadow-sm group-hover:scale-110 transition-transform duration-300">
              <component :is="iconMap[f.icon]" class="h-7 w-7" />
            </div>
            <h3 class="mb-4 text-xl font-bold text-white">{{ f.title }}</h3>
            <p class="text-sm leading-relaxed text-blue-100/80 dark:text-slate-300">{{ f.desc }}</p>
          </div>
        </div>
      </div>
    </div>
    <!-- 底部过渡遮罩 -->
    <div class="pointer-events-none absolute inset-x-0 bottom-0 h-32 z-10 bg-gradient-to-t from-slate-50 to-transparent dark:from-[#0A0A0F] dark:to-transparent"></div>
  </section>
</template>
