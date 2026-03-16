<script setup>
import { computed, ref, watch, inject } from 'vue'
import {
  Listbox,
  ListboxButton,
  ListboxOptions,
  ListboxOption,
} from '@headlessui/vue'
import deepseekLogo from '../assets/deepseek.svg'
import ernieLogo from '../assets/ernie.svg'

const emit = defineEmits(['update:selectedModel'])
const pushToast = inject('pushToast')

const props = defineProps({
  statusLoading: { type: Boolean, default: true },
  statusError: { type: String, default: '' },
  statusPills: { type: Array, default: () => [] },
  providerOptions: { type: Array, default: () => [] },
  selectedModel: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

const modelLogos = { openai: deepseekLogo, anthropic: ernieLogo }

// 构建扁平模型列表，按 provider 分组
const modelOptions = computed(() => {
  const items = []
  for (const p of props.providerOptions) {
    if (!p.models || !p.models.length) continue
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

const selectedLabel = computed(() => props.selectedModel || '选择模型')

// 反查当前选中模型所属的 provider
const currentProvider = computed(() => {
  for (const p of props.providerOptions) {
    if (p.models && p.models.includes(props.selectedModel)) return p
  }
  return null
})

// ---- 模型检查状态 ----
const isChecking = ref(false)
const showResult = ref(true)

watch(() => props.selectedModel, () => {
  isChecking.value = true
  showResult.value = false

  if (pushToast) {
    pushToast('info', '正在检查模型状态...', 1000)
  }

  setTimeout(() => {
    isChecking.value = false
    showResult.value = true

    if (pushToast) {
      if (modelStatusError.value) {
        pushToast('error', modelStatusError.value, 3000)
      } else if (currentProvider.value) {
        pushToast('success', `${currentProvider.value.label} 状态验证成功`, 2000)
      }
    }
  }, 1000)
})

const modelStatusError = computed(() => {
  if (!showResult.value || !currentProvider.value) return ''
  if (!currentProvider.value.configured) return `${currentProvider.value.label} 未配置 API Key`
  if (currentProvider.value.key_valid === false) return `${currentProvider.value.label} API Key 验证失败`
  return ''
})
</script>

<template>
  <div
    class="relative z-20 flex flex-wrap items-center gap-4 py-2 text-sm transition-all shrink-0"
  >
    <div class="flex items-center gap-2.5">
      <div class="flex h-6 w-6 items-center justify-center rounded-lg border border-slate-300 bg-white text-blue-600 shadow-sm backdrop-blur-sm dark:border-white/10 dark:bg-white/5 dark:text-indigo-400">
        <i class="fa-solid fa-bolt-lightning text-[10px]"></i>
      </div>
      <span class="text-[11px] font-bold uppercase tracking-[0.15em] text-slate-600 dark:text-slate-400">
        引擎状态
      </span>
    </div>

    <!-- 分隔符 -->
    <div class="h-4 w-px bg-slate-200 dark:bg-white/10"></div>

    <!-- 全局系统错误 -->
    <span
      v-if="statusError"
      class="inline-flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50/80 px-3 py-1.5 text-[11px] font-bold text-rose-700 shadow-sm dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-400"
    >
      <i class="fa-solid fa-circle-exclamation animate-pulse"></i>
      {{ statusError }}
    </span>

    <!-- Pills -->
    <div v-if="!statusError" class="flex flex-wrap items-center gap-2.5">
      <span
        v-for="p in statusPills"
        :key="p.key"
        class="inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-[11px] font-bold transition-all duration-500 ease-in-out"
        :class="
          p.loading
            ? 'border-amber-200 bg-amber-50/80 text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-400'
            : p.isPlaceholder
              ? 'border-slate-200 bg-slate-50/50 text-slate-400 dark:border-white/5 dark:bg-white/5 dark:text-slate-500'
              : p.ok
                ? 'border-emerald-200 bg-emerald-50/80 text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-400 shadow-sm shadow-emerald-500/5'
                : 'border-rose-200 bg-rose-50/80 text-rose-700 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-400'
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

    <!-- 模型下拉选择器 (按 provider 分组) -->
    <div v-if="!statusLoading && !statusError" class="ml-auto flex items-center gap-2">
      <Listbox :model-value="selectedModel" @update:model-value="(v) => emit('update:selectedModel', v)" :disabled="disabled">
        <div class="relative">
          <ListboxButton
            class="group relative flex h-9 w-full cursor-pointer items-center justify-between gap-4 rounded-xl border border-slate-300 bg-white pl-3 pr-2 text-left shadow-sm backdrop-blur-sm transition-all hover:border-blue-400 hover:bg-slate-50 dark:border-white/5 dark:bg-white/5 dark:hover:border-indigo-500/20 dark:hover:bg-white/10"
            :disabled="disabled"
          >
            <div class="flex items-center gap-2.5">
              <div class="relative flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-blue-600 backdrop-blur-sm dark:border-white/10 dark:bg-white/5 dark:text-indigo-400">
                <Transition name="fade" mode="out-in">
                  <img
                    v-if="currentProvider && modelLogos[currentProvider.value]"
                    :key="currentProvider.value"
                    :src="modelLogos[currentProvider.value]"
                    class="h-3.5 w-3.5 object-contain"
                    alt=""
                  />
                  <i v-else key="default-bot" class="fa-solid fa-robot text-[10px]"></i>
                </Transition>
                <!-- 状态指示点 -->
                <div
                  v-if="currentProvider"
                  class="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full border border-white transition-all duration-500 ease-in-out dark:border-[#0A0A0F]"
                  :class="(!currentProvider.configured || currentProvider.key_valid === false) ? 'bg-rose-500' : 'bg-emerald-500'"
                ></div>
              </div>
              <span class="block max-w-[180px] truncate text-[11px] font-black tracking-tight text-slate-700 dark:text-slate-200">
                {{ selectedLabel }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <div class="relative h-2.5 w-2.5 shrink-0">
                <Transition name="icon-pop">
                  <i v-if="isChecking" key="checking" class="fa-solid fa-spinner animate-spin absolute inset-0 flex items-center justify-center text-[10px] text-blue-500 dark:text-indigo-400"></i>
                  <i v-else-if="currentProvider && (!currentProvider.configured || currentProvider.key_valid === false)" key="error" class="fa-solid fa-xmark absolute inset-0 flex items-center justify-center text-[10px] text-rose-500"></i>
                  <i v-else-if="currentProvider" key="ok" class="fa-solid fa-check absolute inset-0 flex items-center justify-center text-[10px] text-emerald-500"></i>
                </Transition>
              </div>
              <i class="fa-solid fa-chevron-down shrink-0 text-[10px] text-slate-400 transition-transform duration-300 group-aria-expanded:rotate-180"></i>
            </div>
          </ListboxButton>

          <Transition
            enter-active-class="transition duration-200 ease-out"
            enter-from-class="transform scale-95 opacity-0 -translate-y-2"
            enter-to-class="transform scale-100 opacity-100 translate-y-0"
            leave-active-class="transition duration-100 ease-in"
            leave-from-class="transform scale-100 opacity-100 translate-y-0"
            leave-to-class="transform scale-95 opacity-0 -translate-y-2"
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
                  <div class="flex items-center gap-2">
                    <img v-if="modelLogos[item.provider]" :src="modelLogos[item.provider]" class="h-3 w-3 object-contain opacity-60" alt="" />
                    {{ item.label }}
                  </div>
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
                      <i class="fa-solid fa-check text-sm"></i>
                    </span>
                  </li>
                </ListboxOption>
              </template>
            </ListboxOptions>
          </Transition>
        </div>
      </Listbox>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

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
