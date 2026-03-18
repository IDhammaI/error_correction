<script setup>
</script>

<template>
  <!-- CTA + Footer section -->
  <section id="cta" class="relative z-10 min-h-screen flex flex-col justify-between py-16 px-8 overflow-hidden bg-gradient-to-br from-blue-600 via-indigo-600 to-indigo-700 dark:from-indigo-950 dark:via-[#0A0A0F] dark:to-slate-950">
    <!-- 装饰光晕 -->
    <div class="pointer-events-none absolute inset-0 z-0">
      <div class="absolute top-[-15%] left-[-8%] h-[500px] w-[500px] rounded-full bg-blue-400/20 dark:bg-indigo-500/10 blur-[130px]"></div>
      <div class="absolute bottom-[-10%] right-[-5%] h-[400px] w-[400px] rounded-full bg-indigo-300/20 dark:bg-blue-600/10 blur-[100px]"></div>
      <div class="absolute inset-0 opacity-[0.04]" style="background-image: linear-gradient(rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.6) 1px, transparent 1px); background-size: 40px 40px;"></div>
    </div>

    <!-- CTA -->
    <div class="relative z-10 flex-1 flex flex-col items-center justify-center text-center">
      <h2 class="text-4xl font-extrabold mb-6 text-white">即刻开启高效学习模式</h2>
      <p class="text-blue-100/80 text-lg mb-10 max-w-xl mx-auto">告别低效抄录，让 AI 成为你的超级助教。注册即享完整试卷解析体验。</p>
      <RouterLink to="/auth" class="relative inline-flex group h-12">
        <div class="absolute -inset-px bg-gradient-to-r from-blue-400 via-indigo-400 to-blue-500 rounded-full blur-lg opacity-0 group-hover:opacity-80 transition-opacity duration-500"></div>
        <span class="relative inline-flex items-center px-8 py-3 text-sm font-bold text-white bg-white/15 hover:bg-white/25 border border-white/30 rounded-full backdrop-blur-md transition-all">
          免费创建错题库
        </span>
      </RouterLink>
    </div>

    <!-- Footer -->
    <div class="relative z-10 border-t border-white/10 pt-6">
      <div class="flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-blue-100/40">
        <div class="flex items-center gap-2">
          <div class="bg-white/15 border border-white/20 p-1.5 rounded-xl">
            <img src="/logo.svg" class="w-4 h-4 brightness-0 invert" alt="logo" />
          </div>
          <span class="font-bold text-white/60">智卷错题本</span>
        </div>
        <p>© 2026 Intelligent Error Book Generation System. All rights reserved.</p>
        <div class="flex gap-6 font-medium">
          <a href="#" class="hover:text-white transition-colors">架构文档</a>
          <a href="#" class="hover:text-white transition-colors">隐私政策</a>
          <a href="#" class="hover:text-white transition-colors">联系我们</a>
        </div>
      </div>
    </div>
  </section>
</template>
