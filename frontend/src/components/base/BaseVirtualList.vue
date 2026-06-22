<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  itemHeight: { type: Number, default: 44 },
  height: { type: Number, default: 280 },
  overscan: { type: Number, default: 4 },
})

const scrollTop = ref(0)

const visibleRange = computed(() => {
  const start = Math.max(0, Math.floor(scrollTop.value / props.itemHeight) - props.overscan)
  const count = Math.ceil(props.height / props.itemHeight) + props.overscan * 2
  const end = Math.min(props.items.length, start + count)
  return { start, end }
})

const visibleItems = computed(() =>
  props.items.slice(visibleRange.value.start, visibleRange.value.end).map((item, index) => ({
    item,
    index: visibleRange.value.start + index,
  })),
)

function onScroll(event) {
  scrollTop.value = event.target.scrollTop
}
</script>

<template>
  <div class="overflow-auto rounded-xl border border-slate-200 bg-white/70 custom-scrollbar dark:border-white/[0.08] dark:bg-white/[0.025]" :style="{ height: `${height}px` }" @scroll="onScroll">
    <div class="relative" :style="{ height: `${items.length * itemHeight}px` }">
      <div
        v-for="{ item, index } in visibleItems"
        :key="item.id ?? index"
        class="absolute left-0 right-0"
        :style="{ height: `${itemHeight}px`, transform: `translateY(${index * itemHeight}px)` }"
      >
        <slot :item="item" :index="index">
          <div class="flex h-full items-center border-b border-slate-100 px-4 text-sm text-slate-700 dark:border-white/[0.05] dark:text-[#d0d6e0]">
            {{ item.label || item }}
          </div>
        </slot>
      </div>
    </div>
  </div>
</template>
