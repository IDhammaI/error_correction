<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: [Boolean, Array, String, Number], default: false },
  value: { type: [String, Number, Boolean], default: true },
  trueValue: { type: [String, Number, Boolean], default: true },
  falseValue: { type: [String, Number, Boolean], default: false },
  label: { type: String, default: '' },
  description: { type: String, default: '' },
  name: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  required: { type: Boolean, default: false },
  indeterminate: { type: Boolean, default: false },
  error: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'change'])

const checked = computed(() => {
  if (Array.isArray(props.modelValue)) return props.modelValue.includes(props.value)
  return props.modelValue === props.trueValue
})

function toggle(event) {
  if (props.disabled) return

  let nextValue
  if (Array.isArray(props.modelValue)) {
    const next = new Set(props.modelValue)
    if (event.target.checked) next.add(props.value)
    else next.delete(props.value)
    nextValue = [...next]
  } else {
    nextValue = event.target.checked ? props.trueValue : props.falseValue
  }

  emit('update:modelValue', nextValue)
  emit('change', nextValue, event)
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
        type="checkbox"
        :name="name"
        :checked="checked"
        :disabled="disabled"
        :required="required"
        :aria-invalid="error || undefined"
        @change="toggle"
      />
      <span
        class="flex h-4 w-4 items-center justify-center rounded border transition-colors peer-focus-visible:ring-2 peer-focus-visible:ring-[rgb(var(--accent-rgb)/0.35)]"
        :class="[
          checked || indeterminate
            ? 'accent-bg border-transparent text-white'
            : 'border-gray-300 bg-white text-transparent dark:border-white/[0.12] dark:bg-white/[0.04]',
          error ? 'border-rose-500/60' : '',
        ]"
      >
        <i v-if="indeterminate" class="fa-solid fa-minus text-[9px]"></i>
        <i v-else class="fa-solid fa-check text-[9px]"></i>
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
