<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'

import LandingNav from '../components/landing/LandingNav.vue'
import LandingHero from '../components/landing/LandingHero.vue'
import LandingFeatures from '../components/landing/LandingFeatures.vue'
import LandingWorkflow from '../components/landing/LandingWorkflow.vue'
import LandingDemo from '../components/landing/LandingDemo.vue'
import LandingCta from '../components/landing/LandingCta.vue'
import LandingBackToTop from '../components/landing/LandingBackToTop.vue'

const SECTIONS = [
  { id: 'hero',     label: '首页' },
  { id: 'features', label: '核心功能' },
  { id: 'workflow', label: '工作流' },
  { id: 'demo',     label: '效果演示' },
  { id: 'cta',      label: '立即开始' },
]

// Refs
const activeSection = ref('hero')
const backToTopVisible = ref(false)
const navScrolled = ref(false)
const indicatorTop = ref(44)

// Cleanup holders
let wheelUnlisten = null
let scrollUnlisten = null
let revealObserver = null

// ── Wheel snap scroll ──
let wheelLock = false

function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3)
}

function scrollToY(target, duration) {
  const start = window.scrollY
  const dist = target - start
  let startTime = null
  function step(ts) {
    if (!startTime) startTime = ts
    const progress = Math.min((ts - startTime) / duration, 1)
    window.scrollTo(0, start + dist * easeOutCubic(progress))
    if (progress < 1) requestAnimationFrame(step)
    else wheelLock = false
  }
  requestAnimationFrame(step)
}

function getSectionTops() {
  const ids = SECTIONS.map(s => s.id)
  return ids.map(id => {
    if (id === 'hero') return 0
    const el = document.getElementById(id)
    return el ? Math.round(el.getBoundingClientRect().top + window.scrollY) : null
  }).filter(v => v !== null)
}

function onWheel(e) {
  e.preventDefault()
  if (wheelLock) return
  const y = window.scrollY
  const tops = getSectionTops()
  const dir = e.deltaY > 0 ? 1 : -1
  let cur = 0
  for (let i = tops.length - 1; i >= 0; i--) {
    if (y >= tops[i] - 10) { cur = i; break }
  }
  const next = Math.max(0, Math.min(tops.length - 1, cur + dir))
  if (next === cur) return
  wheelLock = true
  scrollToY(tops[next], 1000)
}

// ── Scroll handler ──
let ticking = false

function onScroll() {
  const y = window.scrollY

  // Hero fade + 3D tilt
  const stickyHero = document.getElementById('sticky-hero')
  if (stickyHero) {
    const p = Math.min(y / (window.innerHeight * 0.7), 1)
    stickyHero.style.opacity = 1 - p
    const rotateX = p * 28
    const scale = 1 - p * 0.12
    const heroEl = document.getElementById('hero')
    if (heroEl) {
      heroEl.style.transform = `perspective(900px) rotateX(${rotateX}deg) scale(${scale})`
    }
  }

  // Back to top
  backToTopVisible.value = y > 400

  // Nav scroll state
  navScrolled.value = activeSection.value !== 'hero'

  // Section nav update
  updateNav()

  ticking = false
}

function onScrollThrottled() {
  if (!ticking) {
    requestAnimationFrame(onScroll)
    ticking = true
  }
}

// ── Section nav ──
const DOT_SIZE = 40

function updateNav() {
  const { scrollY, innerHeight } = window
  const scrollHeight = document.documentElement.scrollHeight
  const probe = scrollY + innerHeight / 3
  let next = SECTIONS[0].id

  if (innerHeight + scrollY >= scrollHeight - 100) {
    next = SECTIONS[SECTIONS.length - 1].id
  } else {
    for (let i = SECTIONS.length - 1; i >= 0; i--) {
      const el = document.getElementById(SECTIONS[i].id)
      if (el && probe >= el.getBoundingClientRect().top + scrollY) {
        next = SECTIONS[i].id; break
      }
    }
  }

  if (next === activeSection.value) return
  activeSection.value = next
  const idx = SECTIONS.findIndex(s => s.id === activeSection.value)
  indicatorTop.value = idx * DOT_SIZE + 44
}

function scrollToSection(id) {
  if (id === 'hero') {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } else {
    const el = document.getElementById(id)
    if (el) {
      const targetY = el.getBoundingClientRect().top + window.scrollY
      window.scrollTo({ top: targetY, behavior: 'smooth' })
    }
  }
}

function scrollToSectionSnap(id) {
  if (id === 'hero') {
    scrollToY(0, 1000)
  } else {
    const el = document.getElementById(id)
    if (el) scrollToY(el.getBoundingClientRect().top + window.scrollY, 1000)
  }
}

