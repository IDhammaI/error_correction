<script setup>
import { useTheme } from '../../composables/useTheme.js'
import LandingButton from './LandingButton.vue'
import BrandLogo from '../BrandLogo.vue'

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
  <!-- 导航栏 — Linear 风格 -->
  <nav
    id="top-nav"
    class="fixed top-0 left-0 w-full z-50 border-b transition-[border-color] duration-200"
    :class="navScrolled ? 'border-white/[0.06] bg-[#0A0A0F]/80' : 'border-transparent'"
  >
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-14">
        <!-- Logo -->
        <div class="flex items-center gap-2.5">
          <BrandLogo size="sm" />
          <span class="text-sm font-semibold text-white/90 tracking-wide">智卷错题本</span>
        </div>

        <!-- 中间导航 -->
        <div class="hidden md:flex items-center gap-1">
          <button
            v-for="s in sections"
            :key="s.id"
            @click="emit('scrollToSection', s.id)"
            class="px-3 py-1.5 text-[13px] font-medium rounded-md transition-colors"
            :class="activeSection === s.id ? 'text-white bg-white/[0.06]' : 'text-white/40 hover:text-white/70'"
          >{{ s.label }}</button>
        </div>

        <!-- 右侧操作 -->
        <div class="flex items-center gap-3">
          <a href="https://github.com/xiaozhejiya/error_correction" target="_blank" rel="noopener noreferrer" class="text-white/30 hover:text-white/60 transition-colors">
            <i class="fa-brands fa-github text-base"></i>
          </a>
          <LandingButton to="/auth" size="sm">
            进入工作台
          </LandingButton>
        </div>
      </div>
    </div>
  </nav>

  <!-- 右侧 Section 导航 — Linear 风格 -->
  <nav id="section-nav" class="fixed right-4 md:right-6 top-1/2 -translate-y-1/2 z-40 flex flex-col items-center gap-3 py-4 px-1.5 rounded-lg border border-white/[0.06] bg-[#0A0A0F]/60 scale-90 md:scale-100">
    <button
      v-for="(s, i) in sections"
      :key="s.id"
      class="relative flex items-center justify-center w-6 h-6 focus:outline-none group"
      :title="s.label"
      @click="emit('scrollToSection', s.id)"
    >
      <div
        class="w-1 h-1 rounded-full transition-all duration-200"
        :class="activeSection === s.id
          ? 'bg-white scale-150'
          : 'bg-white/20 group-hover:bg-white/50'"
      ></div>
      <span class="absolute right-10 px-2 py-1 rounded-md bg-[#111118] border border-white/[0.06] text-[11px] font-medium text-white/70 whitespace-nowrap pointer-events-none opacity-0 translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-200">
        {{ s.label }}
      </span>
    </button>
  </nav>
</template>
