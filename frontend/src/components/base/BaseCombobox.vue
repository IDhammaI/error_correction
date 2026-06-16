<script setup>
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number, Object], default: '' },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: '请选择' },
  searchPlaceholder: { type: String, default: '搜索' },
  labelKey: { type: String, default: 'label' },
  valueKey: { type: String, default: 'value' },
  clearable: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue', 'change'])
const open = ref(false)
const query = ref('')
const activeIndex = ref(0)
const inputRef = ref(null)

const normalizedOptions = computed(() =>
  props.options.map(option => typeof option === 'object' ? option : { label: String(option), value: option }),
)

const selectedOption = computed(() =>
  normalizedOptions.value.find(option => option[props.valueKey] === props.modelValue),
)

const filteredOptions = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  if (!keyword) return normalizedOptions.value
  return normalizedOptions.value.filter(option => String(option[props.labelKey] || '').toLowerCase().includes(keyword))
})

watch(open, async value => {
  if (!value) return
  query.value = ''
  activeIndex.value = 0
  await nextTick()
  inputRef.value?.focus()
})

function select(option) {
  const value = option?.[props.valueKey] ?? ''
  emit('update:modelValue', value)
  emit('change', value, option)
  open.value = false
}

function move(delta) {
  if (!filteredOptions.value.length) return
  activeIndex.value = (activeIndex.value + delta + filteredOptions.value.length) % filteredOptions.value.length
}
</script>

<template>
  <div class="relative">
    <button
      type="button"
      class="flex h-10 w-full items-center justify-between gap-2 rounded-lg border border-slate-200 bg-white px-3 text-left text-sm transition-colors hover:bg-slate-50 dark:border-white/[0.08] dark:bg-white/[0.03] dark:hover:bg-white/[0.06]"
      @click="open = !open"
    >
      <span class="min-w-0 flex-1 truncate" :class="selectedOption ? 'text-slate-800 dark:text-[#d0d6e0]' : 'text-slate-400 dark:text-[#62666d]'">
        {{ selectedOption?.[labelKey] || placeholder }}
      </span>
      <button
        v-if="clearable && selectedOption"
        type="button"
        class="flex h-5 w-5 items-center justify-center rounded text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-white/[0.06] dark:hover:text-[#d0d6e0]"
        @click.stop="select(null)"
      >
        <i class="fa-solid fa-xmark text-[10px]"></i>
      </button>
      <i class="fa-solid fa-chevron-down shrink-0 text-[10px] text-slate-400 transition-transform" :class="open ? 'rotate-180' : ''"></i>
    </button>

    <Transition enter-active-class="transition duration-150 ease-out" enter-from-class="-translate-y-1 opacity-0" leave-active-class="transition duration-100 ease-in" leave-to-class="-translate-y-1 opacity-0">
      <div v-if="open" class="absolute left-0 top-full z-[70] mt-1 w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl shadow-black/10 dark:border-white/[0.08] dark:bg-[#1b1b1f] dark:shadow-black/40">
        <div class="border-b border-slate-200 p-2 dark:border-white/[0.06]">
          <input
            ref="inputRef"
            v-model="query"
            class="h-9 w-full rounded-lg bg-slate-100 px-3 text-sm text-slate-900 outline-none placeholder:text-slate-400 dark:bg-white/[0.05] dark:text-[#f7f8f8] dark:placeholder:text-[#62666d]"
            :placeholder="searchPlaceholder"
            @keydown.down.prevent="move(1)"
            @keydown.up.prevent="move(-1)"
            @keydown.enter.prevent="select(filteredOptions[activeIndex])"
            @keydown.esc.prevent="open = false"
          />
        </div>
        <div class="max-h-56 overflow-y-auto p-1.5 custom-scrollbar">
          <button
            v-for="(option, index) in filteredOptions"
            :key="option[valueKey]"
            type="button"
            class="flex h-9 w-full items-center justify-between gap-2 rounded-lg px-2.5 text-left text-sm transition-colors"
            :class="index === activeIndex ? 'accent-bg-soft accent-text' : 'text-slate-700 hover:bg-slate-100 dark:text-[#d0d6e0] dark:hover:bg-white/[0.05]'"
            @mouseenter="activeIndex = index"
            @click="select(option)"
          >
            <span class="min-w-0 truncate">{{ option[labelKey] }}</span>
            <i v-if="option[valueKey] === modelValue" class="fa-solid fa-check text-[10px]"></i>
          </button>
          <div v-if="!filteredOptions.length" class="px-3 py-6 text-center text-sm text-slate-500 dark:text-[#8a8f98]">
            没有匹配项
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>
