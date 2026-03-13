<script setup>
import { computed } from 'vue'
import {
  Listbox,
  ListboxButton,
  ListboxOptions,
  ListboxOption,
} from '@headlessui/vue'

const props = defineProps({
  statusLoading: { type: Boolean, default: true },
  statusError: { type: String, default: '' },
  statusPills: { type: Array, default: () => [] },
  providerOptions: { type: Array, default: () => [] },
  selectedModel: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:selectedModel'])

// 构建扁平模型列表，按 provider 分组
const modelOptions = computed(() => {
  const items = []
  for (const p of props.providerOptions) {
    if (!p.models || !p.models.length) continue
    // 添加分组标题
    items.push({ type: 'group', label: p.label, provider: p.value })
    for (const model of p.models) {
      items.push({
        type: 'model',
        provider: p.value,
        providerLabel: p.label,
        model,
        configured: p.configured,
        isDefault: model === p.default_model,
      })
    }
  }
  return items
})

const selectedLabel = computed(() => {
  return props.selectedModel || '选择模型'
})
</script>

<template>
  <div
    class="relative z-20 mb-8 flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200/60 bg-white/40 px-5 py-4 text-sm shadow-sm backdrop-blur-xl transition-colors dark:border-white/10 dark:bg-[#0A0A0F]/60"
  >
    <div class="flex items-center gap-2 font-mono text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
      <i class="fa-solid fa-server"></i> 系统状态
    </div>

    <!-- 加载中 -->
    <span
      v-if="statusLoading"
      class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-100/50 px-3 py-1.5 text-xs font-semibold text-slate-600 dark:border-white/5 dark:bg-white/5 dark:text-slate-300"
    >
      <span class="relative flex h-2.5 w-2.5">
        <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75"></span>
        <span class="relative inline-flex h-2.5 w-2.5 rounded-full bg-blue-500"></span>
      </span>
      神经元连接中...
    </span>

    <!-- 错误 -->
    <span
      v-else-if="statusError"
      class="inline-flex items-center gap-2 rounded-full border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 shadow-[0_0_10px_rgba(225,29,72,0.1)] dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300"
    >
      <i class="fa-solid fa-triangle-exclamation animate-pulse"></i>
      {{ statusError }}
    </span>

    <!-- 正常 Pills -->
    <span
      v-else
      v-for="p in statusPills"
      :key="p.key"
      class="inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-bold tracking-wide shadow-sm transition-all"
      :class="
        p.ok
          ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-400 dark:shadow-[0_0_10px_rgba(16,185,129,0.1)]'
          : 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-400'
      "
    >
      <i class="fa-solid" :class="p.ok ? 'fa-check-circle' : 'fa-xmark-circle'"></i>
      {{ p.label }}
    </span>

    <!-- 模型下拉选择器 (按 provider 分组) -->
    <div v-if="!statusLoading && !statusError" class="ml-auto flex items-center gap-2">
      <Listbox :model-value="selectedModel" @update:model-value="(v) => emit('update:selectedModel', v)" :disabled="disabled">
        <div class="relative">
          <ListboxButton
            class="group relative flex w-full cursor-pointer items-center justify-between gap-3 rounded-xl border border-slate-200/80 bg-white/80 py-2 pl-4 pr-3 text-left text-xs font-bold text-slate-700 shadow-sm backdrop-blur-sm transition-all hover:border-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/10 dark:bg-slate-900/80 dark:text-indigo-100 dark:hover:border-indigo-500/50 dark:hover:shadow-[0_0_15px_rgba(99,102,241,0.2)]"
          >
            <div class="flex items-center gap-2">
              <i class="fa-solid fa-microchip text-blue-500 dark:text-indigo-400"></i>
              <span class="block max-w-[180px] truncate">{{ selectedLabel }}</span>
            </div>
            <i class="fa-solid fa-chevron-down text-[10px] text-slate-400 transition-transform group-hover:text-blue-500"></i>
          </ListboxButton>
          <transition
            leave-active-class="transition duration-100 ease-in"
            leave-from-class="opacity-100"
            leave-to-class="opacity-0"
          >
            <ListboxOptions
              class="absolute right-0 z-50 mt-2 max-h-72 w-64 overflow-auto rounded-xl border border-slate-200/80 bg-white/95 py-2 text-base shadow-xl backdrop-blur-xl focus:outline-none sm:text-sm dark:border-white/10 dark:bg-[#0A0A0F]/95"
            >
              <template v-for="(item, idx) in modelOptions" :key="idx">
                <!-- 分组标题 -->
                <li
                  v-if="item.type === 'group'"
                  class="select-none px-4 py-2 text-[10px] font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500"
                  :class="idx > 0 ? 'mt-1 border-t border-slate-100 pt-2 dark:border-white/5' : ''"
                >
                  {{ item.label }}
                </li>
                <!-- 模型选项 -->
                <ListboxOption
                  v-else
                  :value="item.model"
                  :disabled="!item.configured"
                  as="template"
                  v-slot="{ active, selected, disabled: optDisabled }"
                >
                  <li
                    class="relative cursor-pointer select-none py-2.5 pl-10 pr-4 transition-colors"
                    :class="[
                      active ? 'bg-blue-50 dark:bg-indigo-500/10' : '',
                      optDisabled ? 'opacity-40 cursor-not-allowed' : ''
                    ]"
                  >
                    <span
                      class="block truncate text-sm transition-colors"
                      :class="[selected ? 'font-bold text-blue-700 dark:text-indigo-300' : 'font-medium text-slate-700 dark:text-slate-300']"
                    >
                      {{ item.model }}
                      <span v-if="item.isDefault" class="ml-1 text-[10px] text-slate-400 dark:text-slate-500">默认</span>
                    </span>
                    <span
                      v-if="selected"
                      class="absolute inset-y-0 left-0 flex items-center pl-3 text-blue-600 dark:text-indigo-400"
                    >
                      <i class="fa-solid fa-check text-sm shadow-blue-500"></i>
                    </span>
                  </li>
                </ListboxOption>
              </template>
            </ListboxOptions>
          </transition>
        </div>
      </Listbox>
    </div>
  </div>
</template>
