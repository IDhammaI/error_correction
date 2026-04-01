<script setup>
import LandingButton from './LandingButton.vue'
</script>

<template>
  <section id="cta" class="relative z-10 min-h-screen flex flex-col justify-between py-16 px-6 bg-[#0A0A0F]">
    <!-- CTA -->
    <div class="flex-1 flex flex-col items-center justify-center text-center">
      <h2 class="text-3xl font-semibold mb-4 text-white/90">即刻开启高效学习模式</h2>
      <p class="text-white/40 text-sm mb-8 max-w-md mx-auto">告别低效抄录，让 AI 成为你的超级助教。注册即享完整试卷解析体验。</p>
      <LandingButton variant="cta" to="/auth">
        免费创建错题库
      </LandingButton>
    </div>

    <!-- Footer -->
    <div class="border-t border-white/[0.06] pt-6">
      <div class="flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-white/25">
        <div class="flex items-center gap-2">
          <div class="bg-white/[0.04] border border-white/[0.06] p-1.5 rounded-lg">
            <img src="/logo.svg" class="w-4 h-4 brightness-0 invert opacity-50" alt="logo" />
          </div>
          <span class="font-semibold text-white/40">智卷错题本</span>
        </div>
        <p>© 2026 Intelligent Error Book Generation System. All rights reserved.</p>
        <div class="flex gap-6">
          <a href="#" class="hover:text-white/60 transition-colors">架构文档</a>
          <a href="#" class="hover:text-white/60 transition-colors">隐私政策</a>
          <a href="#" class="hover:text-white/60 transition-colors">联系我们</a>
        </div>
      </div>
    </div>
  </section>
</template>
