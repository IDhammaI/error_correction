<script setup>
const props = defineProps({
  tone: { type: String, default: 'info' },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  icon: { type: String, default: '' },
  closable: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])

const toneClass = {
  info: {
    wrap: 'border-blue-500/20 bg-blue-500/10 text-blue-700 dark:text-blue-200',
    icon: 'text-blue-500 dark:text-blue-300',
    defaultIcon: 'fa-circle-info',
  },
  success: {
    wrap: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200',
    icon: 'text-emerald-600 dark:text-emerald-300',
    defaultIcon: 'fa-circle-check',
  },
  warning: {
    wrap: 'border-amber-500/20 bg-amber-500/10 text-amber-800 dark:text-amber-200',
    icon: 'text-amber-600 dark:text-amber-300',
    defaultIcon: 'fa-triangle-exclamation',
  },
  danger: {
    wrap: 'border-rose-500/20 bg-rose-500/10 text-rose-700 dark:text-rose-200',
    icon: 'text-rose-600 dark:text-rose-300',
    defaultIcon: 'fa-circle-xmark',
  },
}

const config = () => toneClass[props.tone] || toneClass.info
</script>

<template>
  <div
    role="status"
    class="flex gap-3 rounded-xl border px-4 py-3"
    :class="config().wrap"
  >
    <i class="fa-solid mt-0.5 shrink-0 text-sm" :class="[icon || config().defaultIcon, config().icon]"></i>
    <div class="min-w-0 flex-1">
      <p v-if="title" class="text-sm font-bold">{{ title }}</p>
      <p v-if="description" class="mt-1 text-sm leading-5 opacity-80">{{ description }}</p>
      <div v-if="$slots.default" class="mt-2 text-sm leading-5 opacity-85">
        <slot />
      </div>
    </div>
    <button
      v-if="closable"
      type="button"
      class="-mr-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-md opacity-60 transition hover:bg-black/5 hover:opacity-100 dark:hover:bg-white/10"
      @click="emit('close')"
    >
      <i class="fa-solid fa-xmark text-xs"></i>
    </button>
  </div>
</template>
