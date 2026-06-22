<script setup>
/**
 * ProviderSection.vue
 * API Provider 配置区块
 */
import BaseListGroup from '@/components/base/BaseListGroup.vue'
import BaseListItem from '@/components/base/BaseListItem.vue'
import BaseButton from '@/components/base/BaseButton.vue'

defineProps({
  icon: { type: String, default: '' },
  imgIcon: { type: String, default: '' },
  invertDark: { type: Boolean, default: false },
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  providers: { type: Array, default: () => [] },
  activeId: { type: [Number, String, null], default: null },
})

const emit = defineEmits(['add', 'toggle-active', 'edit', 'remove'])
</script>

<template>
  <div class="mb-8 last:mb-0">
    <!-- 区块标题 -->
    <div class="mb-4 flex items-center justify-between pl-1">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gray-50 dark:bg-white/[0.04] border border-gray-100 dark:border-white/[0.08]">
          <img v-if="imgIcon" :src="imgIcon" class="h-5 w-5 object-contain" :class="{ 'dark:invert': invertDark }" alt="icon" />
          <i v-else-if="icon" :class="icon" class="text-lg text-slate-600 dark:text-slate-400"></i>
        </div>
        <div>
          <h3 class="text-[15px] font-bold text-slate-900 dark:text-[#f7f8f8]">{{ title }}</h3>
          <p v-if="subtitle" class="text-xs text-slate-500 dark:text-slate-400">{{ subtitle }}</p>
        </div>
      </div>
      <BaseButton
        @click="emit('add')"
        variant="primary"
        size="sm"
        class="!h-8 !px-3 !rounded-lg !text-xs !font-bold"
      >
        <i class="fa-solid fa-plus text-[10px]"></i>
        添加
      </BaseButton>
    </div>

    <!-- 空状态 -->
    <div
      v-if="providers.length === 0"
      @click="emit('add')"
      class="group flex min-h-[56px] cursor-pointer items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50/80 transition-all hover:border-gray-300 hover:bg-gray-100 dark:border-white/[0.08] dark:bg-white/[0.035] dark:hover:border-white/[0.15] dark:hover:bg-white/[0.06]"
    >
      <div class="flex items-center gap-2 text-slate-400 transition-colors group-hover:text-slate-500 dark:text-slate-500 dark:group-hover:text-slate-400">
        <i class="fa-solid fa-plus-circle text-sm"></i>
        <span class="text-xs font-medium">尚未配置，点击此处快速添加</span>
      </div>
    </div>

    <!-- Provider 列表 -->
    <div v-else class="flex flex-col gap-3">
      <div
        v-for="(provider, idx) in providers"
        :key="provider.id"
        class="group relative flex min-h-[56px] items-center justify-between rounded-xl border border-gray-100 bg-gray-50/80 px-4 py-2 transition-all hover:bg-gray-100 dark:border-white/[0.08] dark:bg-white/[0.035] dark:hover:bg-white/[0.06]"
      >
        <div class="flex items-center gap-3">
          <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gray-50 dark:bg-white/[0.04]">
            <i class="fa-solid fa-plug text-sm text-slate-500 dark:text-slate-400"></i>
          </div>
          <div class="flex-1 min-w-0">
            <h4 class="truncate text-[15px] font-bold text-slate-900 dark:text-[#f7f8f8]">
              {{ provider.name || '未命名' }}
            </h4>
            <p v-if="provider.model_name" class="mt-0.5 truncate text-xs text-slate-500 dark:text-slate-400">
              {{ provider.model_name }}
            </p>
          </div>
        </div>

        <div class="flex items-center gap-1.5 pl-4 border-l border-gray-50 dark:border-white/[0.04]">
          <button
            @click.stop="emit('edit', provider, idx)"
            class="flex h-7 w-7 items-center justify-center rounded-md text-slate-400 transition-colors hover:text-slate-700 dark:hover:text-slate-200"
            title="编辑"
          >
            <i class="fa-regular fa-pen-to-square text-[13px]"></i>
          </button>
          <button
            @click.stop="emit('remove', idx)"
            class="flex h-7 w-7 items-center justify-center rounded-md text-slate-400 transition-colors hover:text-rose-500"
            title="删除"
          >
            <i class="fa-regular fa-trash-can text-[13px]"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
