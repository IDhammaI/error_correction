<script setup>
/**
 * HomeDemo.vue
 * 落地页产品演示区
 */
import { ArrowRight, Sparkles, CheckCircle2, FileDown } from 'lucide-vue-next'
import BaseButton from '@/components/base/BaseButton.vue'
</script>

<template>
  <section id="demo" class="relative z-10 py-24 overflow-hidden bg-white dark:bg-transparent transition-colors duration-200">
    <!-- 顶部分割线 -->
    <div class="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-200 dark:via-white/[0.06] to-transparent transition-colors duration-200"></div>

    <div class="reveal max-w-5xl mx-auto px-4 sm:px-6 relative z-10">
      <div class="text-center mb-12">
        <h2 class="reveal text-3xl font-semibold tracking-tight mb-4">
          <span class="text-transparent bg-clip-text animate-gradient-sweep home-title-accent" style="
            background-size: 200% auto;
          ">眼见为实的转变</span>
          <span class="hidden" style="
            background-size: 200% auto;
          ">眼见为实的转变</span>
        </h2>
        <p class="text-gray-600 dark:text-white/40 text-sm transition-colors duration-200">复杂的公式、凌乱的涂改，在强大的 AI 引擎面前都不值一提。</p>
      </div>

      <div class="flex flex-col lg:flex-row gap-4 items-center justify-center">
        <!-- 左侧：原图模拟 -->
        <div class="reveal flex-1 w-full max-w-md bg-gray-50 border border-gray-200 dark:bg-transparent dark:border-none dark:brand-btn p-6 rounded-lg relative overflow-hidden transition-colors duration-200">
          <div class="text-xs font-medium tracking-wide text-gray-400 dark:text-white/25 uppercase mb-4 transition-colors duration-200">Input / 原生图像</div>
          <div class="bg-white border border-gray-100 shadow-sm dark:bg-[#15151e]/80 dark:border-white/[0.02] dark:shadow-none p-6 rounded-xl -rotate-1 text-gray-600 dark:text-white/50 transition-colors duration-200">
            <p class="font-[cursive] text-sm mb-2">3. 巳知函数f(x)=2sin(wx+φ)(w&gt;0,|φ|&lt;π/2)的图像...</p>
            <p class="font-[cursive] text-sm">A. w=2, φ=π/6</p>
            <div class="mt-3 w-1/2 h-3 bg-red-400/20 dark:bg-red-400/15 rounded-full blur-[2px] -rotate-3 transition-colors duration-200"></div>
            <p class="font-[cursive] text-xs mt-3 text-red-500/60 dark:text-red-400/40 font-bold -rotate-6 transition-colors duration-200">看不清，选C吧</p>
          </div>
        </div>

        <!-- 中间箭头 -->
        <div class="hidden lg:flex items-center justify-center w-12">
          <ArrowRight class="w-5 h-5 accent-text animate-pulse transition-colors duration-200" />
        </div>
        <div class="lg:hidden flex justify-center py-2">
          <ArrowRight class="w-5 h-5 accent-text rotate-90 animate-pulse transition-colors duration-200" />
        </div>

        <!-- 右侧：AI 结果 -->
        <div class="reveal flex-1 w-full max-w-md bg-[rgb(var(--accent-rgb)/0.08)] border accent-border dark:bg-transparent dark:border-none dark:brand-btn p-6 rounded-lg relative overflow-hidden text-left transition-colors duration-200" style="transition-delay: 200ms;">
          <div class="absolute top-0 right-0 w-32 h-32 bg-[rgb(var(--accent-rgb)/0.2)] dark:bg-[rgb(var(--accent-rgb)/0.1)] blur-[50px] rounded-full pointer-events-none transition-colors duration-200"></div>
          
          <div class="text-xs font-medium tracking-wide accent-text uppercase flex items-center gap-1.5 mb-4 relative z-10 transition-colors duration-200">
            <Sparkles class="w-3 h-3" /> Output / 结构化数据
          </div>

          <div class="bg-white border accent-border shadow-sm dark:bg-[#0A0A0F]/80 dark:border-white/[0.04] dark:shadow-inner p-4 rounded-xl text-gray-700 dark:text-white/70 font-mono text-sm leading-relaxed relative z-10 transition-colors duration-200">
            <div class="flex gap-2 mb-4">
              <span class="accent-bg-soft accent-text border accent-border px-2 py-0.5 rounded-full text-xs transition-colors duration-200">选择题</span>
              <span class="accent-bg-soft accent-text border accent-border px-2 py-0.5 rounded-full text-xs transition-colors duration-200">三角函数</span>
            </div>
            <p class="text-sm"><span class="accent-text mr-1.5 transition-colors duration-200">## 3.</span> 已知函数 <span class="accent-text accent-bg-soft px-1 rounded transition-colors duration-200">$f(x) = 2\sin(\omega x + \varphi)$</span> <span class="accent-text accent-bg-soft px-1 rounded transition-colors duration-200">$(\omega &gt; 0, |\varphi| &lt; \frac{\pi}{2})$</span> 的图像...</p>
            <div class="mt-4 pl-3 border-l border-gray-200 dark:border-white/[0.06] space-y-2 transition-colors duration-200">
              <p class="flex gap-2"><span class="text-gray-400 dark:text-white/25 transition-colors duration-200">A.</span> <span class="text-gray-700 dark:text-white/60 transition-colors duration-200">$\omega = 2, \varphi = \frac{\pi}{6}$</span></p>
              <p class="flex gap-2"><span class="text-gray-400 dark:text-white/25 transition-colors duration-200">B.</span> <span class="text-gray-700 dark:text-white/60 transition-colors duration-200">$\omega = 2, \varphi = -\frac{\pi}{6}$</span></p>
            </div>
            <div class="mt-6 flex items-center justify-between border-t border-gray-100 dark:border-white/[0.06] pt-4 transition-colors duration-200">
              <span class="text-xs text-emerald-600/80 dark:text-emerald-400/70 flex items-center gap-1.5 transition-colors duration-200">
                <CheckCircle2 class="w-3 h-3" /> 已过滤手写痕迹
              </span>
              <BaseButton variant="secondary" size="sm" class="flex items-center gap-1.5 !px-3 !py-1.5 !h-auto">
                导出 MD <FileDown class="w-3 h-3" />
              </BaseButton>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
