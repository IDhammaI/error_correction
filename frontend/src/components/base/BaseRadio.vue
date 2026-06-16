<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number, Boolean], default: '' },
  value: { type: [String, Number, Boolean], required: true },
  label: { type: String, default: '' },
  description: { type: String, default: '' },
  name: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  required: { type: Boolean, default: false },
  error: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'change'])
const checked = computed(() => props.modelValue === props.value)

function select(event) {
  if (props.disabled) return
  emit('update:modelValue', props.value)
  emit('change', props.value, event)
}
</script>

<template>
  <label
    class="group inline-flex items-start gap-3"
    :class="disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'"
  >
    <span class="relative mt-0.5 inline-flex h-4 w-4 shrink-0">
      <input
        class="peer sr-only"
        type="radio"
        :name="name"
        :value="value"
        :checked="checked"
        :disabled="disabled"
        :required="required"
        :aria-invalid="error || undefined"
        @change="select"
      />
      <span
        class="flex h-4 w-4 items-center justify-center rounded-full border transition-colors peer-focus-visible:ring-2 peer-focus-visible:ring-[rgb(var(--accent-rgb)/0.35)]"
        :class="[
          checked ? 'accent-border bg-white dark:bg-white/[0.04]' : 'border-gray-300 bg-white dark:border-white/[0.12] dark:bg-white/[0.04]',
          error ? 'border-rose-500/60' : '',
        ]"
      >
        <span class="h-2 w-2 rounded-full transition-transform" :class="checked ? 'scale-100 accent-bg' : 'scale-0 bg-transparent'"></span>
      </span>
    </span>

    <span v-if="label || description || $slots.default" class="min-w-0">
      <span class="block text-sm font-medium text-slate-800 dark:text-[#f7f8f8]">
        <slot>{{ label }}</slot>
      </span>
      <span v-if="description" class="mt-0.5 block text-xs leading-5 text-slate-500 dark:text-[#8a8f98]">
        {{ description }}
      </span>
    </span>
  </label>
</template>
