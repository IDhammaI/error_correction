<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useOverlay } from '@/composables/useOverlay.js'

const props = defineProps({
  open: { type: Boolean, default: false },
  items: { type: Array, default: () => [] },
  placeholder: { type: String, default: '搜索命令' },
})

const emit = defineEmits(['update:open', 'select'])
const query = ref('')
const activeIndex = ref(0)
const inputRef = ref(null)
const { overlayRef, overlayStyle, backdropStyle } = useOverlay(
  computed(() => props.open),
  { onClose: close },
)

const filteredItems = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  if (!keyword) return props.items
  return props.items.filter(item =>
    [item.label, item.description, item.group]
      .filter(Boolean)
      .some(value => String(value).toLowerCase().includes(keyword)),
  )
})

watch(() => props.open, async (value) => {
  if (!value) return
  query.value = ''
  activeIndex.value = 0
  await nextTick()
  inputRef.value?.focus()
})

watch(filteredItems, () => {
  activeIndex.value = 0
})

function close() {
  emit('update:open', false)
}

function move(delta) {
  if (!filteredItems.value.length) return
  activeIndex.value = (activeIndex.value + delta + filteredItems.value.length) % filteredItems.value.length
}

function select(item = filteredItems.value[activeIndex.value]) {
  if (!item) return
  emit('select', item)
  item.action?.()
  close()
}
</script>

<template>
  <Teleport to="body">
    <Transition enter-active-class="transition-opacity duration-150" enter-from-class="opacity-0" leave-active-class="transition-opacity duration-100" leave-to-class="opacity-0">
      <div v-if="open" class="fixed inset-0 bg-black/45 backdrop-blur-sm" :style="backdropStyle" @click="close"></div>
    </Transition>
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="-translate-y-2 scale-[0.98] opacity-0"
      enter-to-class="translate-y-0 scale-100 opacity-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="translate-y-0 scale-100 opacity-100"
      leave-to-class="-translate-y-2 scale-[0.98] opacity-0"
    >
      <div
        v-if="open"
        ref="overlayRef"
        tabindex="-1"
        class="fixed left-1/2 top-20 w-[calc(100vw-2rem)] max-w-2xl -translate-x-1/2 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-white/[0.08] dark:bg-[#17171a]"
        :style="overlayStyle"
      >
        <div class="flex h-14 items-center gap-3 border-b border-slate-200/70 px-4 dark:border-white/[0.06]">
          <i class="fa-solid fa-magnifying-glass text-sm text-slate-400"></i>
          <input
            ref="inputRef"
            v-model="query"
            class="h-full min-w-0 flex-1 bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400 dark:text-[#f7f8f8] dark:placeholder:text-[#62666d]"
            :placeholder="placeholder"
            @keydown.down.prevent="move(1)"
            @keydown.up.prevent="move(-1)"
            @keydown.enter.prevent="select()"
            @keydown.esc.prevent="close"
          />
          <kbd class="rounded border border-slate-200 px-1.5 py-0.5 text-[10px] font-semibold text-slate-400 dark:border-white/[0.08]">Esc</kbd>
        </div>
        <div class="max-h-[24rem] overflow-y-auto p-2 custom-scrollbar">
          <button
            v-for="(item, index) in filteredItems"
            :key="item.id || item.label"
            type="button"
            class="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors"
            :class="index === activeIndex ? 'accent-bg-soft' : 'hover:bg-slate-100 dark:hover:bg-white/[0.05]'"
            @mouseenter="activeIndex = index"
            @click="select(item)"
          >
            <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500 dark:bg-white/[0.06] dark:text-[#8a8f98]">
              <i class="fa-solid text-sm" :class="item.icon || 'fa-bolt'"></i>
            </span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-sm font-semibold text-slate-900 dark:text-[#f7f8f8]">{{ item.label }}</span>
              <span v-if="item.description" class="mt-0.5 block truncate text-xs text-slate-500 dark:text-[#8a8f98]">{{ item.description }}</span>
            </span>
            <span v-if="item.group" class="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-500 dark:bg-white/[0.06] dark:text-[#8a8f98]">{{ item.group }}</span>
          </button>
          <div v-if="!filteredItems.length" class="px-4 py-10 text-center text-sm text-slate-500 dark:text-[#8a8f98]">
            没有匹配的命令
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
