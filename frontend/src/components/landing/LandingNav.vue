<script setup>
import { useTheme } from '../../composables/useTheme.js'

const { isDark, toggleTheme } = useTheme()

const props = defineProps({
  navScrolled: Boolean,
  activeSection: String,
  indicatorTop: Number,
  sections: Array,
})

const emit = defineEmits(['scrollToSection'])
</script>

<template>
  <!-- 导航栏 -->
  <nav
    id="top-nav"
    class="fixed top-0 left-0 w-full z-50 border-b border-transparent transition-[border-color,backdrop-filter] duration-300"
    :class="navScrolled ? 'glass-panel !border-white/5' : 'border-transparent'"
  >
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div
        id="nav-container"
        class="flex justify-between items-center transition-all duration-300"
        :class="navScrolled ? 'h-16' : 'h-20'"
      >
        <div class="flex items-center gap-3">
          <img src="/logo-dark.svg" class="w-7 h-7 block dark:hidden" alt="logo" />
          <img src="/logo.svg" class="w-7 h-7 hidden dark:block" alt="logo" />
          <span class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-700 to-indigo-700 dark:from-white dark:via-indigo-200 dark:to-indigo-200 tracking-wide">
            智卷错题本
          </span>
        </div>
        <div class="hidden md:flex space-x-8">
          <button data-section="features" class="text-slate-600 hover:text-blue-600 dark:text-slate-400 dark:hover:text-white text-sm font-semibold tracking-wider" @click="emit('scrollToSection', 'features')">核心功能</button>
          <button data-section="workflow" class="text-slate-600 hover:text-blue-600 dark:text-slate-400 dark:hover:text-white text-sm font-semibold tracking-wider" @click="emit('scrollToSection', 'workflow')">工作流</button>
          <button data-section="demo" class="text-slate-600 hover:text-blue-600 dark:text-slate-400 dark:hover:text-white text-sm font-semibold tracking-wider" @click="emit('scrollToSection', 'demo')">效果演示</button>
          <button data-section="cta" class="text-slate-600 hover:text-blue-600 dark:text-slate-400 dark:hover:text-white text-sm font-semibold tracking-wider" @click="emit('scrollToSection', 'cta')">立即开始</button>
        </div>

        <div class="flex items-center gap-4">
          <a href="https://github.com/xiaozhejiya/error_correction" target="_blank" rel="noopener noreferrer" class="text-slate-400 hover:text-blue-600 dark:hover:text-white transition-colors">
            <i class="fa-brands fa-github text-xl"></i>
          </a>
          <button @click="(e) => toggleTheme(e.currentTarget)" class="text-slate-400 hover:text-blue-600 dark:hover:text-white transition-colors" title="切换主题">
            <i class="fa-solid text-xl" :class="isDark ? 'fa-sun' : 'fa-moon'"></i>
          </button>
          <RouterLink to="/auth" class="relative inline-flex group h-12 active:scale-95 transition-transform">
            <div class="absolute -inset-px bg-gradient-to-r from-blue-400 via-indigo-400 to-blue-500 rounded-full blur-lg opacity-0 group-hover:opacity-80 transition-opacity duration-500"></div>
            <span class="relative inline-flex items-center justify-center px-6 py-2 text-sm font-bold rounded-full transition-all border border-transparent bg-blue-600 text-white hover:bg-blue-700 dark:bg-white/15 dark:text-white dark:hover:bg-white/25 dark:border-white/30 dark:backdrop-blur-md dark:shadow-[0_0_15px_rgba(255,255,255,0.15)] dark:hover:shadow-[0_0_20px_rgba(255,255,255,0.25)]">
              进入工作台
            </span>
          </RouterLink>
        </div>
      </div>
    </div>
  </nav>

  <!-- 右侧 Section 导航 -->
  <nav id="section-nav" class="fixed right-4 md:right-8 top-1/2 -translate-y-1/2 z-40 flex flex-col items-center py-6 px-2 rounded-full border border-slate-200/60 bg-white/60 backdrop-blur-md dark:border-white/5 dark:bg-white/[0.02] scale-90 md:scale-100">
    <!-- 垂直轨道 -->
    <div class="absolute top-8 bottom-8 w-px bg-slate-200 dark:bg-white/10 pointer-events-none"></div>
    <!-- 激活指示器 -->
    <div
      id="section-nav-indicator"
      class="absolute w-2 h-2 bg-blue-600 dark:bg-indigo-400 rounded-full pointer-events-none z-10 transition-[top] duration-500 shadow-blue-600/70 dark:shadow-indigo-400/80"
      :style="{ top: indicatorTop + 'px', transform: 'translateY(-50%)' }"
    ></div>

    <button
      v-for="(s, i) in sections"
      :key="s.id"
      class="section-nav-btn relative flex items-center justify-center w-10 h-10 focus:outline-none group"
      :title="s.label"
      :data-id="s.id"
      @click="emit('scrollToSection', s.id)"
    >
      <div
        class="section-dot w-1.5 h-1.5 rounded-full transition-[transform,box-shadow] duration-300"
        :class="activeSection === s.id
          ? 'bg-blue-600 dark:bg-indigo-400 scale-125 shadow-[0_0_8px_3px_rgba(99,102,241,0.7)] dark:shadow-[0_0_10px_4px_rgba(99,102,241,0.9)]'
          : 'bg-slate-300 dark:bg-white/20 group-hover:bg-blue-400 dark:group-hover:bg-indigo-300'"
      ></div>
      <span class="absolute right-14 px-3 py-1.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/10 text-xs font-black text-slate-700 dark:text-white whitespace-nowrap pointer-events-none opacity-0 translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 shadow-md transition-all duration-300">
        <span class="opacity-40 mr-2">{{ String(i + 1).padStart(2, '0') }}</span>{{ s.label }}
      </span>
    </button>
  </nav>
</template>
