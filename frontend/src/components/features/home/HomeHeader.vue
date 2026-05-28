<script setup>
/**
 * HomeHeader.vue
 * 落地页顶部导航栏
 */
import { useTheme } from '@/composables/useTheme.js'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseLogo from '@/components/base/BaseLogo.vue'

const { isDark, toggleTheme } = useTheme()

const props = defineProps({
  navScrolled: Boolean,
  activeSection: String,
  sections: Array,
})

const emit = defineEmits(['scrollToSection'])
</script>

<template>
  <nav id="top-nav"
    class="fixed top-0 left-0 w-full z-50 border-b transition-[border-color,background-color] duration-200"
    :class="navScrolled ? 'border-gray-200/50 bg-white/80 dark:border-white/[0.06] dark:bg-[#0A0A0F]/80 backdrop-blur-md' : 'border-transparent'">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-14">
        <!-- Logo -->
        <div class="flex items-center gap-2.5">
          <BaseLogo size="sm" />
          <span class="text-sm font-semibold text-gray-900 dark:text-white/90 tracking-wide">智卷错题本</span>
        </div>

        <!-- 中间导航 -->
        <div class="hidden md:flex items-center gap-1">
          <button v-for="s in sections" :key="s.id" @click="emit('scrollToSection', s.id)"
            class="px-3 py-1.5 text-[13px] font-medium rounded-md transition-colors"
            :class="activeSection === s.id ? 'text-white accent-bg shadow-sm' : 'text-gray-800 hover:text-black hover:bg-transparent dark:text-white/40 dark:hover:text-white/70 dark:hover:bg-transparent'">{{
              s.label }}</button>
        </div>

        <!-- 右侧操作 -->
        <div class="flex items-center gap-3">
          <button @click="toggleTheme($event.currentTarget)"
            class="w-8 h-8 flex items-center justify-center rounded-md text-gray-800 hover:text-black hover:bg-transparent dark:text-white/40 dark:hover:text-white/70 dark:hover:bg-white/10 transition-colors"
            title="切换主题">
            <i class="fa-solid text-base" :class="isDark ? 'fa-sun' : 'fa-moon'"></i>
          </button>

          <a href="https://github.com/xiaozhejiya/error_correction" target="_blank" rel="noopener noreferrer"
            class="w-8 h-8 flex items-center justify-center rounded-md text-gray-800 hover:text-black hover:bg-transparent dark:text-white/40 dark:hover:text-white/70 dark:hover:bg-white/10 transition-colors">
            <i class="fa-brands fa-github text-base"></i>
          </a>
          <BaseButton to="/auth" size="sm">
            进入工作台
          </BaseButton>
        </div>
      </div>
    </div>
  </nav>
</template>
