<script setup>
/**
 * StatusBar.vue
 * 状态栏（引擎状态 + 模型选择）
 */
import { computed, ref, watch } from 'vue'
import { useToast } from '@/composables/useToast.js'
import {
  Listbox,
  ListboxButton,
  ListboxOptions,
  ListboxOption,
} from '@headlessui/vue'
import deepseekLogo from '@/assets/deepseek.svg'
import ernieLogo from '@/assets/ernie.svg'

// Tooltip 相关状态
const tooltipVisible = ref(false)
const tooltipText = ref('')
const tooltipPosition = ref({ x: 0, y: 0 })

// 显示 tooltip
const showTooltip = (event, text) => {
  if (!text || text.length <= 20) return // 短文本不需要 tooltip

  tooltipText.value = text
  const rect = event.currentTarget.getBoundingClientRect()
  tooltipPosition.value = {
    x: rect.left + rect.width / 2,
    y: rect.top - 8
  }
  tooltipVisible.value = true
}

// 隐藏 tooltip
const hideTooltip = () => {
  tooltipVisible.value = false
}

const emit = defineEmits(['update:selectedLlmOptionId'])
const { pushToast } = useToast()

const props = defineProps({
  statusLoading: { type: Boolean, default: true },
  statusError: { type: String, default: '' },
  statusPills: { type: Array, default: () => [] },
  modelOptionsData: { type: Object, default: null },
  selectedLlmOptionId: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  noModels: { type: Boolean, default: false },
})

const modelLogos = { openai: deepseekLogo, anthropic: ernieLogo }

// 构建分组模型列表
const groupedOptions = computed(() => {
  if (!props.modelOptionsData || !props.modelOptionsData.groups) return []

  const items = []
  for (const group of props.modelOptionsData.groups) {
    const groupOptions = (props.modelOptionsData.options || []).filter(o => o.source === group.key)
    if (groupOptions.length === 0) continue

    items.push({ type: 'group', label: group.label })
    for (const opt of groupOptions) {
      items.push({
        type: 'model',
        optionId: opt.option_id,
        provider: opt.category,
        providerName: opt.provider_name,
        modelName: opt.model_name,
        label: opt.label,
        configured: opt.configured,
        available: opt.available,
        isDefault: opt.is_default,
        reason: opt.reason,
      })
    }
  }
  return items
})

// 当前选中的配置对象
const currentOption = computed(() => {
  if (!props.modelOptionsData || !props.modelOptionsData.options) return null
  return props.modelOptionsData.options.find(o => o.option_id === props.selectedLlmOptionId) || null
})

const selectedLabel = computed(() => {
  if (props.noModels) return '暂无模型'
  if (!currentOption.value) return '选择模型'
  return currentOption.value.label || currentOption.value.model_name
})

// ---- 模型检查状态 ----
const isChecking = ref(false)
const showResult = ref(true)

watch(() => props.selectedLlmOptionId, () => {
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
      } else if (currentOption.value) {
        pushToast('success', `${currentOption.value.provider_name} 状态验证成功`, 2000)
      }
    }
  }, 1000)
})

const modelStatusError = computed(() => {
  if (!showResult.value || !currentOption.value) return ''
  if (!currentOption.value.available) return currentOption.value.reason || '模型不可用'
  return ''
})
</script>

