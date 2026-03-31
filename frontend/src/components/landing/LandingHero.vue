<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Zap, UploadCloud, ArrowRight, Terminal, CheckCircle2, Sparkles } from 'lucide-vue-next'

const emit = defineEmits(['scrollToSection'])

const canvasRef = ref(null)
const terminalRef = ref(null)

let raf = null
let resizeUnlisten = null

// ── 终端打字机动画 ──
const termLines = ref([])
const cursorVisible = ref(true)
let typeTimers = []

const TERMINAL_SCRIPT = [
  { type: 'cmd', text: 'init PaddleOCR-VL --async', delay: 500 },
  { type: 'success', text: '[OCR] 解析完成 (1.2s) — 3,847 字符', delay: 2200 },
  { type: 'blank', delay: 2800 },
  { type: 'cmd', text: 'LangGraph.invoke(note_agent)', delay: 3200 },
  { type: 'comment', text: '# Fixing OCR artifacts', delay: 4500 },
  { type: 'diff-del', text: 'f(x)=sin(wx+φ)', delay: 5300 },
  { type: 'diff-add', text: 'f(x) = sin(ωx + φ)', delay: 6100 },
  { type: 'blank', delay: 6800 },
  { type: 'success', text: '标签: 三角函数, 诱导公式, 周期性', delay: 7400 },
  { type: 'info', text: 'Generating Markdown output...', delay: 8500 },
  { type: 'success', text: '笔记整理完成 — 已保存', delay: 9800 },
]

function startTerminalAnimation() {
  termLines.value = []
  typeTimers.forEach(clearTimeout)
  typeTimers = []

  TERMINAL_SCRIPT.forEach((line, i) => {
    typeTimers.push(setTimeout(() => {
      termLines.value.push({ ...line, charIndex: 0 })
      // 逐字打出
      const lineIdx = termLines.value.length - 1
      const text = line.text || ''
      for (let c = 0; c <= text.length; c++) {
        typeTimers.push(setTimeout(() => {
          if (termLines.value[lineIdx]) {
            termLines.value[lineIdx].charIndex = c
          }
        }, c * 18))
      }
    }, line.delay))
  })

  // 动画结束后停止光标闪烁
  const totalDuration = TERMINAL_SCRIPT[TERMINAL_SCRIPT.length - 1].delay + 2000
  typeTimers.push(setTimeout(() => { cursorVisible.value = false }, totalDuration))
}

// 光标闪烁
let blinkTimer = null

// ── Canvas 微光粒子动画 ──
function initCanvas(canvas) {
  const ctx = canvas.getContext('2d')
  const COUNT = 60
  let W, H, particles

  function isDark() { return document.documentElement.classList.contains('dark') }

  function resize() {
    W = canvas.width = canvas.offsetWidth
    H = canvas.height = canvas.offsetHeight
    init()
  }

  function init() {
    particles = Array.from({ length: COUNT }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.15,
      vy: (Math.random() - 0.5) * 0.1 - 0.05, // 微微上飘
      r: 1 + Math.random() * 2,
      baseAlpha: 0.15 + Math.random() * 0.35,
      phase: Math.random() * Math.PI * 2, // 呼吸闪烁相位
      speed: 0.005 + Math.random() * 0.01,
    }))
  }

  function draw(ts) {
    ctx.clearRect(0, 0, W, H)
    const dark = isDark()

    particles.forEach(p => {
      // 移动
      p.x += p.vx
      p.y += p.vy
      if (p.x < -10) p.x = W + 10
      if (p.x > W + 10) p.x = -10
      if (p.y < -10) p.y = H + 10
      if (p.y > H + 10) p.y = -10

      // 呼吸闪烁
      const breath = Math.sin(ts * p.speed + p.phase) * 0.5 + 0.5
      const alpha = p.baseAlpha * (0.3 + breath * 0.7)

      // 外发光
      const glow = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 6)
      glow.addColorStop(0, dark
        ? `rgba(165,180,252,${(alpha * 0.4).toFixed(3)})`
        : `rgba(99,102,241,${(alpha * 0.3).toFixed(3)})`)
      glow.addColorStop(1, 'transparent')
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r * 6, 0, Math.PI * 2)
      ctx.fillStyle = glow
      ctx.fill()

      // 粒子核心
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fillStyle = dark
        ? `rgba(199,210,254,${alpha.toFixed(3)})`
        : `rgba(99,102,241,${alpha.toFixed(3)})`
      ctx.fill()
    })
  }

  function loop(ts) {
    draw(ts)
    raf = requestAnimationFrame(loop)
  }

  const onResize = () => resize()
  window.addEventListener('resize', onResize)
  resizeUnlisten = () => window.removeEventListener('resize', onResize)

  resize()
  raf = requestAnimationFrame(loop)
  requestAnimationFrame(() => { canvas.style.opacity = '1' })
}

onMounted(() => {
  if (canvasRef.value) {
    initCanvas(canvasRef.value)
  }
  startTerminalAnimation()
  blinkTimer = setInterval(() => { cursorVisible.value = !cursorVisible.value }, 530)
})

onUnmounted(() => {
  if (resizeUnlisten) resizeUnlisten()
  if (raf) cancelAnimationFrame(raf)
  typeTimers.forEach(clearTimeout)
  if (blinkTimer) clearInterval(blinkTimer)
})
</script>

