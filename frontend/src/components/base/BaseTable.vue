<script setup>
defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  rowKey: { type: String, default: 'id' },
  emptyText: { type: String, default: '暂无数据' },
  loading: { type: Boolean, default: false },
  compact: { type: Boolean, default: false },
  sortKey: { type: String, default: '' },
  sortDirection: { type: String, default: '' },
})

const emit = defineEmits(['sort', 'row-click'])

function cellValue(row, column) {
  if (typeof column.render === 'function') return column.render(row)
  return row[column.key]
}

function sortIcon(column, sortKey, sortDirection) {
  if (!column.sortable) return ''
  if (sortKey !== column.key) return 'fa-sort'
  return sortDirection === 'asc' ? 'fa-sort-up' : 'fa-sort-down'
}
</script>

<template>
  <div class="overflow-hidden rounded-xl border border-slate-200 bg-white/80 dark:border-white/[0.08] dark:bg-white/[0.03]">
    <div class="overflow-x-auto custom-scrollbar">
      <table class="min-w-full divide-y divide-slate-200 dark:divide-white/[0.06]">
        <thead class="bg-slate-50/80 dark:bg-white/[0.025]">
          <tr>
            <th
              v-for="column in columns"
              :key="column.key"
              scope="col"
              class="whitespace-nowrap px-4 text-xs font-bold uppercase text-slate-500 dark:text-[#8a8f98]"
              :class="[compact ? 'py-2' : 'py-3', column.align === 'right' ? 'text-right' : column.align === 'center' ? 'text-center' : 'text-left']"
            >
              <button
                v-if="column.sortable"
                type="button"
                class="inline-flex items-center gap-1.5 transition-colors hover:text-slate-900 dark:hover:text-[#f7f8f8]"
                @click="emit('sort', column.key)"
              >
                {{ column.label }}
                <i class="fa-solid text-[10px]" :class="sortIcon(column, sortKey, sortDirection)"></i>
              </button>
              <span v-else>{{ column.label }}</span>
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-white/[0.05]">
          <tr v-if="loading">
            <td :colspan="columns.length" class="px-4 py-8 text-center text-sm text-slate-500 dark:text-[#8a8f98]">
              <i class="fa-solid fa-spinner mr-2 animate-spin"></i>加载中
            </td>
          </tr>
          <tr v-else-if="!rows.length">
            <td :colspan="columns.length" class="px-4 py-8 text-center text-sm text-slate-500 dark:text-[#8a8f98]">
              {{ emptyText }}
            </td>
          </tr>
          <tr
            v-for="(row, index) in rows"
            v-else
            :key="row[rowKey] ?? index"
            class="transition-colors hover:bg-slate-50/80 dark:hover:bg-white/[0.035]"
            @click="emit('row-click', row)"
          >
            <td
              v-for="column in columns"
              :key="column.key"
              class="px-4 text-sm text-slate-700 dark:text-[#d0d6e0]"
              :class="[compact ? 'py-2' : 'py-3', column.align === 'right' ? 'text-right' : column.align === 'center' ? 'text-center' : 'text-left']"
            >
              <slot :name="`cell-${column.key}`" :row="row" :value="cellValue(row, column)">
                {{ cellValue(row, column) }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
