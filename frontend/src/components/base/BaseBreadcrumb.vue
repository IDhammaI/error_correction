<script setup>
defineProps({
  items: { type: Array, default: () => [] },
})

function isCurrent(index, items) {
  return index === items.length - 1
}

function isInteractive(item, index, items) {
  return typeof item.onClick === 'function' && !isCurrent(index, items)
}

function activateItem(item) {
  if (typeof item.onClick === 'function') item.onClick(item)
}
</script>

<template>
  <nav class="flex min-w-0 items-center gap-2 text-sm" aria-label="Breadcrumb">
    <template v-for="(item, index) in items" :key="`${item.label}-${index}`">
      <component
        :is="isInteractive(item, index, items) ? 'button' : 'span'"
        type="button"
        class="inline-flex min-w-0 items-center gap-2 rounded-md outline-none transition-colors"
        :class="[
          isCurrent(index, items)
            ? 'text-gray-900 dark:text-[#f7f8f8]'
            : 'text-gray-500 dark:text-[#8a8f98]',
          isInteractive(item, index, items)
            ? 'cursor-pointer hover:text-gray-900 focus-visible:ring-2 focus-visible:ring-[rgb(var(--accent-rgb)/0.45)] dark:hover:text-[#f7f8f8]'
            : ''
        ]"
        @click="isInteractive(item, index, items) && activateItem(item)"
      >
        <i v-if="item.icon" class="fa-solid shrink-0 text-xs" :class="[item.icon, item.iconClass]"></i>
        <span
          class="min-w-0 truncate"
          :class="isCurrent(index, items) ? 'font-semibold' : 'font-medium'"
        >
          {{ item.label }}
        </span>
      </component>
      <i
        v-if="index < items.length - 1"
        class="fa-solid fa-chevron-right shrink-0 text-[9px] text-gray-400 dark:text-[#62666d]"
      ></i>
    </template>
  </nav>
</template>
