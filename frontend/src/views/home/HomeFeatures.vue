<script setup>
/**
 * HomeFeatures.vue
 * 落地页功能特性展示
 */
import { onMounted, ref } from 'vue'
import { Camera, Cpu, Database, BrainCircuit, Sparkles, Layers } from 'lucide-vue-next'
import FeatureCard from '@/components/home/FeatureCard.vue'

const FEATURES = [
  {
    icon: Camera,
    title: '极速录入，告别手抄',
    desc: '支持 PDF / 多图并行处理，单文件最高 50 MB，将几十页试卷秒变结构化数据。',
    span: '', // 普通 1×1
  },
  {
    icon: Cpu,
    title: '超强公式还原引擎',
    desc: '基于大模型微调，精准识别手写与印刷体混合的复杂 LaTeX 公式和几何图形。',
    span: '', // 普通 1×1
  },
  {
    icon: Database,
    title: 'AI 自动题型分类',
    desc: '自动判断选择题、填空题、解答题，并剥离答案，生成干净的专属题库。',
    span: '', // 普通 1×1
  },
  {
    icon: BrainCircuit,
    title: '错因深度分析',
    desc: '不是简单的“粗心”，AI 将分析你的每一步计算，指出你的逻辑漏洞与思维盲区。',
    span: 'md:col-span-2 lg:col-span-1', // 中屏占2列，大屏恢复1列
  },
  {
    icon: Sparkles,
    title: '同类题智能推演',
    desc: '掌握一道题，解决一类题。系统会自动生成变式训练，确保知识点真正被消化。',
    span: 'md:col-span-2', // 中屏及以上占2列
  },
  {
    icon: Layers,
    title: '多科目知识点打标',
    desc: '覆盖数学、物理、化学、英语等主流学科，每道题自动关联知识点树，构建个人薄弱点图谱。',
    span: '',
  },
]

// ── 鼠标跟随光晕逻辑 (仅限卡片局部光晕) ──

</script>

<template>
  <section id="features"
    class="relative py-24 overflow-hidden bg-slate-50 dark:bg-transparent transition-colors duration-200">

    <!-- 背景装饰：复杂流体拓扑波纹 (Fluid Topography) -->
    <div class="absolute inset-0 pointer-events-none z-0 opacity-[0.8] dark:opacity-20 dark:invert-0 invert" style="
      background-image: url('data:image/svg+xml,%3Csvg viewBox=%220 0 1000 1000%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.005%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3CfeColorMatrix type=%22matrix%22 values=%221 0 0 0 0, 0 1 0 0 0, 0 0 1 0 0, 0 0 0 10 -4%22 /%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22 fill=%22none%22 stroke=%22%23ffffff%22 stroke-width=%221%22 opacity=%220.3%22/%3E%3Cpath d=%22M0,100 C200,300 300,0 500,100 C700,200 800,-100 1000,100 M0,200 C250,400 350,100 550,200 C750,300 850,0 1000,200 M0,300 C300,500 400,200 600,300 C800,400 900,100 1000,300 M0,400 C350,600 450,300 650,400 C850,500 950,200 1000,400 M0,500 C400,700 500,400 700,500 C900,600 1000,300 1000,500 M0,600 C450,800 550,500 750,600 C950,700 1000,400 1000,600 M0,700 C500,900 600,600 800,700 C1000,800 1000,500 1000,700 M0,800 C550,1000 650,700 850,800 C1000,900 1000,600 1000,800 M0,900 C600,1100 700,800 900,900 C1000,1000 1000,700 1000,900%22 stroke=%22%23ffffff%22 stroke-width=%221%22 fill=%22none%22 opacity=%220.15%22 /%3E%3C/svg%3E');
      background-size: cover;
      background-position: center;
      mask-image: radial-gradient(ellipse 100% 100% at 50% 50%, black, transparent);
      -webkit-mask-image: radial-gradient(ellipse 100% 100% at 50% 50%, black, transparent);
    "></div>

    <!-- 背景装饰：模糊环境光 (Ambient Glow) -->
    <div
      class="absolute top-[20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-indigo-600/10 dark:bg-indigo-600/5 blur-[150px] pointer-events-none z-0">
    </div>
    <div
      class="absolute bottom-[10%] right-[-5%] w-[400px] h-[400px] rounded-full bg-violet-600/10 dark:bg-violet-600/5 blur-[120px] pointer-events-none z-0">
    </div>

    <!-- 顶部分割线 -->
    <div
      class="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-200 dark:via-white/[0.06] to-transparent transition-colors duration-200">
    </div>

    <div class="relative mx-auto max-w-6xl px-4 sm:px-6">

      <!-- 标题区 -->
      <div class="mb-16 text-center">
        <h2
          class="reveal text-3xl font-semibold tracking-tight mb-4 text-transparent bg-clip-text animate-gradient-sweep bg-[linear-gradient(to_right,rgb(151,137,222)_0%,rgb(151,137,222)_20%,rgb(79,70,229)_50%,rgb(151,137,222)_80%,rgb(151,137,222)_100%)] dark:bg-[linear-gradient(to_right,rgb(151,137,222)_0%,rgb(151,137,222)_20%,rgb(255,255,255)_50%,rgb(151,137,222)_80%,rgb(151,137,222)_100%)]"
          style="
            background-size: 200% auto;
          ">
          驱动学习效率的核心引擎
        </h2>
        <p
          class="reveal mx-auto max-w-xl text-sm text-gray-600 dark:text-white/35 leading-relaxed transition-colors duration-200">
          不仅是简单的图像识别，而是真正理解学科内在逻辑的 AI 智能体系统。
        </p>
      </div>

      <!-- 特性网格 -->
      <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3 relative z-10 max-w-5xl mx-auto">
        <FeatureCard v-for="(f, i) in FEATURES" :key="f.title" :icon="f.icon" :title="f.title" :desc="f.desc"
          :spanClass="f.span" :delay="`${i * 80}ms`" />
      </div>

    </div>
  </section>
</template>

<style scoped>
/* 移除旧的 hover translateY 浮动效果，保留纯粹的光效反馈 */
@keyframes gradient-sweep {
  0% {
    background-position: -100% center;
  }

  100% {
    background-position: 100% center;
  }
}

.animate-gradient-sweep {
  animation: gradient-sweep 3s ease-in-out infinite alternate;
}
</style>
