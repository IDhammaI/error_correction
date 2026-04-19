<script setup>
/**
 * BaseDropdown.vue
 * 基础下拉菜单组件（支持自定义触发器和菜单内容）
 */
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  position: {
    type: String,
    default: 'bottom' // 'top', 'bottom', 'left', 'right'
  },
  align: {
    type: String,
    default: 'right' // 'left', 'right', 'center'
  },
  width: {
    type: String,
    default: 'w-48'
  },
  offset: {
    type: String,
    default: 'mt-1' // 控制外边距
  },
  panelClass: {
    type: String,
    default: 'rounded-lg border bg-white shadow-lg dark:bg-[#15151e] dark:border-white/[0.08] py-1'
  },
  wrapperClass: {
    type: String,
    default: 'inline-block'
  }
})

const emit = defineEmits(['update:modelValue'])

const dropdownRef = ref(null)

const toggle = () => {
  emit('update:modelValue', !props.modelValue)
}

const close = () => {
  if (props.modelValue) {
    emit('update:modelValue', false)
  }
}

// 点击外部关闭
const handleClickOutside = (event) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="relative" :class="wrapperClass" ref="dropdownRef">
    <!-- 触发器插槽 -->
    <div @click="toggle" class="cursor-pointer h-full">
      <slot name="trigger" :isOpen="modelValue" :toggle="toggle"></slot>
    </div>

    <!-- 菜单面板 -->
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-2"
    >
      <div
        v-if="modelValue"
        class="absolute z-50 overflow-hidden transition-colors duration-200"
        :class="[
          width,
          offset,
          panelClass,
          {
            'bottom-full mb-1': position === 'top',
            'top-full mt-1': position === 'bottom',
            'right-full mr-1': position === 'left',
            'left-full ml-1': position === 'right',
            'right-0': align === 'right',
            'left-0': align === 'left',
            'left-1/2 -translate-x-1/2': align === 'center',
          }
        ]"
      >
        <slot name="background"></slot>
        <div class="relative z-10">
          <slot :close="close"></slot>
        </div>
      </div>
    </Transition>
  </div>
</template>
