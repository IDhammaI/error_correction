<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Zap, UploadCloud, ArrowRight, Terminal, CheckCircle2, Sparkles } from 'lucide-vue-next'

const canvasRef = ref(null)
const terminalRef = ref(null)

let raf = null
let resizeUnlisten = null

// ── 终端打字机动画 ──
const termLines = ref([])
const cursorVisible = ref(true)
let typeTimers = []

const TERMINAL_SCRIPT = [
  { type: 'cmd', text: 'init PaddleOCR-VL --async --model=v1.5', delay: 500 },
  { type: 'info', text: '[upload] 正在上传 exam_scan_001.jpg (2.4MB)...', delay: 1200 },
  { type: 'success', text: '[OCR] 文档结构解析完成 (1.2s) — 提取 3,847 字符, 12 blocks', delay: 2800 },
  { type: 'blank', delay: 3200 },
  { type: 'cmd', text: 'LangGraph.invoke(note_agent, provider="deepseek")', delay: 3600 },
  { type: 'info', text: '[agent] 识别知识结构 & 归纳要点...', delay: 4800 },
  { type: 'blank', delay: 5600 },
  { type: 'comment', text: '# Fixing OCR artifacts & converting to LaTeX', delay: 6000 },
  { type: 'diff-del', text: 'original: f(x)=sin(wx+φ)', delay: 6800 },
  { type: 'diff-add', text: 'fixed:    f(x) = sin(ωx + φ)', delay: 7600 },
  { type: 'blank', delay: 8400 },
  { type: 'success', text: '[agent] 知识点标签: 三角函数, 诱导公式, 周期性', delay: 9000 },
  { type: 'info', text: 'Generating Markdown structured output...', delay: 10000 },
  { type: 'success', text: '✓ 笔记整理完成 — 已保存到笔记库', delay: 11500 },
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

// ── Canvas neural animation ──
function initCanvas(canvas) {
  const ctx = canvas.getContext('2d')
  const NODE_COUNT = 72
  const CONNECT_DIST = 180
  const MAX_CONNECTIONS = 4
  let W, H, nodes, edges, pulses

  function isDark() { return document.documentElement.classList.contains('dark') }

  function resize() {
    W = canvas.width = canvas.offsetWidth
    H = canvas.height = canvas.offsetHeight
    init()
  }

  function init() {
    nodes = Array.from({ length: NODE_COUNT }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      r: 2 + Math.random() * 2,
      activation: 0,
    }))
    pulses = []
    for (let i = 0; i < 18; i++) spawnPulse()
  }

  function buildEdges() {
    edges = []
    const used = new Array(NODE_COUNT).fill(0)
    for (let i = 0; i < NODE_COUNT; i++) {
      const neighbors = []
      for (let j = 0; j < NODE_COUNT; j++) {
        if (i === j) continue
        const dx = nodes[i].x - nodes[j].x
        const dy = nodes[i].y - nodes[j].y
        const d = Math.sqrt(dx * dx + dy * dy)
        if (d < CONNECT_DIST) neighbors.push({ j, d })
      }
      neighbors.sort((a, b) => a.d - b.d)
      neighbors.slice(0, MAX_CONNECTIONS).forEach(({ j, d }) => {
        if (used[i] < MAX_CONNECTIONS && used[j] < MAX_CONNECTIONS) {
          if (!edges.find(e => (e.a === i && e.b === j) || (e.a === j && e.b === i))) {
            edges.push({ a: i, b: j, alpha: 1 - d / CONNECT_DIST })
            used[i]++
            used[j]++
          }
        }
      })
    }
  }

  function spawnPulse() {
    if (!edges || edges.length === 0) return
    const edge = edges[Math.floor(Math.random() * edges.length)]
    pulses.push({
      edge,
      progress: 0,
      speed: 0.012 + Math.random() * 0.012,
    })
  }

  let lastSpawn = 0
  function update(ts) {
    nodes.forEach(n => {
      n.x += n.vx
      n.y += n.vy
      if (n.x < 0 || n.x > W) n.vx *= -1
      if (n.y < 0 || n.y > H) n.vy *= -1
      n.activation *= 0.94
    })

    buildEdges()

    for (let i = pulses.length - 1; i >= 0; i--) {
      const p = pulses[i]
      p.progress += p.speed
      if (p.progress >= 1) {
        const targetIdx = p.edge.b
        nodes[targetIdx].activation = 1
        pulses.splice(i, 1)
        const outEdges = edges.filter(e => e.a === targetIdx || e.b === targetIdx)
        if (outEdges.length && Math.random() < 0.7) {
          const next = outEdges[Math.floor(Math.random() * outEdges.length)]
          const fwd = next.a === targetIdx ? next : { a: next.b, b: next.a, alpha: next.alpha }
          pulses.push({ edge: fwd, progress: 0, speed: 0.012 + Math.random() * 0.012 })
        }
      }
    }

    if (ts - lastSpawn > 800) {
      spawnPulse()
      lastSpawn = ts
    }
  }

  function draw() {
    ctx.clearRect(0, 0, W, H)
    const dark = isDark()

    edges.forEach(({ a, b, alpha }) => {
      const na = nodes[a], nb = nodes[b]
      const act = Math.max(na.activation, nb.activation)
      const baseAlpha = dark ? 0.08 : 0.06
      const lineAlpha = baseAlpha + act * (dark ? 0.25 : 0.2)
      ctx.beginPath()
      ctx.moveTo(na.x, na.y)
      ctx.lineTo(nb.x, nb.y)
      ctx.strokeStyle = dark
        ? `rgba(99,102,241,${(lineAlpha * alpha).toFixed(3)})`
        : `rgba(59,130,246,${(lineAlpha * alpha).toFixed(3)})`
      ctx.lineWidth = 0.8 + act * 0.6
      ctx.stroke()
    })

    nodes.forEach(n => {
      const act = n.activation
      const baseR = n.r
      const r = baseR + act * 4

      if (act > 0.05) {
        const grd = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, r * 4)
        grd.addColorStop(0, dark ? `rgba(165,180,252,${act * 0.5})` : `rgba(59,130,246,${act * 0.4})`)
        grd.addColorStop(1, 'transparent')
        ctx.beginPath()
        ctx.arc(n.x, n.y, r * 4, 0, Math.PI * 2)
        ctx.fillStyle = grd
        ctx.fill()
      }

      ctx.beginPath()
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2)
      ctx.fillStyle = dark
        ? `rgba(${act > 0.1 ? '165,180,252' : '99,102,241'},${0.2 + act * 0.7})`
        : `rgba(${act > 0.1 ? '59,130,246' : '148,163,184'},${0.25 + act * 0.6})`
      ctx.fill()
    })

    pulses.forEach(p => {
      const na = nodes[p.edge.a], nb = nodes[p.edge.b]
      const x = na.x + (nb.x - na.x) * p.progress
      const y = na.y + (nb.y - na.y) * p.progress

      const grd2 = ctx.createRadialGradient(x, y, 0, x, y, 22)
      grd2.addColorStop(0, dark ? 'rgba(99,102,241,0.45)' : 'rgba(59,130,246,0.35)')
      grd2.addColorStop(1, 'transparent')
      ctx.beginPath()
      ctx.arc(x, y, 22, 0, Math.PI * 2)
      ctx.fillStyle = grd2
      ctx.fill()

      const grd = ctx.createRadialGradient(x, y, 0, x, y, 10)
      grd.addColorStop(0, dark ? 'rgba(224,231,255,1)' : 'rgba(59,130,246,0.95)')
      grd.addColorStop(0.35, dark ? 'rgba(99,102,241,0.7)' : 'rgba(99,102,241,0.55)')
      grd.addColorStop(1, 'transparent')
      ctx.beginPath()
      ctx.arc(x, y, 10, 0, Math.PI * 2)
      ctx.fillStyle = grd
      ctx.fill()

      ctx.beginPath()
      ctx.arc(x, y, 2.5, 0, Math.PI * 2)
      ctx.fillStyle = dark ? 'rgba(224,231,255,1)' : 'rgba(59,130,246,1)'
      ctx.fill()
    })
  }

  function loop(ts) {
    update(ts)
    draw()
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
  <!-- ① Sticky Hero 容器 -->
  <div id="sticky-hero" class="sticky top-0 h-screen overflow-hidden z-0 flex items-center bg-slate-50 dark:bg-[#0A0A0F]">

    <!-- 动态背景环境光 -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none z-0 h-screen">
      <div class="absolute top-[-10%] left-[-10%] w-[40vw] h-[40vw] rounded-full bg-blue-300/20 dark:bg-indigo-600/20 dark:mix-blend-screen filter blur-[100px] animate-blob"></div>
      <div class="absolute top-[20%] right-[-10%] w-[35vw] h-[35vw] rounded-full bg-indigo-200/25 dark:bg-indigo-600/20 dark:mix-blend-screen filter blur-[100px] animate-blob animation-delay-2000"></div>
      <div class="absolute bottom-[-20%] left-[20%] w-[50vw] h-[50vw] rounded-full bg-cyan-200/20 dark:bg-cyan-600/10 dark:mix-blend-screen filter blur-[120px] animate-blob animation-delay-4000"></div>
      <div class="absolute inset-0 bg-[url(&quot;data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E&quot;)] opacity-[0.03] dark:opacity-20 mix-blend-overlay"></div>
    </div>

    <!-- 电路板背景动画 -->
    <canvas
      ref="canvasRef"
      id="circuit-canvas"
      class="absolute inset-0 pointer-events-none z-0"
      style="height:100vh;width:100%;opacity:0;transition:opacity 1.2s ease;"
    ></canvas>

    <!-- 首屏区块 -->
    <section id="hero" class="relative w-full pt-20 pb-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-16 z-10" style="transform-origin: center 55%; will-change: transform;">
      <div class="flex-1 text-center lg:text-left">
        <div class="hero-anim">
          <div class="mb-10 flex items-center justify-center lg:justify-start">
            <div class="relative flex items-center gap-3 py-1 text-xs font-black tracking-widest text-blue-700/90 dark:text-indigo-300/90">
              <div class="relative flex h-5 w-5 items-center justify-center">
                <Zap class="absolute w-4 h-4 text-orange-500 dark:text-yellow-400 animate-pulse" />
                <div class="absolute h-full w-full animate-ping rounded-full bg-orange-400/10 dark:bg-yellow-400/10"></div>
              </div>
              <span class="relative z-10 uppercase pb-0.5">
                新一代 AI 错题处理架构 <span class="ml-1 font-extrabold text-blue-600 dark:text-indigo-300">V2.0</span>
              </span>
            </div>
          </div>
          <h1 class="text-4xl font-extrabold tracking-tight leading-[1.1] mb-6 text-slate-900 dark:text-white">
            重塑错题整理 <br />
            <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-cyan-400 dark:via-indigo-400 dark:to-indigo-400 animate-pulse">
              一键生成知识图谱
            </span>
          </h1>
          <p class="text-base md:text-xl text-slate-600 dark:text-slate-400 mb-10 max-w-2xl mx-auto lg:mx-0 leading-relaxed">
            专为中学生与大学生研发。上传凌乱试卷，AI 自动完成图片分割、OCR 纠错及 LaTeX 公式还原。释放你的双手，将时间交还给真正的思考。
          </p>
          <div class="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start" style="transition-delay: 450ms;">
            <RouterLink to="/auth" class="relative inline-flex group h-14 w-full sm:w-auto">
              <div class="absolute -inset-px bg-gradient-to-r from-blue-400 via-indigo-400 to-blue-500 rounded-full blur-lg opacity-0 group-hover:opacity-80 transition-opacity duration-500"></div>
              <span class="relative inline-flex items-center justify-center w-full px-8 py-4 text-base font-bold text-white bg-white/15 hover:bg-white/25 border border-white/30 rounded-full backdrop-blur-md transition-all gap-3">
                <UploadCloud class="w-5 h-5" />
                上传试卷分析
              </span>
            </RouterLink>
            <a href="#demo" class="relative inline-flex group h-14 w-full sm:w-auto">
              <div class="absolute -inset-px bg-gradient-to-r from-blue-400 via-indigo-400 to-blue-500 rounded-full blur-lg opacity-0 group-hover:opacity-80 transition-opacity duration-500"></div>
              <span class="relative inline-flex items-center justify-center w-full px-8 py-4 text-base font-bold text-white bg-white/15 hover:bg-white/25 border border-white/30 rounded-full backdrop-blur-md transition-all gap-2">
                查看实时演示
                <ArrowRight class="w-5 h-5" />
              </span>
            </a>
          </div>
        </div>
      </div>

      <!-- 右侧代码状态图 -->
      <div class="hero-anim flex-1 relative w-full max-w-xl lg:max-w-none" style="transition-delay: 200ms;">
        <div class="relative animate-float group">

          <!-- 后层：空窗口 -->
          <div class="absolute inset-0 translate-x-6 -translate-y-5 z-0 opacity-80 dark:opacity-60 pointer-events-none transition-transform duration-500 ease-out group-hover:translate-x-10 group-hover:-translate-y-8">
            <div class="relative bg-white dark:bg-transparent dark:glass-panel rounded-2xl p-1 border border-slate-200 dark:border-indigo-500/40 shadow-md dark:shadow-[0_0_20px_rgba(99,102,241,0.2)] h-full">
              <div class="bg-slate-50 dark:bg-[#0A0A0F]/80 backdrop-blur-md rounded-t-xl p-4 flex items-center justify-between border-b border-slate-100 dark:border-white/5">
                <div class="flex gap-2">
                  <div class="w-3 h-3 rounded-full bg-red-400 dark:bg-[#FF5F57]"></div>
                  <div class="w-3 h-3 rounded-full bg-yellow-400 dark:bg-[#FFBD2E]"></div>
                  <div class="w-3 h-3 rounded-full bg-green-400 dark:bg-[#28C840]"></div>
                </div>
                <div class="flex items-center gap-2 text-xs font-mono text-slate-400 dark:text-slate-600">
                  <Terminal class="w-3 h-3" />
                  error_bank.py
                </div>
              </div>
              <div class="bg-white dark:bg-[#0A0A0F]/90 rounded-b-xl h-[340px]"></div>
            </div>
          </div>

          <!-- 前层：有内容的卡片 -->
          <div class="relative overflow-hidden rounded-2xl z-10 transition-transform duration-500 ease-out group-hover:-translate-x-2 group-hover:translate-y-1">
            <div class="absolute inset-0 bg-gradient-to-tr from-blue-200 to-indigo-200 dark:from-indigo-500 dark:to-indigo-500 rounded-3xl transform rotate-6 scale-105 opacity-60 dark:opacity-20 blur-xl"></div>
            <div class="absolute inset-0 bg-gradient-to-bl from-cyan-200 to-blue-200 dark:from-cyan-500 dark:to-blue-500 rounded-3xl transform -rotate-3 scale-105 opacity-60 dark:opacity-20 blur-xl"></div>
            <div class="bg-white dark:bg-transparent dark:glass-panel rounded-2xl p-1 relative overflow-hidden border border-slate-200 dark:border-indigo-500/40 shadow-md dark:shadow-[0_0_20px_rgba(99,102,241,0.2)]">
              <div class="bg-slate-50 dark:bg-[#0A0A0F]/80 backdrop-blur-md rounded-t-xl p-4 flex items-center justify-between border-b border-slate-100 dark:border-white/5">
                <div class="flex gap-2">
                  <div class="w-3 h-3 rounded-full bg-red-400 dark:bg-[#FF5F57]"></div>
                  <div class="w-3 h-3 rounded-full bg-yellow-400 dark:bg-[#FFBD2E]"></div>
                  <div class="w-3 h-3 rounded-full bg-green-400 dark:bg-[#28C840]"></div>
                </div>
                <div class="flex items-center gap-2 text-xs font-mono text-slate-500">
                  <Terminal class="w-3 h-3" />
                  agent_workflow.py
                </div>
              </div>

              <div ref="terminalRef" class="bg-white dark:bg-[#0A0A0F]/90 p-5 rounded-b-xl font-mono text-[13px] leading-relaxed h-[340px] overflow-hidden relative">
                <div class="space-y-1.5">
                  <div v-for="(line, i) in termLines" :key="i">
                    <!-- 空行 -->
                    <div v-if="line.type === 'blank'" class="h-2"></div>
                    <!-- 命令行 -->
                    <div v-else-if="line.type === 'cmd'" class="flex items-start gap-2">
                      <span class="text-cyan-500 shrink-0">❯</span>
                      <span class="text-slate-300">{{ (line.text || '').slice(0, line.charIndex) }}</span>
                    </div>
                    <!-- 成功 -->
                    <div v-else-if="line.type === 'success'" class="flex items-start gap-2 text-emerald-400">
                      <span class="shrink-0">✓</span>
                      <span>{{ (line.text || '').slice(0, line.charIndex) }}</span>
                    </div>
                    <!-- 注释 -->
                    <div v-else-if="line.type === 'comment'" class="text-indigo-400">
                      {{ (line.text || '').slice(0, line.charIndex) }}
                    </div>
                    <!-- diff 删除 -->
                    <div v-else-if="line.type === 'diff-del'" class="flex items-start gap-2">
                      <span class="text-rose-500 shrink-0">-</span>
                      <span class="text-rose-400/70 line-through">{{ (line.text || '').slice(0, line.charIndex) }}</span>
                    </div>
                    <!-- diff 新增 -->
                    <div v-else-if="line.type === 'diff-add'" class="flex items-start gap-2">
                      <span class="text-emerald-500 shrink-0">+</span>
                      <span class="text-emerald-400">{{ (line.text || '').slice(0, line.charIndex) }}</span>
                    </div>
                    <!-- 普通信息 -->
                    <div v-else class="text-slate-400">
                      {{ (line.text || '').slice(0, line.charIndex) }}
                    </div>
                  </div>
                </div>
                <!-- 光标 -->
                <span
                  v-if="termLines.length > 0"
                  class="inline-block w-[7px] h-[15px] ml-0.5 -mb-0.5 align-middle"
                  :class="cursorVisible ? 'bg-cyan-400' : 'bg-transparent'"
                ></span>
              </div>
            </div>
          </div><!-- /光晕裁切层 -->
        </div>
      </div>
    </section>

  </div><!-- /sticky-hero -->
</template>
