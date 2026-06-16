<script setup>
import BaseFieldMessage from './BaseFieldMessage.vue'

defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  hint: { type: String, default: '' },
  error: { type: String, default: '' },
  name: { type: String, default: '' },
  min: { type: String, default: '' },
  max: { type: String, default: '' },
  step: { type: [Number, String], default: 60 },
  required: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'change'])

function update(event) {
  emit('update:modelValue', event.target.value)
  emit('change', event.target.value, event)
}
</script>

<template>
  <div>
    <label v-if="label" class="mb-2 block text-sm font-medium text-gray-700 dark:text-white/60">
      {{ label }}<span v-if="required" class="ml-0.5 text-rose-500">*</span>
    </label>
    <div class="relative">
      <input
        :value="modelValue"
        type="time"
        :name="name"
        :min="min"
        :max="max"
        :step="step"
        :required="required"
        :disabled="disabled"
        :aria-invalid="Boolean(error) || undefined"
        class="h-10 w-full rounded-lg border bg-white px-4 pr-10 text-sm text-gray-900 outline-none transition-all focus:ring-0 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white/[0.03] dark:text-white"
        :class="error ? 'border-rose-500/50 focus:border-rose-500/50' : 'border-gray-200 focus:border-[rgb(var(--accent-rgb)/0.4)] dark:border-white/[0.08] dark:focus:border-[rgb(var(--accent-rgb)/0.4)]'"
        @input="update"
      />
      <i class="fa-regular fa-clock pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 dark:text-[#62666d]"></i>
    </div>
    <BaseFieldMessage v-if="error" :message="error" type="error" />
    <BaseFieldMessage v-else-if="hint" :message="hint" />
  </div>
</template>
