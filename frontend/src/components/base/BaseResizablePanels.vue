<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: { type: Number, default: 45 },
  min: { type: Number, default: 20 },
  max: { type: Number, default: 80 },
})

const emit = defineEmits(['update:modelValue', 'change'])
const rootRef = ref(null)
const dragging = ref(false)

const leftStyle = computed(() => ({ flexBasis: `${props.modelValue}%` }))

function startDrag(event) {
  dragging.value = true
  window.addEventListener('pointermove', onDrag)
  window.addEventListener('pointerup', stopDrag)
  event.preventDefault()
}

function onDrag(event) {
  if (!rootRef.value) return
  const rect = rootRef.value.getBoundingClientRect()
  const raw = ((event.clientX - rect.left) / rect.width) * 100
  const value = Math.min(props.max, Math.max(props.min, raw))
  emit('update:modelValue', Math.round(value))
  emit('change', Math.round(value))
}

function stopDrag() {
  dragging.value = false
  window.removeEventListener('pointermove', onDrag)
  window.removeEventListener('pointerup', stopDrag)
}
</script>

<template>
  <div ref="rootRef" class="flex min-h-56 overflow-hidden rounded-xl border border-slate-200 bg-white/70 dark:border-white/[0.08] dark:bg-white/[0.025]">
    <section class="min-w-0 shrink-0 grow-0 overflow-auto p-4 custom-scrollbar" :style="leftStyle">
      <slot name="left" />
    </section>
    <button
      type="button"
      class="w-2 shrink-0 cursor-col-resize bg-slate-200/70 transition-colors hover:bg-[rgb(var(--accent-rgb)/0.45)] dark:bg-white/[0.08] dark:hover:bg-[rgb(var(--accent-rgb)/0.45)]"
      :class="dragging ? 'bg-[rgb(var(--accent-rgb)/0.55)]' : ''"
      @pointerdown="startDrag"
    ></button>
    <section class="min-w-0 flex-1 overflow-auto p-4 custom-scrollbar">
      <slot name="right" />
    </section>
  </div>
</template>
