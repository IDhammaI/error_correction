<script setup>
import ModelProviderSelect from '@/components/workspace/ModelProviderSelect.vue'

const emit = defineEmits(['update:selectedLlmOptionId'])

defineProps({
  statusLoading: { type: Boolean, default: true },
  statusError: { type: String, default: '' },
  statusPills: { type: Array, default: () => [] },
  modelOptionsData: { type: Object, default: null },
  selectedLlmOptionId: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  noModels: { type: Boolean, default: false },
})
</script>

<template>
  <div class="relative z-20 flex shrink-0 flex-wrap items-center gap-4 text-sm">
    <div class="flex items-center gap-2.5">
      <span class="text-xs font-medium uppercase tracking-[0.15em] text-gray-500 transition-colors dark:text-[#62666d]">
        引擎状态
      </span>
    </div>

    <div class="h-4 w-px bg-gray-300 transition-colors dark:bg-white/[0.08]"></div>

    <span
      v-if="statusError"
      class="inline-flex items-center gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-1.5 text-xs font-medium text-rose-500 transition-colors dark:text-rose-400"
    >
      <i class="fa-solid fa-circle-exclamation animate-pulse"></i>
      {{ statusError }}
    </span>

    <div v-if="!statusError" class="flex flex-wrap items-center gap-2.5">
      <span
        v-for="p in statusPills"
        :key="p.key"
        class="inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors"
        :class="p.loading
          ? 'border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-400'
          : p.isPlaceholder
            ? 'border-gray-200 bg-gray-100 text-gray-500 dark:border-white/[0.05] dark:bg-white/[0.03] dark:text-[#62666d]'
            : p.ok
              ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
              : 'border-rose-500/20 bg-rose-500/10 text-rose-500 dark:text-rose-400'
        "
      >
        <div class="relative h-2.5 w-2.5 shrink-0">
          <Transition name="icon-pop">
            <i
              :key="p.loading ? 'loading' : p.isPlaceholder ? 'placeholder' : p.ok ? 'ok' : 'error'"
              class="fa-solid absolute inset-0 flex items-center justify-center text-[10px]"
              :class="p.loading ? 'fa-spinner animate-spin' : p.isPlaceholder ? 'fa-hourglass-start' : p.ok ? 'fa-check' : 'fa-xmark'"
            ></i>
          </Transition>
        </div>
        {{ p.label }}
      </span>
    </div>

    <div v-if="!statusError" class="ml-auto flex items-center gap-2">
      <ModelProviderSelect
        :model-value="selectedLlmOptionId"
        :model-options-data="modelOptionsData"
        :disabled="disabled"
        :no-models="noModels"
        :status-loading="statusLoading"
        @update:model-value="(value) => emit('update:selectedLlmOptionId', value)"
      />
    </div>
  </div>
</template>

<style scoped>
.icon-pop-enter-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.icon-pop-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.icon-pop-enter-from {
  opacity: 0;
  transform: scale(0.3) rotate(-180deg);
}

.icon-pop-leave-to {
  opacity: 0;
  transform: scale(0.3) rotate(180deg);
}
</style>
