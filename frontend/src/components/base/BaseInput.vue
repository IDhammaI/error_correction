<script setup>
/**
 * BaseInput.vue
 * 基础输入框组件（支持密码显隐、错误高亮、右侧附加元素）
 */
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  label: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  },
  placeholder: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  },
  autocomplete: {
    type: String,
    default: 'off'
  },
  maxlength: {
    type: [String, Number],
    default: null
  },
  inputmode: {
    type: String,
    default: 'text'
  },
  inputClass: {
    type: String,
    default: ''
  },
  error: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const showPwd = ref(false)

const inputType = computed(() => {
  if (props.type === 'password') {
    return showPwd.value ? 'text' : 'password'
  }
  return props.type
})
</script>

<template>
  <div>
    <label v-if="label" class="block text-sm font-medium text-gray-700 dark:text-white/60 mb-2 transition-colors">{{ label }}</label>
    <div :class="['relative', { 'flex gap-2': $slots.append }]">
      <div class="relative flex-1 min-w-0">
        <input
          :value="modelValue"
          @input="$emit('update:modelValue', $event.target.value)"
          :type="inputType"
          :required="required"
          :autocomplete="autocomplete"
          :placeholder="placeholder"
          :maxlength="maxlength"
          :inputmode="inputmode"
          :spellcheck="spellcheck"
          data-gramm="false"
          :class="[
            'w-full h-10 px-4 rounded-xl border bg-white dark:bg-white/[0.03] text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-white/25 focus:outline-none focus:ring-0 focus:ring-offset-0 transition-all text-sm outline-none [&::-ms-reveal]:hidden [&::-ms-clear]:hidden',
            error ? 'border-rose-500/50 focus:border-rose-500/50' : 'border-gray-200 dark:border-white/[0.08] focus:border-[rgb(var(--accent-rgb)/0.4)] dark:focus:border-[rgb(var(--accent-rgb)/0.4)]',
            type === 'password' ? 'pr-11' : '',
            inputClass
          ]"
        />
        <button
          v-if="type === 'password'"
          type="button"
          @click="showPwd = !showPwd"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:text-white/25 dark:hover:text-white/50 transition-colors"
        >
          <i :class="showPwd ? 'fas fa-eye-slash' : 'fas fa-eye'" class="text-xs"></i>
        </button>
      </div>
      <slot name="append" />
    </div>
  </div>
</template>
