<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  modelValue: { type: [String, Number], default: '' },
  defaultExpanded: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue', 'select'])
const expanded = ref(new Set(props.defaultExpanded))

function hasChildren(item) {
  return Array.isArray(item.children) && item.children.length > 0
}

function toggle(item) {
  if (!hasChildren(item)) return
  const next = new Set(expanded.value)
  if (next.has(item.value)) next.delete(item.value)
  else next.add(item.value)
  expanded.value = next
}

function select(item) {
  emit('update:modelValue', item.value)
  emit('select', item)
}

const isExpanded = computed(() => item => expanded.value.has(item.value))
</script>

<template>
  <ul class="space-y-1">
    <li v-for="item in items" :key="item.value">
      <div class="flex items-center gap-1">
        <button
          type="button"
          class="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-white/[0.06] dark:hover:text-[#d0d6e0]"
          :class="hasChildren(item) ? '' : 'invisible'"
          @click="toggle(item)"
        >
          <i class="fa-solid fa-chevron-right text-[10px] transition-transform" :class="isExpanded(item) ? 'rotate-90' : ''"></i>
        </button>
        <button
          type="button"
          class="flex min-h-8 min-w-0 flex-1 items-center gap-2 rounded-lg px-2 text-left text-sm transition-colors"
          :class="modelValue === item.value ? 'accent-bg-soft accent-text' : 'text-slate-700 hover:bg-slate-100 dark:text-[#d0d6e0] dark:hover:bg-white/[0.05]'"
          @click="select(item)"
        >
          <i v-if="item.icon" class="fa-solid shrink-0 text-xs" :class="item.icon"></i>
          <span class="min-w-0 truncate">{{ item.label }}</span>
        </button>
      </div>
      <BaseTree
        v-if="hasChildren(item) && isExpanded(item)"
        class="ml-7 mt-1"
        :model-value="modelValue"
        :items="item.children"
        :default-expanded="defaultExpanded"
        @update:model-value="emit('update:modelValue', $event)"
        @select="emit('select', $event)"
      />
    </li>
  </ul>
</template>
