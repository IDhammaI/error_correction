<script setup>
import { provide } from 'vue'

const props = defineProps({
  delay: { type: Number, default: 0 },
  offset: { type: Number, default: 8 },
  zIndex: { type: Number, default: 9999 },
  disabled: { type: Boolean, default: false },
})

provide('baseTooltipProvider', props)
</script>

<template>
  <slot />
</template>
