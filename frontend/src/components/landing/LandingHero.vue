<script setup>
import { UploadCloud, ArrowRight } from 'lucide-vue-next'

const emit = defineEmits(['scrollToSection'])
</script>

<template>
  <!-- ① Sticky Hero 容器 — Linear 风格 -->
  <div id="sticky-hero" class="sticky top-0 h-screen overflow-hidden z-0 flex flex-col justify-center bg-[#0A0A0F]">

    <!-- 顶部装饰椭圆 — 用 vw 统一大小和位置的缩放基准 -->
    <div class="absolute pointer-events-none z-0" style="
      top: -90vw;
      left: 50%;
      transform: translateX(-50%);
      width: 140vw;
      aspect-ratio: 1.3 / 1;
      border-radius: 50%;
      background: linear-gradient(to bottom, rgba(92,81,148,0.5), rgba(47,40,91,0.95));
      box-shadow:
        inset 0 -20px 24px 0 rgba(255,255,255,0.15),
        0 16px 32px 0 rgba(97,62,210,0.32),
        inset 0 -1px 0 0 rgba(129,115,223,0.6);
    "></div>

    <!-- 装饰: 点阵网格 -->
    <div class="absolute inset-0 pointer-events-none z-0 opacity-[0.03]"
      style="background-image: radial-gradient(circle, rgba(255,255,255,0.8) 1px, transparent 1px); background-size: 32px 32px;"
    ></div>

    <!-- 装饰: 光斑 -->
    <div class="absolute pointer-events-none z-0 w-80 h-80 rounded-full blur-[120px] bg-indigo-600/[0.07]"
      style="top: 25%; left: 8%;"
    ></div>
    <div class="absolute pointer-events-none z-0 w-64 h-64 rounded-full blur-[100px] bg-violet-500/[0.05]"
      style="top: 55%; right: 10%;"
    ></div>

    <!-- 首屏区块 — 居中布局 -->
    <section id="hero" class="relative w-full px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto z-10">
      <div class="text-center">
        <!-- 标签 -->
        <div class="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs font-medium text-white/50">
          <span class="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          PaddleOCR + LangChain Agent
        </div>

        <h1 class="text-4xl sm:text-5xl font-semibold tracking-tight leading-tight mb-6 text-white">
          重塑错题整理<br />
          <span class="text-white/40">一键生成知识图谱</span>
        </h1>

        <p class="text-base text-white/40 mb-8 max-w-lg mx-auto leading-relaxed">
          上传试卷或手写笔记，AI 自动完成 OCR 识别、题目分割、公式还原、知识点标注。
        </p>

        <div class="flex gap-3 justify-center">
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
