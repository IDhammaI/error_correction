<script setup>
/**
 * ErrorQuestionDetailPanel.vue
 * 错题库中间题目详情面板。
 */
import BaseButton from '@/components/base/BaseButton.vue'
import BaseEmptyState from '@/components/base/BaseEmptyState.vue'
import BasePanel from '@/components/base/BasePanel.vue'
import BasePanelTitle from '@/components/base/BasePanelTitle.vue'
import BasePopconfirm from '@/components/base/BasePopconfirm.vue'
import BaseTabs from '@/components/base/BaseTabs.vue'
import BaseTag from '@/components/base/BaseTag.vue'
import BaseToolbarButton from '@/components/base/BaseToolbarButton.vue'
import { formatOption, isHtml, sanitizeHtml } from '@/utils/index.js'

const props = defineProps({
  question: { type: Object, default: null },
  contentBlocks: { type: Array, default: () => [] },
  optionList: { type: Array, default: () => [] },
  knowledgeTags: { type: Array, default: () => [] },
  activeTab: { type: String, default: 'analysis' },
  detailTabs: { type: Array, default: () => [] },
  aiSummary: { type: String, default: '' },
})

const emit = defineEmits([
  'update:activeTab',
  'edit',
  'delete',
  'open-image',
  'open-detail',
  'open-chat',
  'start-practice',
  'back-to-list',
])

const statusTone = (status) => {
  if (status === '已掌握') return 'emerald'
  if (status === '复习中') return 'amber'
  return 'rose'
}

const setActiveTab = (value) => emit('update:activeTab', value)
</script>