// ── Reveal observer ──
function setupRevealObserver() {
  const observerOptions = { threshold: 0.01, rootMargin: '0px 0px 0px 0px' }
  revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('active')
        revealObserver.unobserve(entry.target)
      }
    })
  }, observerOptions)

  document.querySelectorAll('.reveal').forEach(el => {
    const rect = el.getBoundingClientRect()
    if (rect.top < window.innerHeight && rect.bottom > 0) {
      el.classList.add('active')
    } else {
      revealObserver.observe(el)
    }
  })
}

onMounted(async () => {
  // 读取用户主题偏好，默认暗色
  const savedTheme = localStorage.getItem('theme') || 'dark'
  document.documentElement.classList.toggle('dark', savedTheme === 'dark')

  // Set overflow-hidden on body for wheel snap
  document.body.style.overflow = 'hidden'

  await nextTick()

  // Wheel listener with passive: false
  const wheelHandler = onWheel
  window.addEventListener('wheel', wheelHandler, { passive: false })
  wheelUnlisten = () => window.removeEventListener('wheel', wheelHandler)

  // Scroll listener
  window.addEventListener('scroll', onScrollThrottled, { passive: true })
  scrollUnlisten = () => window.removeEventListener('scroll', onScrollThrottled)

  // Hero anim
  setTimeout(() => {
    document.querySelectorAll('.hero-anim').forEach(el => el.classList.add('is-visible'))
  }, 100)

  // Reveal observer
  setupRevealObserver()

  // MathJax typeset
  await nextTick()
  window.MathJax?.typesetPromise?.()

  // Initial nav state
  updateNav()
})

onUnmounted(() => {
  // Restore body overflow
  document.body.style.overflow = ''

  if (wheelUnlisten) wheelUnlisten()
  if (scrollUnlisten) scrollUnlisten()
  if (revealObserver) revealObserver.disconnect()
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-900 dark:bg-[#0A0A0F] dark:text-slate-300 selection:bg-blue-200 dark:selection:bg-indigo-500/30 page-enter">

    <LandingNav
      :navScrolled="navScrolled"
      :activeSection="activeSection"
      :indicatorTop="indicatorTop"
      :sections="SECTIONS"
      @scrollToSection="scrollToSectionSnap"
    />

    <!-- 主内容包裹层 -->
    <div class="relative">

      <LandingHero @scrollToSection="scrollToSectionSnap" />

      <!-- ② 滚动叠盖层 -->
      <div class="relative z-10 overflow-x-hidden">

        <LandingFeatures />

        <LandingWorkflow />

        <LandingDemo />

        <LandingCta />

      </div><!-- /滚动叠盖层 -->

    </div><!-- /主内容包裹层 -->

    <LandingBackToTop
      :visible="backToTopVisible"
      @click="scrollToY(0, 1000)"
    />

  </div>
</template>

<style>
/* Landing page always uses dark mode class - set in onMounted */

@keyframes pageEnter {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.page-enter {
  animation: pageEnter 0.3s ease forwards;
}

@keyframes blob {
  0% { transform: translate(0px, 0px) scale(1); }
  33% { transform: translate(30px, -50px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
  100% { transform: translate(0px, 0px) scale(1); }
}
.animate-blob { animation: blob 10s infinite alternate; }
.animation-delay-2000 { animation-delay: 2s; }
.animation-delay-4000 { animation-delay: 4s; }

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}
.animate-float { animation: float 6s ease-in-out infinite; }

@keyframes scan {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(100%); }
}
.animate-scan { animation: scan 3s ease-in-out infinite; }

/* 动态玻璃态面板 */
.glass-panel {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
html.dark .glass-panel {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: none;
}

/* 平滑滚动时补偿固定导航栏高度 */
html { scroll-padding-top: 80px; }

/* 禁用浏览器默认 View Transitions 淡出 */
::view-transition-old(root),
::view-transition-new(root) {
  animation: none;
  mix-blend-mode: normal;
}

/* 初始隐藏，用于实现加载动画 */
.hero-anim {
  opacity: 0;
  transform: translateY(40px);
  transition: opacity 1s cubic-bezier(0.2, 0.8, 0.2, 1), transform 1s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.hero-anim.is-visible {
  opacity: 1;
  transform: translateY(0);
}

/* 统一的 Section 进场动画 */
.reveal {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.8s cubic-bezier(0.4, 0, 0.2, 1), transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}
.reveal.active {
  opacity: 1;
  transform: translateY(0);
}
</style>
