<script setup>
import { onMounted, ref } from 'vue'
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
const cardsRef = ref([])

function handleGridMouseMove(e) {
  // 更新卡片的鼠标位置 (卡片是 relative 相对定位，需要计算相对坐标)
  cardsRef.value.forEach((card) => {
    if (!card) return
    const rect = card.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    card.style.setProperty('--mouse-x', `${x}px`)
    card.style.setProperty('--mouse-y', `${y}px`)
  })
}
</script>

<template>
  <section id="features" class="relative py-24 overflow-hidden" @mousemove="handleGridMouseMove">

    <!-- 背景装饰：模糊环境光 (Ambient Glow) -->
    <div class="absolute top-[20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-indigo-600/5 blur-[150px] pointer-events-none z-0"></div>
    <div class="absolute bottom-[10%] right-[-5%] w-[400px] h-[400px] rounded-full bg-violet-600/5 blur-[120px] pointer-events-none z-0"></div>

    <!-- 顶部分割线 -->
    <div class="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/[0.06] to-transparent"></div>

    <div class="relative mx-auto max-w-6xl px-4 sm:px-6">

      <!-- 标题区 -->
      <div class="mb-16 text-center">
        <h2 class="reveal text-3xl font-semibold tracking-tight mb-4 text-transparent bg-clip-text animate-gradient-sweep" style="
            background-image: linear-gradient(to right, rgb(151, 137, 222) 0%, rgb(151, 137, 222) 20%, rgb(255, 255, 255) 50%, rgb(151, 137, 222) 80%, rgb(151, 137, 222) 100%);
            background-size: 200% auto;
          ">
          驱动学习效率的核心引擎
        </h2>
        <p class="reveal mx-auto max-w-xl text-sm text-white/35 leading-relaxed">
          不仅是简单的图像识别，而是真正理解学科内在逻辑的 AI 智能体系统。
        </p>
      </div>

      <!-- 特性网格 -->
      <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3 relative z-10 max-w-5xl mx-auto">
        <div
          v-for="(f, i) in FEATURES"
          :key="f.title"
          ref="cardsRef"
          class="reveal feature-card group relative flex flex-col rounded-[20px] p-[1px] overflow-hidden"
          :class="f.span"
          :style="{ transitionDelay: `${i * 80}ms` }"
        >
          <!-- 默认状态：灰色 Linear 渐变边框层 -->
          <div class="absolute inset-0 bg-gradient-to-br from-white/[0.12] via-white/[0.04] to-transparent"></div>

          <!-- 鼠标跟随：边框高光层 -->
          <div class="pointer-events-none absolute inset-0 transition-opacity duration-300"
               style="background: radial-gradient(300px circle at var(--mouse-x, -1000px) var(--mouse-y, -1000px), rgba(129, 115, 223, 0.5), transparent 40%);">
          </div>
          
          <!-- 卡片主体背景层 (修改为半透明玻璃态) -->
          <div class="relative h-full w-full rounded-[19px] bg-gradient-to-br from-[#1A1A24]/60 to-[#0A0A0F]/60 p-6 flex flex-col items-start text-left transition-all duration-500 overflow-hidden shadow-2xl shadow-black/50 border border-white/[0.02]">
            <!-- 静态微弱磨砂噪点层 (降低透明度和颗粒粗糙度) -->
            <div class="pointer-events-none absolute inset-0 opacity-[0.03]" style="background-image: url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.85%22 numOctaves=%221%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E');"></div>

            <!-- 鼠标跟随：内部环境光晕 -->
            <div class="pointer-events-none absolute inset-0 transition-opacity duration-300"
                 style="background: radial-gradient(250px circle at var(--mouse-x, -1000px) var(--mouse-y, -1000px), rgba(129, 115, 223, 0.12), transparent 40%);">
            </div>

            <!-- 图标容器 (带边框鼠标跟随高光) -->
            <div class="relative z-10 mb-4 flex h-10 w-10 items-center justify-center rounded-xl p-[1px] overflow-hidden">
              <!-- 默认暗色边框 -->
              <div class="absolute inset-0 bg-white/[0.08] rounded-xl"></div>
              
              <!-- 鼠标跟随：图标边框高光层 -->
              <div class="pointer-events-none absolute inset-0 transition-opacity duration-300"
                   style="background: radial-gradient(100px circle at calc(var(--mouse-x, -1000px) - 24px) calc(var(--mouse-y, -1000px) - 24px), rgba(151, 137, 222, 0.8), transparent 40%);">
              </div>
              
              <!-- 图标内部主体 -->
              <div class="relative h-full w-full bg-[#15151e] rounded-[11px] flex items-center justify-center shadow-inner">
                <!-- 静态白色图标 (底层) -->
                <component :is="f.icon" class="absolute h-5 w-5 text-white/60" />
                
                <!-- 鼠标跟随：染色图标 (顶层，通过遮罩只显示光圈经过的部分) -->
                <div class="absolute inset-0 flex items-center justify-center transition-opacity duration-300"
                     style="mask-image: radial-gradient(40px circle at calc(var(--mouse-x, -1000px) - 24px) calc(var(--mouse-y, -1000px) - 24px), black 0%, transparent 100%);
                            -webkit-mask-image: radial-gradient(40px circle at calc(var(--mouse-x, -1000px) - 24px) calc(var(--mouse-y, -1000px) - 24px), black 0%, transparent 100%);">
                  <component :is="f.icon" class="h-5 w-5 text-[#9789de] drop-shadow-[0_0_8px_rgba(151,137,222,0.8)]" />
                </div>
              </div>
            </div>
            
            <!-- 文字内容 -->
            <h3 class="relative z-10 mb-2 text-base font-semibold text-white/90 group-hover:text-white transition-colors duration-300">{{ f.title }}</h3>
            <p class="relative z-10 text-sm leading-relaxed text-white/40 group-hover:text-white/60 transition-colors duration-300">{{ f.desc }}</p>
          </div>
        </div>
      </div>

    </div>
  </section>
</template>

<style scoped>
/* 移除旧的 hover translateY 浮动效果，保留纯粹的光效反馈 */
@keyframes gradient-sweep {
  0% { background-position: -100% center; }
  100% { background-position: 100% center; }
}

.animate-gradient-sweep {
  animation: gradient-sweep 3s ease-in-out infinite alternate;
}
</style>
