<script setup>
import { computed, inject } from 'vue'
import BaseFieldMessage from './BaseFieldMessage.vue'

const props = defineProps({
  label: { type: String, default: '' },
  hint: { type: String, default: '' },
  error: { type: String, default: '' },
  required: { type: Boolean, default: false },
  forId: { type: String, default: '' },
  layout: { type: String, default: '' },
})

const form = inject('baseForm', null)
const resolvedLayout = computed(() => props.layout || form?.layout || 'vertical')
</script>

<template>
  <div
    class="min-w-0"
    :class="resolvedLayout === 'horizontal' ? 'grid gap-3 sm:grid-cols-[10rem_minmax(0,1fr)] sm:items-start' : ''"
  >
    <div v-if="label || hint" :class="resolvedLayout === 'horizontal' ? 'pt-2' : 'mb-2'">
      <label
        v-if="label"
        class="block text-sm font-medium text-gray-700 dark:text-white/60"
        :for="forId || undefined"
      >
        {{ label }}<span v-if="required" class="ml-0.5 text-rose-500">*</span>
      </label>
      <p v-if="hint && resolvedLayout === 'horizontal'" class="mt-1 text-xs leading-5 text-slate-500 dark:text-[#8a8f98]">
        {{ hint }}
      </p>
    </div>

    <div class="min-w-0">
      <slot :invalid="Boolean(error)" />
      <BaseFieldMessage v-if="error" :message="error" type="error" />
      <BaseFieldMessage v-else-if="hint && resolvedLayout !== 'horizontal'" :message="hint" />
    </div>
  </div>
</template>
