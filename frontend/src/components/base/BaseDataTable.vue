<script setup>
import { computed, ref, watch } from 'vue'
import BasePagination from './BasePagination.vue'
import BaseSearchInput from './BaseSearchInput.vue'
import BaseTable from './BaseTable.vue'

const props = defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  rowKey: { type: String, default: 'id' },
  searchable: { type: Boolean, default: true },
  pageSize: { type: Number, default: 5 },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['row-click'])
const query = ref('')
const page = ref(1)
const sortKey = ref('')
const sortDirection = ref('')

const filteredRows = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  if (!keyword) return props.rows
  return props.rows.filter(row =>
    props.columns.some(column => String(row[column.key] ?? '').toLowerCase().includes(keyword)),
  )
})

const sortedRows = computed(() => {
  if (!sortKey.value || !sortDirection.value) return filteredRows.value
  return [...filteredRows.value].sort((a, b) => {
    const av = a[sortKey.value]
    const bv = b[sortKey.value]
    if (av === bv) return 0
    const result = av > bv ? 1 : -1
    return sortDirection.value === 'asc' ? result : -result
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(sortedRows.value.length / props.pageSize)))
const visibleRows = computed(() => {
  const start = (page.value - 1) * props.pageSize
  return sortedRows.value.slice(start, start + props.pageSize)
})

watch([query, () => props.rows.length], () => {
  page.value = 1
})

function sort(columnKey) {
  if (sortKey.value !== columnKey) {
    sortKey.value = columnKey
    sortDirection.value = 'asc'
    return
  }
  if (sortDirection.value === 'asc') sortDirection.value = 'desc'
  else if (sortDirection.value === 'desc') {
    sortKey.value = ''
    sortDirection.value = ''
  } else sortDirection.value = 'asc'
}
</script>

<template>
  <div class="space-y-3">
    <div v-if="searchable || $slots.toolbar" class="flex flex-wrap items-center justify-between gap-3">
      <BaseSearchInput v-if="searchable" v-model="query" class="w-64 max-w-full" placeholder="搜索表格" />
      <slot name="toolbar" />
    </div>
    <BaseTable
      :columns="columns"
      :rows="visibleRows"
      :row-key="rowKey"
      :loading="loading"
      :sort-key="sortKey"
      :sort-direction="sortDirection"
      @sort="sort"
      @row-click="row => emit('row-click', row)"
    >
      <template v-for="column in columns" #[`cell-${column.key}`]="slotProps">
        <slot :name="`cell-${column.key}`" v-bind="slotProps">
          {{ slotProps.value }}
        </slot>
      </template>
    </BaseTable>
    <div class="flex items-center justify-between gap-3">
      <p class="text-xs text-slate-500 dark:text-[#8a8f98]">
        共 {{ filteredRows.length }} 条
      </p>
      <BasePagination v-if="totalPages > 1" v-model:page="page" :total-pages="totalPages" />
    </div>
  </div>
</template>
