<script setup>
import { computed } from 'vue'
import BaseFieldMessage from './BaseFieldMessage.vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  hint: { type: String, default: '' },
  error: { type: String, default: '' },
  name: { type: String, default: '' },
  rows: { type: [Number, String], default: 4 },
  maxlength: { type: [Number, String], default: null },
  required: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  resize: { type: String, default: 'vertical' },
  textareaClass: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])
const countText = computed(() => {
  if (!props.maxlength) return ''
  return `${String(props.modelValue || '').length}/${props.maxlength}`
})
</script>

<template>
  <div>
    <div v-if="label || countText" class="mb-2 flex items-center justify-between gap-3">
      <label v-if="label" class="text-sm font-medium text-gray-700 dark:text-white/60">
        {{ label }}<span v-if="required" class="ml-0.5 text-rose-500">*</span>
      </label>
      <span v-if="countText" class="text-xs text-slate-400 dark:text-[#62666d]">{{ countText }}</span>
    </div>
    <textarea
      :value="modelValue"
      :name="name"
      :rows="rows"
      :placeholder="placeholder"
      :maxlength="maxlength"
      :required="required"
      :disabled="disabled"
      :aria-invalid="Boolean(error) || undefined"
      class="w-full rounded-lg border bg-white px-4 py-3 text-sm text-gray-900 outline-none transition-all placeholder:text-gray-400 focus:ring-0 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white/[0.03] dark:text-white dark:placeholder-white/25"
      :class="[
        error ? 'border-rose-500/50 focus:border-rose-500/50' : 'border-gray-200 focus:border-[rgb(var(--accent-rgb)/0.4)] dark:border-white/[0.08] dark:focus:border-[rgb(var(--accent-rgb)/0.4)]',
        resize === 'none' ? 'resize-none' : resize === 'horizontal' ? 'resize-x' : 'resize-y',
        textareaClass,
      ]"
      @input="emit('update:modelValue', $event.target.value)"
    ></textarea>
    <BaseFieldMessage v-if="error" :message="error" type="error" />
    <BaseFieldMessage v-else-if="hint" :message="hint" />
  </div>
</template>
