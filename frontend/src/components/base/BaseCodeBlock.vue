<script setup>
import BaseCopyButton from './BaseCopyButton.vue'

defineProps({
  code: { type: String, default: '' },
  language: { type: String, default: 'text' },
  title: { type: String, default: '' },
  copyable: { type: Boolean, default: true },
})
</script>

<template>
  <div class="overflow-hidden rounded-xl border border-slate-200 bg-slate-950 text-slate-100 shadow-sm dark:border-white/[0.08]">
    <div v-if="title || language || copyable" class="flex min-h-10 items-center justify-between gap-3 border-b border-white/[0.08] px-3">
      <div class="min-w-0">
        <p v-if="title" class="truncate text-xs font-bold text-slate-200">{{ title }}</p>
        <p v-else class="text-xs font-bold uppercase text-slate-500">{{ language }}</p>
      </div>
      <BaseCopyButton v-if="copyable" :text="code" />
    </div>
    <pre class="custom-scrollbar max-h-72 overflow-auto p-4 text-xs leading-6"><code>{{ code }}</code></pre>
  </div>
</template>
