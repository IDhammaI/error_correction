<script setup>
import { provide } from 'vue'

const props = defineProps({
  disabled: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  layout: { type: String, default: 'vertical' },
  gap: { type: String, default: 'gap-4' },
})

const emit = defineEmits(['submit'])

provide('baseForm', props)

function submit(event) {
  if (props.disabled || props.loading) return
  emit('submit', event)
}
</script>

<template>
  <form
    class="relative grid"
    :class="[gap, layout === 'horizontal' ? 'grid-cols-1' : 'grid-cols-1']"
    @submit.prevent="submit"
  >
    <fieldset class="contents" :disabled="disabled || loading">
      <slot />
    </fieldset>
    <div v-if="loading" class="pointer-events-none absolute inset-0 rounded-xl bg-white/30 backdrop-blur-[1px] dark:bg-black/10"></div>
  </form>
</template>
