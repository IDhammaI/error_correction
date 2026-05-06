<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: {
    type: [Object, Function],
    required: true
  },
  title: {
    type: String,
    required: true
  },
  desc: {
    type: String,
    required: true
  },
  spanClass: {
    type: String,
    default: ''
  },
  delay: {
    type: String,
    default: '0ms'
  }
})
</script>

<template>
  <div
    class="reveal feature-card group relative flex flex-col rounded-[20px] p-[1px] overflow-hidden"
    :class="spanClass"
    :style="{ transitionDelay: delay }"
  >
    <!-- 默认状态：灰色 Linear 渐变边框层 (去除浅色模式下的渐变边框，改用内部阴影和 border) -->
    <div class="absolute inset-0 bg-transparent dark:bg-gradient-to-br dark:from-white/[0.12] dark:via-white/[0.04] dark:to-transparent transition-colors duration-300"></div>

    <!-- Hover 状态下的发光背景层 (浅色模式下增加主题色微光) -->
    <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br from-[rgb(var(--accent-rgb)/0.15)] via-[rgb(var(--accent-hover-rgb)/0.05)] to-transparent dark:from-[rgb(var(--accent-rgb)/0.1)] dark:via-[rgb(var(--accent-hover-rgb)/0.05)] dark:to-transparent z-0"></div>

    <!-- 卡片主体背景层 — brand-btn 风格白玻璃 -->
    <div class="feature-card-inner relative h-full w-full rounded-[19px] p-6 flex flex-col items-start text-left transition-all duration-500 overflow-hidden">

      <!-- 图标容器（BaseLogo 风格） -->
      <div class="feature-icon relative z-10 mb-4 flex h-10 w-10 items-center justify-center rounded-xl overflow-hidden">
        <span class="feature-icon__grid absolute inset-0 pointer-events-none"></span>
        <component :is="icon" class="relative h-5 w-5 text-white" />
      </div>
      
      <!-- 文字内容 -->
      <h3 class="relative z-10 mb-2 text-base font-semibold text-gray-900 group-hover:text-gray-950 dark:text-white/90 dark:group-hover:text-white transition-colors duration-300">{{ title }}</h3>
      <p class="relative z-10 text-sm leading-relaxed text-gray-500 group-hover:text-gray-700 dark:text-white/40 dark:group-hover:text-white/60 transition-colors duration-300">{{ desc }}</p>
    </div>
  </div>
</template>

<style scoped>
.feature-card-inner {
  background: #ffffff;
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
}
:root.dark .feature-card-inner {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  border-top-color: rgba(255,255,255,0.15);
  border-bottom-color: rgba(255,255,255,0.03);
  box-shadow: none;
}

.feature-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
}

.feature-card:hover .feature-card-inner {
  background: rgba(255,255,255,0.9);
  border-color: rgb(var(--accent-rgb) / 0.4);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01), 0 0 0 1px rgb(var(--accent-rgb) / 0.2);
}
:root.dark .feature-card:hover .feature-card-inner {
  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.08);
  border-top-color: rgba(255,255,255,0.15);
  border-bottom-color: rgba(255,255,255,0.03);
  box-shadow: none;
}

.feature-icon {
  background: linear-gradient(to bottom, rgb(var(--accent-rgb) / 0.9), rgb(var(--accent-strong-rgb) / 0.9));
  box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.12);
}

.feature-icon__grid {
  background-image:
    linear-gradient(to right, rgba(255, 255, 255, 0.06) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-size: 8px 8px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
}
</style>
