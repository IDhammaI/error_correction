<script setup>
import BaseRadio from './BaseRadio.vue'
import BaseFieldMessage from './BaseFieldMessage.vue'

defineProps({
  modelValue: { type: [String, Number, Boolean], default: '' },
  options: { type: Array, default: () => [] },
  label: { type: String, default: '' },
  description: { type: String, default: '' },
  name: { type: String, default: '' },
  required: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  error: { type: String, default: '' },
  direction: { type: String, default: 'vertical' },
})

const emit = defineEmits(['update:modelValue', 'change'])

function select(value, event) {
  emit('update:modelValue', value)
  emit('change', value, event)
}
</script>

<template>
  <fieldset>
    <legend v-if="label" class="text-sm font-medium text-slate-800 dark:text-[#f7f8f8]">
      {{ label }}<span v-if="required" class="ml-0.5 text-rose-500">*</span>
    </legend>
    <p v-if="description" class="mt-1 text-xs leading-5 text-slate-500 dark:text-[#8a8f98]">
      {{ description }}
    </p>

    <div class="mt-3 flex gap-4" :class="direction === 'horizontal' ? 'flex-row flex-wrap' : 'flex-col'">
      <BaseRadio
        v-for="option in options"
        :key="option.value"
        :model-value="modelValue"
        :value="option.value"
        :label="option.label"
        :description="option.description"
        :name="name"
        :disabled="disabled || option.disabled"
        :required="required"
        :error="Boolean(error)"
        @update:model-value="value => select(value)"
      />
      <slot />
    </div>

    <BaseFieldMessage v-if="error" :message="error" type="error" />
  </fieldset>
</template>