<template>
  <BasePanel v-if="question" body-class="p-5" header-class="flex h-16 items-center px-5 py-3" footer-class="px-5 py-4">
    <template #header>
      <div class="flex w-full items-center justify-between gap-3">
        <BasePanelTitle icon="fa-file-lines">题目详情</BasePanelTitle>
        <div class="flex items-center gap-2">
          <BaseToolbarButton icon="fa-arrow-left-long" title="返回题目列表" @click="emit('back-to-list')">
            <span class="hidden sm:inline">返回列表</span>
          </BaseToolbarButton>
          <BaseToolbarButton icon="fa-pen" title="编辑题目" @click="emit('edit', question, 'question')" />
          <BasePopconfirm title="删除这道题？" description="删除后将从当前错题库永久移除。" confirm-text="删除" danger @confirm="emit('delete', question)">
            <BaseToolbarButton icon="fa-trash-can" variant="danger" title="删除题目" />
          </BasePopconfirm>
        </div>
      </div>
    </template>

        <div class="space-y-5">
          <div class="flex flex-wrap items-center gap-2">
            <BaseTag v-if="question.subject" tone="accent">{{ question.subject }}</BaseTag>
            <BaseTag v-for="tag in knowledgeTags.slice(0, 3)" :key="tag">{{ tag }}</BaseTag>
            <BaseTag :tone="statusTone(question.review_status || '待复习')">{{ question.review_status || '待复习' }}</BaseTag>
          </div>

          <div class="rounded-xl bg-gray-50/85 p-5 dark:bg-white/[0.035]">
            <template v-for="(block, index) in contentBlocks" :key="index">
              <div
                v-if="block.block_type === 'text' && isHtml(block.content)"
                v-html="sanitizeHtml(block.content)"
                class="question-rich mb-4 text-[15px] font-medium leading-8 text-gray-800 dark:text-[#d0d6e0]"
              ></div>
              <p
                v-else-if="block.block_type === 'text'"
                class="mb-4 text-[15px] font-medium leading-8 text-gray-800 dark:text-[#d0d6e0]"
              >
                {{ block.content }}
              </p>
              <img
                v-else-if="block.block_type === 'image'"
                :src="block.content"
                class="mb-4 max-h-72 max-w-full cursor-zoom-in rounded-xl object-contain shadow-sm shadow-black/[0.04] dark:shadow-black/20"
                @click="emit('open-image', block.content)"
              />
            </template>
          </div>

          <div v-if="optionList.length" class="grid gap-3 sm:grid-cols-2">
            <div
              v-for="(option, index) in optionList"
              :key="index"
              class="rounded-xl bg-gray-50/80 px-4 py-3 text-sm font-medium text-gray-700 dark:bg-white/[0.035] dark:text-[#d0d6e0]"
            >
              <span class="mr-2 text-gray-400">{{ String.fromCharCode(65 + index) }}.</span>
              {{ formatOption(option).replace(/^[A-Da-d][.、．]\s*/, '') }}
            </div>
          </div>

          <div class="rounded-xl bg-white/75 shadow-sm shadow-black/[0.03] dark:bg-white/[0.035] dark:shadow-black/20">
            <BaseTabs :model-value="activeTab" :items="detailTabs" @update:model-value="setActiveTab" />

            <div class="p-5">
              <div v-if="activeTab === 'analysis'" class="space-y-4">
                <div class="rounded-xl bg-gray-50/80 p-4 dark:bg-white/[0.035]">
                  <h4 class="mb-2 text-sm font-bold accent-text">
                    <i class="fa-solid fa-wand-magic-sparkles mr-1.5"></i>总结
                  </h4>
                  <p class="text-sm leading-7 text-gray-600 dark:text-[#b8bec8]">{{ aiSummary }}</p>
                </div>
                <div class="rounded-xl bg-gray-50/80 p-4 dark:bg-white/[0.035]">
                  <h4 class="mb-3 text-sm font-bold text-gray-900 dark:text-[#f7f8f8]">建议步骤</h4>
                  <ol class="space-y-2 text-sm leading-7 text-gray-600 dark:text-[#b8bec8]">
                    <li>1. 先复盘题干中的关键条件和对应知识点；</li>
                    <li>2. 对照答案解析，标记自己卡住的步骤；</li>
                    <li>3. 将题目状态改为复习中，并在掌握后标记为已掌握。</li>
                  </ol>
                </div>
              </div>

              <div v-else-if="activeTab === 'answer'" class="space-y-3">
                <p v-if="question.answer" class="whitespace-pre-wrap text-sm leading-7 text-gray-700 dark:text-[#d0d6e0]">
                  {{ question.answer }}
                </p>
                <BaseEmptyState v-else icon="fa-regular fa-circle-question" title="暂无答案解析" description="可以点击编辑，为这道题补充标准答案或解析。" />
              </div>

              <div v-else class="space-y-3">
                <p v-if="question.user_answer" class="whitespace-pre-wrap text-sm leading-7 text-gray-700 dark:text-[#d0d6e0]">
                  {{ question.user_answer }}
                </p>
                <BaseEmptyState v-else icon="fa-solid fa-camera" title="还没有作答记录" description="拍照、上传或手动记录你的答案和解题过程。" />
              </div>
            </div>
          </div>
        </div>

    <template #footer>
      <div class="flex flex-wrap items-center gap-3">
        <BaseButton size="sm" variant="primary" @click="emit('open-detail', question)">
          <i class="fa-solid fa-magnifying-glass-chart"></i>
          查看完整解析
        </BaseButton>
        <BaseButton size="sm" variant="secondary" @click="emit('open-chat', question)">
          <i class="fa-solid fa-comments"></i>
          AI 讲解
        </BaseButton>
        <BaseButton size="sm" variant="secondary" @click="emit('start-practice')">
          <i class="fa-solid fa-calendar-plus"></i>
          加入复习
        </BaseButton>
        <BaseButton size="sm" variant="secondary" disabled title="需要后端同类题生成接口">
          <i class="fa-solid fa-shuffle"></i>
          同类题
        </BaseButton>
      </div>
    </template>
  </BasePanel>

  <BasePanel v-else :scroll-body="false" body-class="grid h-full place-items-center p-6">
    <BaseEmptyState icon="fa-solid fa-file-circle-question" title="请选择一道题目" description="从左侧列表选择题目后，这里会展示题干、选项和解析。" />
  </BasePanel>
</template>

<style scoped>
.question-rich :deep(table) {
  @apply my-4 block w-full overflow-x-auto rounded-xl border border-gray-200 text-sm dark:border-white/[0.08];
}

.question-rich :deep(th) {
  @apply bg-gray-100 px-3 py-2 text-left font-bold dark:bg-white/[0.06];
}

.question-rich :deep(td) {
  @apply border-t border-gray-200 px-3 py-2 dark:border-white/[0.08];
}

.question-rich :deep(ul) {
  @apply my-2 list-disc pl-5;
}

.question-rich :deep(ol) {
  @apply my-2 list-decimal pl-5;
}
</style>
