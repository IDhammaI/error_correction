<script setup>
import { Camera, Cpu, Database, BrainCircuit, Sparkles, Layers } from 'lucide-vue-next'

const FEATURES = [
  { icon: 'camera',        title: '极速录入，告别手抄',       desc: '支持 PDF/多图并行处理。单文件最高 50MB，将几十页试卷秒变结构化数据，把时间留给思考。', delay: 0 },
  { icon: 'cpu',           title: '双引擎 OCR 极致精准',      desc: 'PaddleOCR + DeepSeek/文心一言 双重保障。自动纠错并完美还原复杂数学公式及变量下标。', delay: 80 },
  { icon: 'database',      title: '智能图谱与一键导出',       desc: 'AI 自动提取知识点标签。自由剔除无用题目，一键导出排版精美的 Markdown / PDF 错题本。', delay: 160 },
  { icon: 'brain-circuit', title: 'LangGraph Agent 拆题',    desc: '基于 LangGraph 的多步骤 Agent 流水线，智能识别题目边界、拆分子问题，精度超越单次 LLM 调用。', delay: 240 },
  { icon: 'sparkles',      title: 'LaTeX 公式无损还原',       desc: '深度理解数学符号语义，自动将手写或印刷公式转换为标准 LaTeX，支持分式、积分、矩阵等复杂结构。', delay: 320 },
  { icon: 'layers',        title: '多科目知识点打标',         desc: '覆盖数学、物理、化学、英语等主流学科。每道题自动关联知识点树，构建可视化个人薄弱点图谱。', delay: 400 },
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
  <section id="features" class="relative py-24 bg-[#0A0A0F]">
    <div class="mx-auto max-w-6xl px-4 sm:px-6">
      <div class="mb-12 text-center">
        <h2 class="reveal mb-4 text-2xl font-semibold text-white/90">驱动学习效率的核心引擎</h2>
        <p class="reveal mx-auto max-w-xl text-sm text-white/40">不仅是简单的图像识别，而是真正理解学科内在逻辑的 AI 智能体系统。</p>
      </div>
      <div class="grid gap-4 md:grid-cols-3">
        <div
          v-for="f in FEATURES"
          :key="f.title"
          class="reveal group rounded-lg p-6 transition-colors duration-200 border border-white/[0.06] bg-[#111118] hover:bg-white/[0.04]"
          :style="f.delay ? `transition-delay:${f.delay}ms` : ''"
        >
          <div class="mb-4 flex h-10 w-10 items-center justify-center rounded-lg border border-white/[0.06] bg-white/[0.04] text-white/60">
            <component :is="iconMap[f.icon]" class="h-5 w-5" />
          </div>
          <h3 class="mb-2 text-sm font-semibold text-white/90">{{ f.title }}</h3>
          <p class="text-xs leading-relaxed text-white/40">{{ f.desc }}</p>
        </div>
      </div>
    </div>
  </section>
</template>