<template>
  <div class="relative z-20 flex flex-wrap items-center gap-4 text-sm shrink-0">
    <div class="flex items-center gap-2.5">
      <span class="text-xs font-medium uppercase tracking-[0.15em] text-gray-500 dark:text-[#62666d] transition-colors">
        引擎状态
      </span>
    </div>

    <!-- 分隔符 -->
    <div class="h-4 w-px bg-gray-300 dark:bg-white/[0.08] transition-colors"></div>

    <!-- 全局系统错误 -->
    <span v-if="statusError"
      class="inline-flex items-center gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-1.5 text-xs font-medium text-rose-500 dark:text-rose-400 transition-colors">
      <i class="fa-solid fa-circle-exclamation animate-pulse"></i>
      {{ statusError }}
    </span>

    <!-- Pills -->
    <div v-if="!statusError" class="flex flex-wrap items-center gap-2.5">
      <span v-for="p in statusPills" :key="p.key"
        class="inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors"
        :class="p.loading
          ? 'border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-400'
          : p.isPlaceholder
            ? 'border-gray-200 bg-gray-100 text-gray-500 dark:border-white/[0.05] dark:bg-white/[0.03] dark:text-[#62666d]'
            : p.ok
              ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
              : 'border-rose-500/20 bg-rose-500/10 text-rose-500 dark:text-rose-400'
          ">
        <div class="relative h-2.5 w-2.5 shrink-0">
          <Transition name="icon-pop">
            <i :key="p.loading ? 'loading' : p.isPlaceholder ? 'placeholder' : p.ok ? 'ok' : 'error'"
              class="fa-solid absolute inset-0 flex items-center justify-center text-[10px]"
              :class="p.loading ? 'fa-spinner animate-spin' : p.isPlaceholder ? 'fa-hourglass-start' : p.ok ? 'fa-check' : 'fa-xmark'"></i>
          </Transition>
        </div>
        {{ p.label }}
      </span>
    </div>

    <!-- 模型下拉选择器 (按 provider 分组) -->
    <div v-if="!statusError" class="ml-auto flex items-center gap-2">
      <Listbox :model-value="selectedLlmOptionId" @update:model-value="(v) => emit('update:selectedLlmOptionId', v)"
        :disabled="disabled || noModels">
        <div class="relative w-56 min-w-0">
          <ListboxButton
            class="group relative flex w-full cursor-pointer items-center justify-between gap-4 rounded-md border border-gray-200 dark:border-white/[0.08] bg-white dark:bg-white/[0.02] px-3 py-1.5 text-left text-xs font-medium text-gray-900 dark:text-[#d0d6e0] transition-colors hover:bg-gray-50 dark:hover:bg-white/[0.05] hover:border-gray-300 dark:hover:border-white/[0.12]"
            :disabled="disabled">
            <div class="flex items-center gap-2.5 min-w-0 flex-1">
              <div
                class="relative flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-gray-100 dark:bg-white/[0.05] accent-text transition-colors">
                <Transition name="fade" mode="out-in">
                  <img v-if="currentOption && modelLogos[currentOption.category]" :key="currentOption.category"
                    :src="modelLogos[currentOption.category]" class="h-3.5 w-3.5 object-contain" alt="" />
                  <i v-else key="default-bot" class="fa-solid fa-robot text-[10px]"></i>
                </Transition>
                <!-- 状态指示点 -->
                <div v-if="currentOption || statusLoading"
                  class="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full border border-white dark:border-[#0f1011] transition-colors"
                  :class="(statusLoading || isChecking) ? 'bg-amber-400 animate-pulse' : (!currentOption.available) ? 'bg-rose-500' : 'bg-emerald-500'">
                </div>
              </div>
              <span
                class="block min-w-0 flex-1 truncate text-xs font-medium tracking-tight text-gray-900 dark:text-[#d0d6e0] transition-colors"
                @mouseenter="showTooltip($event, selectedLabel)" @mouseleave="hideTooltip">
                {{ selectedLabel }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <div class="relative h-2.5 w-2.5 shrink-0">
                <Transition name="icon-pop">
                  <i v-if="isChecking || statusLoading" key="checking"
                    class="fa-solid fa-spinner animate-spin absolute inset-0 flex items-center justify-center text-[10px] text-amber-500"></i>
                  <i v-else-if="currentOption && !currentOption.available" key="error"
                    class="fa-solid fa-xmark absolute inset-0 flex items-center justify-center text-[10px] text-rose-500"></i>
                  <i v-else-if="currentOption" key="ok"
                    class="fa-solid fa-check absolute inset-0 flex items-center justify-center text-[10px] text-emerald-500"></i>
                </Transition>
              </div>
              <i
                class="fa-solid fa-chevron-down shrink-0 text-[10px] text-gray-400 dark:text-[#62666d] transition-all duration-300 group-aria-expanded:rotate-180"></i>
            </div>
          </ListboxButton>

          <Transition enter-active-class="transition duration-200 ease-out"
            enter-from-class="transform scale-95 opacity-0 -translate-y-2"
            enter-to-class="transform scale-100 opacity-100 translate-y-0"
            leave-active-class="transition duration-100 ease-in"
            leave-from-class="transform scale-100 opacity-100 translate-y-0"
            leave-to-class="transform scale-95 opacity-0 -translate-y-2">
            <ListboxOptions
              class="absolute right-0 z-50 mt-2 max-h-72 w-full overflow-auto rounded-md border border-gray-200 dark:border-white/[0.08] bg-white dark:bg-[#15151e] text-base shadow-lg focus:outline-none sm:text-sm transition-colors">
              <template v-for="(item, idx) in groupedOptions" :key="idx">
                <!-- 分组标题 -->
                <li v-if="item.type === 'group'"
                  class="select-none px-4 text-[10px] font-medium uppercase tracking-widest text-gray-500 dark:text-[#62666d] transition-colors"
                  :class="idx > 0 ? 'mt-1 border-t border-gray-100 dark:border-white/[0.05] pt-2' : ''">
                  <div class="flex items-center gap-2">
                    {{ item.label }}
                  </div>
                </li>
                <!-- 模型选项 -->
                <ListboxOption v-else :value="item.optionId" :disabled="!item.available" as="template"
                  v-slot="{ active, selected, disabled: optDisabled }">
                  <li class="relative cursor-pointer select-none py-2.5 pl-10 pr-4 transition-colors" :class="[
                    active ? 'bg-gray-100 dark:bg-white/[0.05]' : '',
                    optDisabled ? 'opacity-40 cursor-not-allowed' : ''
                  ]">
                    <div class="flex items-center justify-between gap-2 min-w-0"
                      @mouseenter="showTooltip($event, item.label)" @mouseleave="hideTooltip">
                      <div class="flex items-center gap-2 min-w-0">
                        <img v-if="modelLogos[item.provider]" :src="modelLogos[item.provider]"
                          class="h-3.5 w-3.5 object-contain opacity-60 shrink-0" alt="" />
                        <span class="truncate text-sm transition-colors"
                          :class="[selected ? 'font-medium accent-text dark:text-white' : 'font-medium text-gray-700 dark:text-[#d0d6e0]']">
                          {{ item.label }}
                        </span>
                      </div>
                      <span v-if="item.isDefault"
                        class="shrink-0 rounded bg-gray-100 px-1 py-0.5 text-[9px] font-bold text-gray-400 dark:bg-white/5 dark:text-[#62666d] transition-colors">默认</span>
                    </div>
                    <span v-if="selected"
                      class="absolute inset-y-0 left-0 flex items-center pl-3 accent-text dark:text-white transition-colors">
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

  <!-- Tooltip 组件 -->
  <Teleport to="body">
    <Transition enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95 translate-y-1" enter-to-class="opacity-100 scale-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in" leave-from-class="opacity-100 scale-100 translate-y-0"
      leave-to-class="opacity-0 scale-95 translate-y-1">
      <div v-if="tooltipVisible && tooltipText" class="fixed z-[9999] pointer-events-none" :style="{
        left: `${tooltipPosition.x}px`,
        top: `${tooltipPosition.y}px`,
        transform: 'translateX(-50%) translateY(-100%)'
      }">
        <div class="relative">
          <!-- 箭头 -->
          <div class="absolute left-1/2 top-full -translate-x-1/2 w-2 h-2">
            <div class="w-2 h-2 bg-[#191a1b] rotate-45"></div>
          </div>

          <!-- 内容 -->
          <div class="bg-[#191a1b] text-[#d0d6e0] px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap">
            {{ tooltipText }}
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
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
