<script setup>
/**
 * HomeFooter.vue
 * 落地页底部行动号召区
 */
import BaseButton from '@/components/base/BaseButton.vue'
</script>

<template>
  <section id="cta" class="relative z-10 flex flex-col items-center justify-center py-32 px-6 overflow-hidden min-h-[70vh] bg-slate-50 dark:bg-transparent transition-colors duration-200">
    <!-- 底部中心光晕 -->
    <div class="absolute bottom-0 left-1/2 -translate-x-1/2 w-[80vw] h-[50vh] pointer-events-none z-0">
      <div class="absolute inset-0 bg-[rgb(var(--accent-rgb)/0.2)] dark:bg-[rgb(var(--accent-rgb)/0.1)] blur-[120px] rounded-[100%] transform translate-y-1/2 transition-colors duration-200"></div>
      <div class="absolute inset-0 bg-[rgb(var(--accent-hover-rgb)/0.1)] dark:bg-[rgb(var(--accent-hover-rgb)/0.05)] blur-[150px] rounded-[100%] transform translate-y-1/2 scale-150 transition-colors duration-200"></div>
    </div>

    <!-- CTA -->
    <div class="flex-1 flex flex-col items-center justify-center text-center relative z-10 w-full">
      <h2 class="reveal text-4xl sm:text-5xl font-semibold tracking-tight mb-6">
        <span class="text-transparent bg-clip-text animate-gradient-sweep home-title-accent" style="
          background-size: 200% auto;
        ">即刻开启高效学习模式</span>
        <span class="hidden" style="
          background-size: 200% auto;
        ">即刻开启高效学习模式</span>
      </h2>
      <p class="reveal text-gray-600 dark:text-white/40 text-base mb-10 max-w-md mx-auto leading-relaxed transition-colors duration-200">告别低效抄录，让 AI 成为你的超级助教。注册即享完整试卷解析体验。</p>
      <div class="reveal">
        <BaseButton variant="cta" to="/auth" class="shadow-[0_0_30px_rgb(var(--accent-rgb)/0.3)] hover:shadow-[0_0_50px_rgb(var(--accent-rgb)/0.5)] transform hover:-translate-y-1 transition-all duration-300">
          免费创建错题库
        </BaseButton>
      </div>
    </div>
  </section>
</template>
