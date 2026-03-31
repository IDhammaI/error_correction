<script setup>
import { ArrowRight, Sparkles, CheckCircle2, FileDown } from 'lucide-vue-next'
</script>

<template>
  <section id="demo" class="relative z-10 py-24 bg-[#0A0A0F]">
    <div class="reveal max-w-5xl mx-auto px-4 sm:px-6">
      <div class="text-center mb-12">
        <h2 class="text-2xl font-semibold mb-4 text-white/90">眼见为实的转变</h2>
        <p class="text-white/40 text-sm">复杂的公式、凌乱的涂改，在强大的 AI 引擎面前都不值一提。</p>
      </div>

      <div class="flex flex-col lg:flex-row gap-4 items-center justify-center">
        <!-- 左侧：原图模拟 -->
        <div class="reveal flex-1 w-full max-w-md border border-white/[0.06] bg-[#111118] p-6 rounded-lg relative overflow-hidden">
          <div class="text-xs font-medium tracking-wide text-white/25 uppercase mb-4">Input / 原生图像</div>
          <div class="bg-[#1a1a22] p-6 rounded-lg -rotate-1 text-white/50">
            <p class="font-[cursive] text-sm mb-2">3. 巳知函数f(x)=2sin(wx+φ)(w&gt;0,|φ|&lt;π/2)的图像...</p>
            <p class="font-[cursive] text-sm">A. w=2, φ=π/6</p>
            <div class="mt-3 w-1/2 h-3 bg-red-400/15 rounded-full blur-[2px] -rotate-3"></div>
            <p class="font-[cursive] text-xs mt-3 text-red-400/40 font-bold -rotate-6">看不清，选C吧</p>
          </div>
        </div>

        <!-- 中间箭头 -->
        <div class="hidden lg:flex items-center justify-center w-12">
          <ArrowRight class="w-5 h-5 text-white/25" />
        </div>
        <div class="lg:hidden flex justify-center py-2">
          <ArrowRight class="w-5 h-5 text-white/25 rotate-90" />
        </div>

        <!-- 右侧：AI 结果 -->
        <div class="reveal flex-1 w-full max-w-md border border-white/[0.06] bg-[#111118] p-6 rounded-lg relative overflow-hidden text-left" style="transition-delay: 200ms;">
          <div class="text-xs font-medium tracking-wide text-indigo-400/70 uppercase flex items-center gap-1.5 mb-4">
            <Sparkles class="w-3 h-3" /> Output / 结构化数据
          </div>

          <div class="bg-[#0A0A0F] border border-white/[0.06] p-4 rounded-lg text-white/70 font-mono text-sm leading-relaxed">
            <div class="flex gap-2 mb-4">
              <span class="bg-white/[0.04] text-white/50 px-2 py-0.5 rounded-full text-xs border border-white/[0.06]">选择题</span>
              <span class="bg-white/[0.04] text-white/50 px-2 py-0.5 rounded-full text-xs border border-white/[0.06]">三角函数</span>
            </div>
            <p class="text-sm"><span class="text-indigo-400/70 mr-1.5">## 3.</span> 已知函数 <span class="text-indigo-300/80 bg-indigo-500/10 px-1 rounded">$f(x) = 2\sin(\omega x + \varphi)$</span> <span class="text-indigo-300/80 bg-indigo-500/10 px-1 rounded">$(\omega &gt; 0, |\varphi| &lt; \frac{\pi}{2})$</span> 的图像...</p>
            <div class="mt-4 pl-3 border-l border-white/[0.06] space-y-2">
              <p class="flex gap-2"><span class="text-white/25">A.</span> <span class="text-white/60">$\omega = 2, \varphi = \frac{\pi}{6}$</span></p>
              <p class="flex gap-2"><span class="text-white/25">B.</span> <span class="text-white/60">$\omega = 2, \varphi = -\frac{\pi}{6}$</span></p>
            </div>
            <div class="mt-6 flex items-center justify-between border-t border-white/[0.06] pt-4">
              <span class="text-xs text-emerald-400/70 flex items-center gap-1.5">
                <CheckCircle2 class="w-3 h-3" /> 已过滤手写痕迹
              </span>
              <button class="text-xs bg-white/[0.06] text-white/60 hover:bg-white/[0.1] px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors border border-white/[0.06]">
                导出 MD <FileDown class="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
