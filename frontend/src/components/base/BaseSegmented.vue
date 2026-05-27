<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number, Boolean], default: '' },
  options: { type: Array, default: () => [] },
  size: { type: String, default: 'sm' },
})

const emit = defineEmits(['update:modelValue', 'change'])
const rootRef = ref(null)
const optionRefs = ref([])
const indicatorStyle = ref({ opacity: 0, width: '0px', transform: 'translateX(0px)' })
let resizeObserver = null

const activeIndex = computed(() => props.options.findIndex(option => option.value === props.modelValue))

const setOptionRef = (el, index) => {
  if (el) optionRefs.value[index] = el
}

const updateIndicator = async () => {
  await nextTick()
  const el = optionRefs.value[activeIndex.value]
  if (!el) {
    indicatorStyle.value = { opacity: 0, width: '0px', transform: 'translateX(0px)' }
    return
  }

  indicatorStyle.value = {
    opacity: 1,
    width: `${el.offsetWidth}px`,
    transform: `translateX(${el.offsetLeft}px)`,
  }
}

const selectOption = (value) => {
  emit('update:modelValue', value)
  emit('change', value)
}

watch(() => [props.modelValue, props.options.length, props.size], updateIndicator, { immediate: true })

onMounted(() => {
  updateIndicator()
  if (typeof ResizeObserver !== 'undefined' && rootRef.value) {
    resizeObserver = new ResizeObserver(updateIndicator)
    resizeObserver.observe(rootRef.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
})
</script>

<template>
  <div ref="rootRef" class="relative inline-flex items-center overflow-hidden rounded-md brand-btn p-0.5 transition-colors">
    <span
      class="pointer-events-none absolute inset-y-0.5 left-0 rounded brand-gradient-bg shadow-sm transition-[transform,width,opacity] duration-200 ease-out"
      :style="indicatorStyle"
      aria-hidden="true"
    ></span>
    <button
      v-for="(option, index) in options"
      :key="option.value"
      :ref="el => setOptionRef(el, index)"
      type="button"
      class="relative z-10 inline-flex shrink-0 items-center justify-center whitespace-nowrap rounded font-medium transition-colors duration-150"
      :class="[
        size === 'sm' ? 'h-7 px-3 text-xs' : 'h-8 px-3.5 text-sm',
        modelValue === option.value
          ? 'text-white'
          : 'text-gray-500 hover:text-gray-700 dark:text-[#62666d] dark:hover:text-[#8a8f98]',
      ]"
      @click="selectOption(option.value)"
    >
      <i v-if="option.icon" class="fa-solid mr-1.5" :class="option.icon"></i>
      <span class="whitespace-nowrap">{{ option.label }}</span>
    </button>
  </div>
</template>
