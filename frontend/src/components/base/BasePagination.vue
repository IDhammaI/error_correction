<script setup>
/**
 * BasePagination.vue
 * 通用分页组件，内部计算页码窗口和省略号。
 */
import { computed } from 'vue'

const props = defineProps({
  page: { type: Number, default: 1 },
  totalPages: { type: Number, default: 0 },
})

const emit = defineEmits(['update:page', 'change'])

const pageButtons = computed(() => {
  const total = props.totalPages
  const current = props.page
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages = [1]
  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)
  if (start > 2) pages.push('...')
  for (let i = start; i <= end; i++) pages.push(i)
  if (end < total - 1) pages.push('...')
  pages.push(total)
  return pages
})

const setPage = (value) => {
  if (value < 1 || value > props.totalPages || value === props.page) return
  emit('update:page', value)
  emit('change', value)
}
</script>

<template>
  <nav v-if="totalPages > 1" class="flex items-center justify-center gap-2">
    <button class="pager-btn" :disabled="page <= 1" @click="setPage(page - 1)">
      <i class="fa-solid fa-chevron-left"></i>
    </button>
    <template v-for="(p, i) in pageButtons" :key="i">
      <span v-if="p === '...'" class="px-1 text-gray-400">...</span>
      <button v-else class="pager-btn min-w-9" :class="p === page ? 'accent-bg text-white border-transparent' : ''" @click="setPage(p)">
        {{ p }}
      </button>
    </template>
    <button class="pager-btn" :disabled="page >= totalPages" @click="setPage(page + 1)">
      <i class="fa-solid fa-chevron-right"></i>
    </button>
  </nav>
</template>

<style scoped>
.pager-btn {
  @apply inline-flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 bg-white text-sm font-bold text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-800 disabled:cursor-not-allowed disabled:opacity-35 dark:border-white/[0.07] dark:bg-white/[0.035] dark:text-[#8a8f98] dark:hover:bg-white/[0.06] dark:hover:text-[#d0d6e0];
}
</style>