<template>
  <!-- ① Sticky Hero 容器 — Linear 风格 -->
  <div id="sticky-hero" class="sticky top-0 h-screen overflow-hidden z-0 flex items-center bg-[#0A0A0F]">

    <!-- 顶部装饰椭圆 -->
    <div class="absolute pointer-events-none z-0" style="
      top: -150%;
      left: 50%;
      transform: translateX(-50%);
      width: 140%;
      aspect-ratio: 1.3 / 1;
      border-radius: 50%;
      background: linear-gradient(to bottom, rgba(92,81,148,0.5), rgba(47,40,91,0.95));
      box-shadow:
        inset 0 -20px 24px 0 rgba(255,255,255,0.15),
        0 16px 32px 0 rgba(97,62,210,0.32),
        inset 0 -1px 0 0 rgba(129,115,223,0.6);
    "></div>

    <!-- 首屏区块 -->
    <section id="hero" class="relative w-full pt-20 pb-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-20 z-10">

      <!-- 左侧文案 -->
      <div class="flex-1 text-center lg:text-left">
        <!-- 标签 -->
        <div class="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs font-medium text-white/50">
          <span class="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          PaddleOCR + LangChain Agent
        </div>

        <h1 class="text-4xl sm:text-5xl font-semibold tracking-tight leading-[1.15] mb-6 text-white">
          重塑错题整理<br />
          <span class="text-white/40">一键生成知识图谱</span>
        </h1>

        <p class="text-base text-white/40 mb-10 max-w-lg mx-auto lg:mx-0 leading-relaxed">
          上传试卷或手写笔记，AI 自动完成 OCR 识别、题目分割、公式还原、知识点标注。专为中学生与大学生设计。
        </p>

        <div class="flex flex-col sm:flex-row gap-3 justify-center lg:justify-start">
          <RouterLink to="/auth" class="inline-flex items-center justify-center h-10 px-6 text-sm font-medium rounded-lg bg-white text-[#0A0A0F] hover:bg-white/90 transition-colors gap-2">
            <UploadCloud class="w-4 h-4" />
            开始使用
          </RouterLink>
          <a href="#demo" class="inline-flex items-center justify-center h-10 px-6 text-sm font-medium rounded-lg border border-white/10 text-white/70 hover:text-white hover:border-white/20 transition-colors gap-2">
            查看演示
            <ArrowRight class="w-4 h-4" />
          </a>
        </div>
      </div>

      <!-- 右侧终端 -->
      <div class="flex-1 relative w-full max-w-xl lg:max-w-none">
        <div class="relative">
          <!-- 终端窗口 -->
          <div class="rounded-lg border border-white/[0.06] bg-[#111118] overflow-hidden">
            <!-- 标题栏 -->
            <div class="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
              <div class="flex gap-1.5">
                <div class="w-2.5 h-2.5 rounded-full bg-white/10"></div>
                <div class="w-2.5 h-2.5 rounded-full bg-white/10"></div>
                <div class="w-2.5 h-2.5 rounded-full bg-white/10"></div>
              </div>
              <span class="text-[11px] font-mono text-white/25">agent_workflow.py</span>
            </div>

            <!-- 终端内容 -->
            <div ref="terminalRef" class="p-5 font-mono text-[13px] leading-relaxed h-[320px] overflow-hidden">
              <div class="space-y-1.5">
                <div v-for="(line, i) in termLines" :key="i">
                  <div v-if="line.type === 'blank'" class="h-2"></div>
                  <div v-else-if="line.type === 'cmd'" class="flex items-start gap-2">
                    <span class="text-indigo-400 shrink-0">❯</span>
                    <span class="text-white/70">{{ (line.text || '').slice(0, line.charIndex) }}</span>
                  </div>
                  <div v-else-if="line.type === 'success'" class="flex items-start gap-2 text-emerald-400/80">
                    <span class="shrink-0">✓</span>
                    <span>{{ (line.text || '').slice(0, line.charIndex) }}</span>
                  </div>
                  <div v-else-if="line.type === 'comment'" class="text-white/25">
                    {{ (line.text || '').slice(0, line.charIndex) }}
                  </div>
                  <div v-else-if="line.type === 'diff-del'" class="flex items-start gap-2">
                    <span class="text-rose-400/70 shrink-0">-</span>
                    <span class="text-rose-400/50 line-through">{{ (line.text || '').slice(0, line.charIndex) }}</span>
                  </div>
                  <div v-else-if="line.type === 'diff-add'" class="flex items-start gap-2">
                    <span class="text-emerald-400/70 shrink-0">+</span>
                    <span class="text-emerald-400/70">{{ (line.text || '').slice(0, line.charIndex) }}</span>
                  </div>
                  <div v-else class="text-white/30">
                    {{ (line.text || '').slice(0, line.charIndex) }}
                  </div>
                </div>
              </div>
              <span
                v-if="termLines.length > 0"
                class="inline-block w-[6px] h-[14px] ml-0.5 -mb-0.5 align-middle"
                :class="cursorVisible ? 'bg-indigo-400' : 'bg-transparent'"
              ></span>
            </div>
          </div>
        </div>
      </div>

    </section>

    <!-- 底部箭头 -->
    <button
      @click="emit('scrollToSection', 'features')"
      class="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 text-white/20 hover:text-white/50 transition-colors cursor-pointer"
    >
      <i class="fa-solid fa-chevron-down text-lg animate-bounce"></i>
    </button>
  </div>
</template>
