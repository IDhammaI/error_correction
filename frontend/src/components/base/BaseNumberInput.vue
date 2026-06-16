<script setup>
import { computed } from 'vue'
import BaseFieldMessage from './BaseFieldMessage.vue'

const props = defineProps({
  modelValue: { type: [Number, String], default: null },
  label: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  hint: { type: String, default: '' },
  error: { type: String, default: '' },
  min: { type: Number, default: null },
  max: { type: Number, default: null },
  step: { type: Number, default: 1 },
  name: { type: String, default: '' },
  required: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'change'])

const numericValue = computed(() => {
  if (props.modelValue === '' || props.modelValue === null || props.modelValue === undefined) return null
  const parsed = Number(props.modelValue)
  return Number.isFinite(parsed) ? parsed : null
})

function clamp(value) {
  if (value === null) return null
  if (props.min !== null && value < props.min) return props.min
  if (props.max !== null && value > props.max) return props.max
  return value
}

function commit(value, event) {
  const next = clamp(value)
  emit('update:modelValue', next)
  emit('change', next, event)
}

function onInput(event) {
  const raw = event.target.value
  commit(raw === '' ? null : Number(raw), event)
}

function stepBy(delta, event) {
  if (props.disabled) return
  commit((numericValue.value ?? 0) + delta * props.step, event)
}
</script>

<template>
  <div>
    <label v-if="label" class="mb-2 block text-sm font-medium text-gray-700 dark:text-white/60">
      {{ label }}<span v-if="required" class="ml-0.5 text-rose-500">*</span>
    </label>
    <div class="relative">
      <input
        :value="modelValue ?? ''"
        type="number"
        :name="name"
        :min="min"
        :max="max"
        :step="step"
        :placeholder="placeholder"
        :required="required"
        :disabled="disabled"
        :aria-invalid="Boolean(error) || undefined"
        class="h-10 w-full rounded-lg border bg-white px-4 pr-20 text-sm text-gray-900 outline-none transition-all placeholder:text-gray-400 focus:ring-0 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white/[0.03] dark:text-white dark:placeholder-white/25"
        :class="error ? 'border-rose-500/50 focus:border-rose-500/50' : 'border-gray-200 focus:border-[rgb(var(--accent-rgb)/0.4)] dark:border-white/[0.08] dark:focus:border-[rgb(var(--accent-rgb)/0.4)]'"
        @input="onInput"
      />
      <div class="absolute right-1 top-1 flex h-8 overflow-hidden rounded-md border border-gray-200 bg-gray-50 dark:border-white/[0.08] dark:bg-white/[0.04]">
        <button type="button" class="flex w-8 items-center justify-center text-xs text-slate-500 hover:bg-white dark:text-[#8a8f98] dark:hover:bg-white/[0.06]" :disabled="disabled" @click="stepBy(-1, $event)">
          <i class="fa-solid fa-minus"></i>
        </button>
        <button type="button" class="flex w-8 items-center justify-center border-l border-gray-200 text-xs text-slate-500 hover:bg-white dark:border-white/[0.08] dark:text-[#8a8f98] dark:hover:bg-white/[0.06]" :disabled="disabled" @click="stepBy(1, $event)">
          <i class="fa-solid fa-plus"></i>
        </button>
      </div>
    </div>
    <BaseFieldMessage v-if="error" :message="error" type="error" />
    <BaseFieldMessage v-else-if="hint" :message="hint" />
  </div>
</template>
