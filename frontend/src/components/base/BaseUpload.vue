<script setup>
import { computed, ref } from 'vue'
import BaseFieldMessage from './BaseFieldMessage.vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  label: { type: String, default: '' },
  description: { type: String, default: '' },
  accept: { type: String, default: '' },
  multiple: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false },
  maxSize: { type: Number, default: 0 },
  error: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'change', 'reject'])

const fileInput = ref(null)
const dragging = ref(false)

const acceptText = computed(() => props.accept || 'Any file type')

function openDialog() {
  if (props.disabled) return
  fileInput.value?.click()
}

function normalize(fileList) {
  const files = Array.from(fileList || [])
  const accepted = []
  const rejected = []

  files.forEach((file) => {
    if (props.maxSize && file.size > props.maxSize) rejected.push({ file, reason: 'size' })
    else accepted.push(file)
  })

  if (rejected.length) emit('reject', rejected)
  return props.multiple ? [...props.modelValue, ...accepted] : accepted.slice(0, 1)
}

function commit(fileList, event) {
  if (props.disabled) return
  const next = normalize(fileList)
  emit('update:modelValue', next)
  emit('change', next, event)
}

function onInput(event) {
  commit(event.target.files, event)
  event.target.value = ''
}

function onDrop(event) {
  dragging.value = false
  commit(event.dataTransfer.files, event)
}

function remove(index) {
  const next = props.modelValue.filter((_, itemIndex) => itemIndex !== index)
  emit('update:modelValue', next)
  emit('change', next)
}

function formatSize(size) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}
</script>

<template>
  <div>
    <label v-if="label" class="mb-2 block text-sm font-medium text-gray-700 dark:text-white/60">{{ label }}</label>
    <div
      class="group flex min-h-32 flex-col items-center justify-center rounded-xl border border-dashed px-5 py-6 text-center transition-colors"
      :class="[
        dragging ? 'accent-border accent-bg-muted' : 'border-gray-300 bg-white/60 hover:bg-white dark:border-white/[0.08] dark:bg-white/[0.025] dark:hover:bg-white/[0.04]',
        disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer',
        error ? 'border-rose-500/50' : '',
      ]"
      role="button"
      tabindex="0"
      @click="openDialog"
      @keydown.enter.prevent="openDialog"
      @keydown.space.prevent="openDialog"
      @dragenter.prevent="dragging = true"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="onDrop"
    >
      <input ref="fileInput" class="hidden" type="file" :accept="accept" :multiple="multiple" :disabled="disabled" @change="onInput" />
      <i class="fa-solid fa-cloud-arrow-up text-xl text-slate-400 transition-colors group-hover:text-slate-500 dark:text-[#62666d] dark:group-hover:text-[#8a8f98]"></i>
      <p class="mt-3 text-sm font-medium text-slate-700 dark:text-[#d0d6e0]">
        Drop files here or browse
      </p>
      <p class="mt-1 text-xs text-slate-500 dark:text-[#8a8f98]">
        {{ description || acceptText }}
      </p>
    </div>

    <div v-if="modelValue.length" class="mt-3 space-y-2">
      <div
        v-for="(file, index) in modelValue"
        :key="`${file.name}-${file.size}-${index}`"
        class="flex min-h-10 items-center gap-3 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-white/[0.08] dark:bg-white/[0.035]"
      >
        <i class="fa-regular fa-file-lines shrink-0 text-slate-400 dark:text-[#62666d]"></i>
        <span class="min-w-0 flex-1 truncate text-slate-700 dark:text-[#d0d6e0]">{{ file.name }}</span>
        <span class="shrink-0 text-xs text-slate-400 dark:text-[#62666d]">{{ formatSize(file.size) }}</span>
        <button type="button" class="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-white/[0.06] dark:hover:text-[#d0d6e0]" @click.stop="remove(index)">
          <i class="fa-solid fa-xmark text-xs"></i>
        </button>
      </div>
    </div>

    <BaseFieldMessage v-if="error" :message="error" type="error" />
  </div>
</template>
