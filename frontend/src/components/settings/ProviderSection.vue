<script setup>
/**
 * ProviderSection.vue
 * API Provider 配置区块
 */
import BaseListGroup from '@/components/base/BaseListGroup.vue'
import BaseListItem from '@/components/base/BaseListItem.vue'

defineProps({
  icon: { type: String, default: '' },
  imgIcon: { type: String, default: '' },
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  providers: { type: Array, default: () => [] },
  activeId: { type: [Number, String, null], default: null },
})

const emit = defineEmits(['add', 'toggle-active', 'edit', 'remove'])
</script>

<template>
  <div class="mb-10 last:mb-0">
    <!-- 区块标题 -->
    <div class="mb-4 flex items-center justify-between pl-1">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gray-50 dark:bg-white/[0.04] border border-gray-100 dark:border-white/[0.08]">
          <img v-if="imgIcon" :src="imgIcon" class="h-5 w-5 object-contain" :class="{'dark:invert': imgIcon.includes('provider-openai.svg')}" alt="icon" />
          <i v-else-if="icon" :class="icon" class="text-lg text-slate-600 dark:text-slate-400"></i>
        </div>
        <div>
          <h3 class="text-[15px] font-bold text-slate-900 dark:text-[#f7f8f8]">{{ title }}</h3>
          <p v-if="subtitle" class="text-xs text-slate-500 dark:text-slate-400">{{ subtitle }}</p>
        </div>
      </div>
      <button
        @click="emit('add')"
        class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-600 transition-all hover:bg-gray-50 dark:border-white/[0.08] dark:bg-white/[0.04] dark:text-slate-400 dark:hover:bg-white/[0.08] dark:hover:text-[#f7f8f8]"
      >
        <i class="fa-solid fa-plus text-[10px]"></i>
        添加
      </button>
    </div>

    <!-- 空状态 -->
    <div v-if="providers.length === 0" class="flex min-h-[56px] items-center justify-center rounded-2xl border border-dashed border-gray-200 dark:border-white/[0.08]">
      <div class="flex items-center gap-2">
        <i class="fa-solid fa-plug text-sm text-slate-300 dark:text-slate-600"></i>
        <span class="text-xs font-medium text-slate-400 dark:text-slate-500">尚未配置，点击右侧按钮添加</span>
      </div>
    </div>

    <!-- Provider 列表 -->
    <BaseListGroup v-else>
      <BaseListItem
        v-for="(provider, idx) in providers" 
        :key="provider.id"
        :label="provider.name || '未命名'"
        class="group"
        @click="emit('toggle-active', provider.id)"
      >
        <template #icon>
          <div
            class="flex h-4 w-4 shrink-0 items-center justify-center rounded-full border-[1.5px] transition-all"
            :class="activeId === provider.id
              ? 'border-slate-900 bg-slate-900 dark:border-[#f7f8f8] dark:bg-[#f7f8f8]'
              : 'border-gray-300 dark:border-white/20'"
          >
            <i v-if="activeId === provider.id" class="fa-solid fa-check text-[8px] text-white dark:text-[#1b1b1d]"></i>
          </div>
        </template>

        <template #right>
          <div class="flex items-center gap-4 px-3 py-1.5">
            <!-- 状态标签 -->
            <div class="flex items-center gap-2">
              <span v-if="activeId === provider.id" class="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-bold text-gray-700 ring-1 ring-inset ring-gray-500/10 dark:bg-white/10 dark:text-[#f7f8f8] dark:ring-white/20">
                使用中
              </span>
              <span v-else-if="provider.api_key_set" class="inline-flex items-center rounded-full bg-gray-50 px-2 py-0.5 text-[10px] font-bold text-gray-500 ring-1 ring-inset ring-gray-500/20 dark:bg-white/5 dark:text-slate-400 dark:ring-white/10">
                已配置
              </span>
            </div>

            <!-- 操作按钮 -->
            <div class="flex items-center gap-1">
              <button
                @click.stop="emit('edit', provider, idx)"
                class="flex h-7 w-7 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-gray-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-slate-300"
                title="设置"
              >
                <i class="fa-solid fa-gear text-xs"></i>
              </button>
              <button
                @click.stop="emit('remove', idx)"
                class="flex h-7 w-7 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-rose-50 hover:text-rose-500 dark:hover:bg-rose-500/10"
                title="删除"
              >
                <i class="fa-solid fa-trash-can text-xs"></i>
              </button>
            </div>
          </div>
        </template>
      </BaseListItem>
    </BaseListGroup>
  </div>
</template>
