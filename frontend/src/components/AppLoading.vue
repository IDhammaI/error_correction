<script setup>
defineProps({
  visible: { type: Boolean, default: true },
})
const emit = defineEmits(['after-enter'])
</script>

<template>
  <Transition name="loading-fade" @after-enter="emit('after-enter')">
    <div v-if="visible" class="fixed inset-0 z-[200] flex flex-col items-center justify-center gap-8 bg-gray-50 dark:bg-[#0A0A0F]">
      <div class="relative">
        <div class="absolute inset-0 rounded-2xl bg-indigo-500/40 blur-xl"></div>
        <div class="relative bg-gradient-to-br from-indigo-500 to-indigo-700 p-4 rounded-2xl shadow-md border border-black/10 dark:border-white/10">
          <img src="/logo.svg" class="w-8 h-8" alt="logo" />
        </div>
      </div>
      <div class="w-48">
        <div class="h-0.5 w-full rounded-full bg-black/10 dark:bg-white/10 overflow-hidden">
          <div class="h-full rounded-full bg-gradient-to-r from-indigo-500 to-blue-400 loading-bar"></div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.loading-fade-enter-active {
  transition: opacity 0.25s ease;
}
.loading-fade-leave-active {
  transition: opacity 0.4s ease;
}
.loading-fade-enter-from,
.loading-fade-leave-to {
  opacity: 0;
}

.loading-bar {
  animation: loadProgress 1.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}
@keyframes loadProgress {
  from { width: 0%; }
  to   { width: 100%; }
}
</style>
