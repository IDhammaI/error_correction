<script setup>
/**
 * WorkspaceLoading.vue
 * 工作台初始加载动画（品牌 Logo + 进度条）
 */
import BrandLogo from '@/components/base/BrandLogo.vue'

defineProps({
  loading: Boolean,
})
</script>

<template>
  <Transition name="ws-loading-fade">
    <div v-if="loading" class="fixed inset-0 z-[200] flex flex-col items-center justify-center gap-8 bg-[#0A0A0F]">
      <BrandLogo size="lg" breathe />
      <div class="w-48">
        <div class="h-0.5 w-full rounded-full bg-white/10 overflow-hidden">
          <div class="h-full rounded-full ws-loading-bar" style="background: linear-gradient(to right, rgba(129,115,223,0.8), rgba(99,87,199,0.8));"></div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style>
.ws-loading-fade-leave-active { transition: opacity 0.4s ease; }
.ws-loading-fade-leave-to { opacity: 0; }
.ws-loading-bar {
  animation: wsLoadProgress 2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}
@keyframes wsLoadProgress {
  from { width: 0%; }
  to   { width: 100%; }
}
</style>
