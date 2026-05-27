<script setup>
/**
 * ViewSettingsPopover.vue
 * app 内通用的视图筛选与设置弹出框。
 */
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useClickOutside } from '@/composables/useClickOutside.js'
import BaseSearchableSelect from '@/components/base/BaseSearchableSelect.vue'

const props = defineProps({
    modelValue: { type: Boolean, default: false },
    filters: { type: Object, required: true },
    subjects: { type: Array, default: () => [] },
    questionTypes: { type: Array, default: () => [] },
    tagNames: { type: Array, default: () => [] },
    selectedTags: { type: Set, required: true },
    showReviewStatus: { type: Boolean, default: true },
    showQuestionType: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue', 'toggle-tag', 'reset'])

const popoverRef = ref(null)
const tagFilterValue = computed({
    get() {
        return props.filters.knowledge_tag ?? props.filters.tag ?? []
    },
    set(value) {
        if ('knowledge_tag' in props.filters) props.filters.knowledge_tag = value
        else props.filters.tag = value
    },
})

// 重置逻辑
const handleReset = () => {
    props.filters.subject = ''
    props.filters.question_type = ''
    props.filters.review_status = ''
    if ('knowledge_tag' in props.filters) props.filters.knowledge_tag = []
    if ('tag' in props.filters) props.filters.tag = []
    emit('reset')
}

// 关闭逻辑
const close = () => {
    emit('update:modelValue', false)
}

useClickOutside('.linear-popover-wrapper', () => {
    if (props.modelValue) close()
})

const handleKeydown = (e) => {
    if (e.key === 'Escape' && props.modelValue) {
        close()
    }
}

onMounted(() => {
    document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
    document.removeEventListener('keydown', handleKeydown)
})

const labelClass = "font-medium text-gray-500 dark:text-[#8a8f98] shrink-0 w-16"

</script>

<template>
    <Transition name="popover">
        <div v-if="modelValue"
            class="linear-popover-wrapper absolute right-0 top-full mt-1.5 z-50 w-72 origin-top-right rounded-xl bg-white dark:bg-[#232429] border border-gray-200 dark:border-white/[0.08] shadow-[0_4px_24px_rgba(0,0,0,0.08)] dark:shadow-[0_4px_24px_rgba(0,0,0,0.4)] p-1.5 flex flex-col gap-0.5"
            ref="popoverRef">

            <!-- 1. 复习状态 (Tab 切换风格) - 置顶 -->
            <div v-if="showReviewStatus" class="flex flex-col gap-2 py-2 px-2">
                <span
                    class="text-[11px] font-semibold text-gray-400 dark:text-[#62666d] uppercase tracking-wider">复习状态</span>
                <div role="tablist"
                    class="flex p-0.5 rounded-lg bg-gray-100/80 dark:bg-white/[0.04] border border-gray-200/50 dark:border-white/[0.06]">
                    <button
                        v-for="status in [{ v: '', l: '全部' }, { v: '待复习', l: '待复习' }, { v: '复习中', l: '复习中' }, { v: '已掌握', l: '已掌握' }]"
                        :key="status.v" role="tab" :aria-selected="filters.review_status === status.v"
                        @click="filters.review_status = status.v"
                        class="flex-1 flex items-center justify-center py-1 rounded-[6px] text-[12px] font-medium transition-all duration-200"
                        :class="filters.review_status === status.v
                            ? 'bg-white dark:bg-white/[0.08] accent-text dark:text-[#f7f8f8] shadow-[0_1px_3px_rgba(0,0,0,0.1)] dark:shadow-none border border-gray-200/50 dark:border-white/[0.1]'
                            : 'text-gray-500 dark:text-[#8a8f98] hover:text-gray-700 dark:hover:text-[#d0d6e0] border border-transparent'">
                        {{ status.l }}
                    </button>
                </div>
            </div>

            <!-- 分割线 -->
            <div v-if="showReviewStatus" class="h-px bg-gray-100 dark:bg-white/[0.06] my-1 mx-1"></div>

            <!-- 2. 学科 -->
            <div class="flex items-center justify-between px-2.5 py-1.5 rounded-md transition-colors text-[13px]">
                <span class="font-medium text-gray-500 dark:text-[#8a8f98] shrink-0 w-16">学科</span>
                <div class="flex-1 max-w-[160px]">
                    <BaseSearchableSelect v-model="filters.subject" :options="subjects" placeholder="全部学科" search-placeholder="搜索学科" multiple />
                </div>
            </div>

            <!-- 3. 题型 -->
            <div v-if="showQuestionType"
                class="flex items-center justify-between px-2.5 py-1.5 rounded-md transition-colors text-[13px]">
                <span class="font-medium text-gray-500 dark:text-[#8a8f98] shrink-0 w-16">题型</span>
                <div class="flex-1 max-w-[160px]">
                    <BaseSearchableSelect v-model="filters.question_type" :options="questionTypes" placeholder="全部题型" search-placeholder="搜索题型" multiple />
                </div>
            </div>

            <!-- 分割线 (如果有标签) -->
            <div v-if="tagNames?.length" class="h-px bg-gray-100 dark:bg-white/[0.06] my-1 mx-1"></div>

            <!-- 4. 知识点标签 -->
            <div v-if="tagNames?.length" class="flex flex-col gap-2 py-2 px-2">
                <span
                    class="text-[11px] font-semibold text-gray-400 dark:text-[#62666d] uppercase tracking-wider">知识点过滤</span>
                <BaseSearchableSelect
                    v-model="tagFilterValue"
                    :options="tagNames"
                    placeholder="全部知识点"
                    search-placeholder="搜索知识点"
                    width-class="w-full"
                    multiple
                />
            </div>

            <!-- 分割线 -->
            <div class="h-px bg-gray-100 dark:bg-white/[0.06] my-1 mx-1"></div>

            <!-- 5. 重置按钮 -->
            <div class="flex items-center justify-end px-2 py-1.5">
                <button @click="handleReset"
                    class="px-3 py-1.5 rounded-md text-[12px] font-medium text-gray-500 dark:text-[#8a8f98] hover:bg-gray-100 dark:hover:bg-white/[0.06] hover:text-gray-700 dark:hover:text-[#d0d6e0] transition-colors">
                    重置
                </button>
            </div>
        </div>
    </Transition>
</template>

<style scoped>
/* 核心动画要求 */
.popover-enter-active,
.popover-leave-active {
    transition: all 150ms cubic-bezier(0.2, 0, 0, 1);
}

.popover-enter-from,
.popover-leave-to {
    opacity: 0;
    transform: scale(0.95) translateY(4px);
}

.popover-enter-to,
.popover-leave-from {
    opacity: 1;
    transform: scale(1) translateY(0);
}
</style>
