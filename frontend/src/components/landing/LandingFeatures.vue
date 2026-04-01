<script setup>
import { Camera, Cpu, Database, BrainCircuit, Sparkles, Layers } from 'lucide-vue-next'

const FEATURES = [
  {
    icon: Camera,
    title: '极速录入，告别手抄',
    desc: '支持 PDF / 多图并行处理，单文件最高 50 MB，将几十页试卷秒变结构化数据。',
    span: '', // 普通 1×1
  },
  {
    icon: Cpu,
    title: '双引擎 OCR 极致精准',
    desc: 'PaddleOCR + DeepSeek / 文心一言双重保障，自动纠错并完美还原复杂数学公式及变量下标。',
    span: 'md:col-span-2', // 宽卡片
  },
  {
    icon: BrainCircuit,
    title: 'LangGraph Agent 拆题',
    desc: '基于 LangGraph 的多步骤 Agent 流水线，智能识别题目边界、拆分子问题，精度超越单次 LLM 调用。',
    span: 'md:col-span-2', // 宽卡片
  },
  {
    icon: Sparkles,
    title: 'LaTeX 公式无损还原',
    desc: '深度理解数学符号语义，自动将手写或印刷公式转换为标准 LaTeX，支持分式、积分、矩阵等复杂结构。',
    span: '',
  },
  {
    icon: Database,
    title: '智能图谱与一键导出',
    desc: 'AI 自动提取知识点标签，自由剔除无用题目，一键导出排版精美的 Markdown / PDF 错题本。',
    span: '',
  },
  {
    icon: Layers,
    title: '多科目知识点打标',
    desc: '覆盖数学、物理、化学、英语等主流学科，每道题自动关联知识点树，构建个人薄弱点图谱。',
    span: '',
  },
]
</script>

<template>
  <section id="features" class="relative py-24 bg-[#0A0A0F] overflow-hidden">

    <!-- 顶部分割线 -->
    <div class="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/[0.06] to-transparent"></div>

    <div class="relative mx-auto max-w-6xl px-4 sm:px-6">

      <!-- 标题区 -->
      <div class="mb-16 text-center">
        <div class="reveal mb-4 inline-flex items-center gap-2 rounded-full border border-white/[0.06] bg-white/[0.02] px-3 py-1 text-xs font-medium text-white/40">
          核心功能
        </div>
        <h2 class="reveal text-3xl font-semibold tracking-tight text-white/90 mb-4">
          驱动学习效率的核心引擎
        </h2>
        <p class="reveal mx-auto max-w-xl text-sm text-white/35 leading-relaxed">
          不仅是简单的图像识别，而是真正理解学科内在逻辑的 AI 智能体系统。
        </p>
      </div>

      <!-- Bento Grid -->
      <div class="grid gap-3 md:grid-cols-3">
        <div
          v-for="(f, i) in FEATURES"
          :key="f.title"
          class="reveal feature-card group relative rounded-xl p-6 border border-white/[0.06] bg-white/[0.02] transition-all duration-300"
          :class="f.span"
          :style="{ transitionDelay: `${i * 80}ms` }"
        >
          <!-- Hover 光晕 -->
          <div class="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
            style="background: radial-gradient(circle at 50% 0%, rgba(129, 115, 223, 0.06) 0%, transparent 70%);"
          ></div>

          <!-- 内容 -->
          <div class="relative z-10">
            <div class="mb-4 flex h-10 w-10 items-center justify-center rounded-lg border border-white/[0.06] bg-white/[0.03] text-white/50 group-hover:text-indigo-400 group-hover:border-indigo-500/20 transition-colors duration-300">
              <component :is="f.icon" class="h-5 w-5" />
            </div>
            <h3 class="mb-2 text-sm font-semibold text-white/80 group-hover:text-white/95 transition-colors duration-300">{{ f.title }}</h3>
            <p class="text-xs leading-relaxed text-white/35">{{ f.desc }}</p>
          </div>
        </div>
      </div>

    </div>
  </section>
</template>

<style scoped>
.feature-card:hover {
  border-color: rgba(129, 115, 223, 0.15);
  background: rgba(255, 255, 255, 0.03);
}
</style>
