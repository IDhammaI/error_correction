<script setup>
import { ArrowRight, Sparkles, CheckCircle2, FileDown } from 'lucide-vue-next'
</script>

<template>
  <!-- 效果对比区 -->
  <section id="demo" class="relative z-10 min-h-screen flex flex-col justify-center py-24 overflow-hidden">
    <!-- 顶部过渡遮罩 -->
    <div class="pointer-events-none absolute inset-x-0 top-0 h-32 z-10 bg-gradient-to-b from-slate-950 to-transparent"></div>
    <!-- 装饰光晕 -->
    <div class="pointer-events-none absolute inset-0 z-0">
      <div class="absolute bottom-[-10%] right-[-5%] h-[500px] w-[500px] rounded-full bg-blue-400/20 dark:bg-indigo-500/10 blur-[130px]"></div>
      <div class="absolute inset-0 opacity-[0.04]" style="background-image: linear-gradient(rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.6) 1px, transparent 1px); background-size: 40px 40px;"></div>
    </div>
    <div class="reveal relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-16">
        <h2 class="text-3xl md:text-4xl font-bold mb-6 text-white">眼见为实的 <span class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-300 to-cyan-300">魔法转变</span></h2>
        <p class="text-slate-400 text-base">复杂的公式、凌乱的涂改，在强大的 AI 引擎面前都不值一提。</p>
      </div>

      <div class="flex flex-col lg:flex-row gap-6 items-center justify-center">
        <!-- 左侧：原图模拟 -->
        <div class="reveal flex-1 w-full max-w-md bg-white/8 backdrop-blur-md border border-white/12 p-6 md:p-10 rounded-3xl relative overflow-hidden group">
          <div class="absolute top-5 left-6 text-xs font-bold tracking-widest text-slate-400 uppercase">Input / 原生图像</div>
          <div class="bg-white dark:bg-[#EAEAEA] p-8 rounded-xl transform -rotate-2 opacity-90 dark:opacity-80 mt-8 blur-[0.5px] text-slate-800 shadow-sm dark:shadow-inner filter dark:sepia-[0.2] relative">
            <div class="hidden dark:block absolute inset-0 bg-[url(&quot;data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E&quot;)] opacity-40 mix-blend-multiply"></div>
            <p class="font-[cursive] text-base mb-3">3. 巳知函数f(x)=2sin(wx+φ)(w&gt;0,|φ|&lt;π/2)的图像...</p>
            <p class="font-[cursive] text-base">A. w=2, φ=π/6</p>
            <div class="mt-4 w-1/2 h-4 bg-red-400/30 dark:bg-red-400/20 rounded-full blur-[2px] transform -rotate-3"></div>
            <p class="font-[cursive] text-sm mt-4 text-red-500 dark:text-red-600/60 font-bold transform -rotate-6">看不清，选C吧</p>
          </div>
        </div>

        <!-- 中间发光箭头 -->
        <div class="hidden lg:flex items-center justify-center relative w-20">
          <div class="absolute inset-0 bg-blue-500/10 dark:bg-indigo-500/20 blur-xl rounded-full animate-pulse"></div>
          <ArrowRight class="w-10 h-10 text-blue-500 dark:text-indigo-400 relative z-10" />
        </div>
        <div class="lg:hidden flex justify-center py-4">
          <ArrowRight class="w-8 h-8 text-blue-500 dark:text-indigo-400 rotate-90" />
        </div>

        <!-- 右侧：AI 结果 -->
        <div class="reveal flex-1 w-full max-w-md bg-white/8 backdrop-blur-md border border-indigo-400/25 p-6 md:p-10 rounded-3xl relative overflow-hidden text-left group transition-shadow duration-500" style="transition-delay: 200ms;">
          <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-indigo-500 dark:from-cyan-500 dark:via-indigo-500 dark:to-indigo-500"></div>
          <div class="absolute top-5 left-6 text-xs font-bold tracking-widest text-blue-400 dark:text-indigo-400 uppercase flex items-center gap-2">
            <Sparkles class="w-3 h-3" /> Output / 结构化数据
          </div>

          <div class="mt-10 bg-black/20 border border-white/10 p-6 rounded-xl text-slate-200 font-mono text-sm leading-relaxed relative">
            <div class="flex gap-2 mb-5">
              <span class="bg-blue-500/20 dark:bg-cyan-500/10 text-blue-400 dark:text-cyan-400 px-3 py-1 rounded-full text-xs border border-blue-500/30 dark:border-cyan-500/20">选择题</span>
              <span class="bg-indigo-500/20 dark:bg-indigo-500/10 text-indigo-400 px-3 py-1 rounded-full text-xs border border-indigo-500/30 dark:border-indigo-500/20">三角函数</span>
            </div>
            <p class="text-base"><span class="text-blue-500 dark:text-indigo-500 mr-2">## 3.</span> 已知函数 <span class="text-indigo-300 dark:text-indigo-300 bg-indigo-500/20 dark:bg-indigo-500/10 px-1 rounded">$f(x) = 2\sin(\omega x + \varphi)$</span> <span class="text-indigo-300 dark:text-indigo-300 bg-indigo-500/20 dark:bg-indigo-500/10 px-1 rounded">$(\omega &gt; 0, |\varphi| &lt; \frac{\pi}{2})$</span> 的图像...</p>
            <div class="mt-5 pl-4 border-l-2 border-blue-500/50 dark:border-indigo-500/50 space-y-3">
              <p class="flex gap-3"><span class="text-slate-400 dark:text-slate-500">A.</span> <span class="text-slate-200 dark:text-slate-300">$\omega = 2, \varphi = \frac{\pi}{6}$</span></p>
              <p class="flex gap-3"><span class="text-slate-400 dark:text-slate-500">B.</span> <span class="text-slate-200 dark:text-slate-300">$\omega = 2, \varphi = -\frac{\pi}{6}$</span></p>
            </div>
            <div class="mt-8 flex items-center justify-between border-t border-slate-700 dark:border-white/10 pt-5">
              <span class="text-xs text-emerald-400 flex items-center gap-1.5 bg-emerald-400/10 px-2 py-1 rounded">
                <CheckCircle2 class="w-3 h-3" /> 已过滤手写痕迹
              </span>
              <button class="text-xs bg-white text-slate-900 hover:bg-slate-200 dark:bg-indigo-500 dark:hover:bg-indigo-400 dark:text-white px-4 py-2 rounded-lg flex items-center gap-2">
                导出 MD <FileDown class="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
