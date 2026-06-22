<script setup>
import { computed, ref } from 'vue'

import ContentPanel from '@/components/features/app/layout/ContentPanel.vue'
import BaseAlert from '@/components/base/BaseAlert.vue'
import BaseAccordion from '@/components/base/BaseAccordion.vue'
import BaseAvatar from '@/components/base/BaseAvatar.vue'
import BaseBadge from '@/components/base/BaseBadge.vue'
import BaseBreadcrumb from '@/components/base/BaseBreadcrumb.vue'
import BaseBreadcrumbItem from '@/components/base/BaseBreadcrumbItem.vue'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseCalendar from '@/components/base/BaseCalendar.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import BaseCheckbox from '@/components/base/BaseCheckbox.vue'
import BaseCodeBlock from '@/components/base/BaseCodeBlock.vue'
import BaseCombobox from '@/components/base/BaseCombobox.vue'
import BaseCommandPalette from '@/components/base/BaseCommandPalette.vue'
import BaseCopyButton from '@/components/base/BaseCopyButton.vue'
import BaseDataTable from '@/components/base/BaseDataTable.vue'
import BaseDatePicker from '@/components/base/BaseDatePicker.vue'
import BaseDivider from '@/components/base/BaseDivider.vue'
import BaseDrawer from '@/components/base/BaseDrawer.vue'
import BaseDropdown from '@/components/base/BaseDropdown.vue'
import BaseEmptyState from '@/components/base/BaseEmptyState.vue'
import BaseForm from '@/components/base/BaseForm.vue'
import BaseFormItem from '@/components/base/BaseFormItem.vue'
import BaseGhostButton from '@/components/base/BaseGhostButton.vue'
import BaseInput from '@/components/base/BaseInput.vue'
import BaseListGroup from '@/components/base/BaseListGroup.vue'
import BaseListItem from '@/components/base/BaseListItem.vue'
import BaseLoading from '@/components/base/BaseLoading.vue'
import BaseLogo from '@/components/base/BaseLogo.vue'
import BaseKbd from '@/components/base/BaseKbd.vue'
import BaseMenu from '@/components/base/BaseMenu.vue'
import BaseModal from '@/components/base/BaseModal.vue'
import BaseNumberInput from '@/components/base/BaseNumberInput.vue'
import BasePagination from '@/components/base/BasePagination.vue'
import BasePanel from '@/components/base/BasePanel.vue'
import BasePanelTitle from '@/components/base/BasePanelTitle.vue'
import BasePopconfirm from '@/components/base/BasePopconfirm.vue'
import BasePopover from '@/components/base/BasePopover.vue'
import BaseProgress from '@/components/base/BaseProgress.vue'
import BaseRadioGroup from '@/components/base/BaseRadioGroup.vue'
import BaseResizablePanels from '@/components/base/BaseResizablePanels.vue'
import BaseSearchableSelect from '@/components/base/BaseSearchableSelect.vue'
import BaseSearchInput from '@/components/base/BaseSearchInput.vue'
import BaseSegmented from '@/components/base/BaseSegmented.vue'
import BaseSelect from '@/components/base/BaseSelect.vue'
import BaseSkeleton from '@/components/base/BaseSkeleton.vue'
import BaseSlider from '@/components/base/BaseSlider.vue'
import BaseStat from '@/components/base/BaseStat.vue'
import BaseStepper from '@/components/base/BaseStepper.vue'
import BaseStatusPill from '@/components/base/BaseStatusPill.vue'
import BaseSurface from '@/components/base/BaseSurface.vue'
import BaseSwitch from '@/components/base/BaseSwitch.vue'
import BaseTabs from '@/components/base/BaseTabs.vue'
import BaseTable from '@/components/base/BaseTable.vue'
import BaseTag from '@/components/base/BaseTag.vue'
import BaseTextarea from '@/components/base/BaseTextarea.vue'
import BaseTimePicker from '@/components/base/BaseTimePicker.vue'
import BaseToastContainer from '@/components/base/BaseToastContainer.vue'
import BaseToolbarButton from '@/components/base/BaseToolbarButton.vue'
import BaseTooltip from '@/components/base/BaseTooltip.vue'
import BaseTooltipProvider from '@/components/base/BaseTooltipProvider.vue'
import BaseTree from '@/components/base/BaseTree.vue'
import BaseVirtualList from '@/components/base/BaseVirtualList.vue'
import ImageModal from '@/components/base/ImageModal.vue'
import BaseUpload from '@/components/base/BaseUpload.vue'
import {
  BASE_COMPONENT_API_DOCS,
  BASE_COMPONENT_COUNT,
  BASE_COMPONENT_GROUPS,
  BASE_COMPONENT_GROUP_SUMMARY,
} from '@/components/base/registry.js'

const activeGroup = ref('overview')
const catalogSearch = ref('')
const tab = ref('props')
const segmented = ref('light')
const selectValue = ref('数学')
const searchableValue = ref(['函数', '几何'])
const search = ref('')
const inputValue = ref('错题订正')
const password = ref('123456')
const switchOn = ref(true)
const checkboxValue = ref(['wrongbook'])
const radioValue = ref('compact')
const textareaValue = ref('Keep the explanation concise and cite the key formula.')
const numberValue = ref(30)
const dateValue = ref('2026-06-15')
const timeValue = ref('19:30')
const uploadFiles = ref([])
const sliderValue = ref(64)
const stepValue = ref('review')
const menuValue = ref('components')
const calendarValue = ref('2026-06-15')
const comboboxValue = ref('geometry')
const treeValue = ref('components')
const panelSize = ref(42)
const page = ref(3)
const modalOpen = ref(false)
const drawerOpen = ref(false)
const commandPaletteOpen = ref(false)
const popoverOpen = ref(false)
const alertVisible = ref(true)
const imageModalOpen = ref(false)
const imageScale = ref(1)
const loadingPreview = ref(false)
const dropdownOpen = ref(false)
const toastId = ref(2)
const toasts = ref([
  { id: 1, type: 'success', title: '保存成功', description: '组件状态已经同步到预览面板。' },
])

const componentGroups = BASE_COMPONENT_GROUP_SUMMARY
const catalogGroups = BASE_COMPONENT_GROUPS

const subjects = ['语文', '数学', '英语', '物理', '化学']
const tags = ['函数', '几何', '方程', '力学', '电学', '阅读理解', '作文']
const comboboxOptions = [
  { value: 'function', label: '函数' },
  { value: 'geometry', label: '几何' },
  { value: 'mechanics', label: '力学' },
  { value: 'reading', label: '阅读理解' },
]
const breadcrumbItems = [
  { label: '工作台', to: '/app/workspace' },
  { label: '组件预览' },
]
const tabItems = [
  { value: 'props', label: 'Props', icon: 'fa-sliders', badge: '12' },
  { value: 'states', label: '状态', icon: 'fa-layer-group' },
  { value: 'slots', label: '插槽', icon: 'fa-puzzle-piece' },
]
const segmentedOptions = [
  { value: 'light', label: '浅色', icon: 'fa-sun' },
  { value: 'dark', label: '深色', icon: 'fa-moon' },
  { value: 'auto', label: '跟随', icon: 'fa-circle-half-stroke' },
]
const stepperSteps = [
  { value: 'upload', label: '上传', description: '选择文件或图片' },
  { value: 'review', label: '检查', description: '确认 OCR 结果' },
  { value: 'save', label: '保存', description: '写入错题库' },
]
const menuItems = [
  { value: 'overview', label: '总览', icon: 'fa-gauge-high' },
  { value: 'components', label: '组件', icon: 'fa-cubes', badge: '42' },
  { value: 'tokens', label: 'Token', icon: 'fa-palette' },
  { value: 'disabled', label: '禁用项', icon: 'fa-lock', disabled: true },
]
const treeItems = [
  {
    value: 'base',
    label: 'Base',
    icon: 'fa-folder',
    children: [
      { value: 'components', label: 'Components', icon: 'fa-cubes' },
      { value: 'tokens', label: 'Tokens', icon: 'fa-palette' },
    ],
  },
  {
    value: 'features',
    label: 'Features',
    icon: 'fa-folder',
    children: [
      { value: 'workspace', label: 'Workspace', icon: 'fa-wand-magic-sparkles' },
      { value: 'settings', label: 'Settings', icon: 'fa-gear' },
    ],
  },
]
const virtualItems = Array.from({ length: 1000 }, (_, index) => ({
  id: index + 1,
  label: `虚拟列表项 ${index + 1}`,
  description: `只渲染视口附近的第 ${index + 1} 项`,
}))
const codeSample = `{
  "component": "BaseCodeBlock",
  "copyable": true,
  "language": "json"
}`
const radioOptions = [
  { value: 'compact', label: 'Compact', description: 'Dense controls for work surfaces.' },
  { value: 'comfortable', label: 'Comfortable', description: 'More breathing room for reading.' },
]
const accordionValue = ref('table')
const accordionItems = [
  { value: 'table', label: '表格组件', content: 'BaseTable 负责稳定渲染，BaseDataTable 增加搜索、排序和分页。' },
  { value: 'overlay', label: '浮层组件', content: 'BasePopover 和 BaseCommandPalette 用于轻量浮层与全局命令。' },
  { value: 'identity', label: '身份组件', content: 'BaseAvatar 支持图片、姓名缩写和图标兜底。' },
]
const tableColumns = [
  { key: 'name', label: '组件', sortable: true },
  { key: 'category', label: '分类', sortable: true },
  { key: 'status', label: '状态', sortable: true },
  { key: 'coverage', label: '覆盖率', align: 'right', sortable: true },
]
const tableRows = [
  { id: 1, name: 'BaseTable', category: '数据展示', status: '已完成', coverage: 90 },
  { id: 2, name: 'BasePopover', category: '浮层', status: '已完成', coverage: 82 },
  { id: 3, name: 'BaseAvatar', category: '展示', status: '已完成', coverage: 78 },
  { id: 4, name: 'BaseAccordion', category: '内容组织', status: '已完成', coverage: 84 },
  { id: 5, name: 'BaseCommandPalette', category: '导航', status: '已完成', coverage: 75 },
  { id: 6, name: 'BaseDataTable', category: '数据展示', status: '已完成', coverage: 88 },
]
const apiDocColumns = [
  { key: 'component', label: '组件', sortable: true },
  { key: 'props', label: '核心 Props' },
  { key: 'emits', label: 'Emits' },
  { key: 'slots', label: 'Slots' },
]
const apiDocs = BASE_COMPONENT_API_DOCS
const commandItems = [
  { id: 'workspace', label: '打开工作台', description: '进入错题录入流程', icon: 'fa-wand-magic-sparkles', group: '导航' },
  { id: 'toast', label: '触发成功通知', description: '展示全局 Toast', icon: 'fa-circle-check', group: '反馈', action: () => pushDemoToast('success') },
  { id: 'drawer', label: '打开抽屉', description: '展示 BaseDrawer', icon: 'fa-window-restore', group: '浮层', action: () => { drawerOpen.value = true } },
  { id: 'loading', label: '预览 Loading', description: '展示全局加载遮罩', icon: 'fa-spinner', group: '反馈', action: showLoadingPreview },
]
const statusRows = [
  { label: '在线', ok: true },
  { label: '处理中', loading: true },
  { label: '待配置', placeholder: true },
  { label: '失败' },
]
const plannedComponents = []
const componentDescriptions = {
  BaseAccordion: '折叠内容、FAQ 和配置分组。',
  BaseAlert: '页面内提示、成功、警告和错误反馈。',
  BaseAvatar: '用户头像、姓名缩写和图标兜底。',
  BaseBadge: '角标、红点和数量提示。',
  BaseButton: '主要操作、次要操作和链接操作。',
  BaseCalendar: '日历选择和日期面板。',
  BaseCheckbox: '布尔选择、多选和中间态。',
  BaseCombobox: '可搜索选择器，支持键盘选择。',
  BaseCommandPalette: '全局命令搜索和快捷动作。',
  BaseDataTable: '搜索、排序、分页的数据表格。',
  BaseDrawer: '侧边详情、筛选和表单浮层。',
  BaseForm: '表单容器、提交和加载状态。',
  BaseInput: '文本输入、密码输入和错误状态。',
  BaseModal: '居中弹窗和焦点管理。',
  BasePopover: '轻量说明、筛选和表单浮层。',
  BaseTable: '基础表格渲染和排序事件。',
  BaseTooltip: '悬停说明和全局浮层配置。',
  BaseTree: '层级目录和树形选择。',
  BaseVirtualList: '大列表虚拟渲染。',
}

const groupMeta = {
  layout: { icon: 'fa-layer-group', subtitle: '页面框架、容器和分隔结构' },
  form: { icon: 'fa-keyboard', subtitle: '输入、选择、上传和表单状态' },
  feedback: { icon: 'fa-window-restore', subtitle: '弹窗、通知、浮层和进度反馈' },
  display: { icon: 'fa-shapes', subtitle: '信息展示、数据呈现和空状态' },
  navigation: { icon: 'fa-compass', subtitle: '导航、菜单、分页和快捷操作' },
}

const catalogSections = computed(() => {
  const keyword = catalogSearch.value.trim().toLowerCase()
  return catalogGroups
    .map(group => ({
      ...group,
      components: group.components.filter(name => {
        if (!keyword) return true
        return `${name} ${componentLabel(name)} ${componentDescription(name)}`.toLowerCase().includes(keyword)
      }),
    }))
    .filter(group => group.components.length > 0)
})
const businessComponents = [
  { name: 'QuestionCard', desc: '题目卡片，依赖题目数据' },
  { name: 'QuestionList', desc: '题目列表，依赖分页与选择状态' },
  { name: 'ProviderDialog', desc: '模型供应商配置弹窗' },
  { name: 'ErrorQuestionDetailPanel', desc: '错题详情面板' },
  { name: 'NoteDetailPanel', desc: '笔记详情面板' },
  { name: 'FileUploader', desc: '上传工作流组件' },
  { name: 'StepIndicator', desc: '工作流步骤指示器' },
  { name: 'ModelProviderSelect', desc: '模型选择业务控件' },
]

const filteredGroups = computed(() => {
  const keyword = search.value.trim().toLowerCase()
  if (!keyword) return componentGroups
  return componentGroups.filter(group => group.label.toLowerCase().includes(keyword) || group.id.includes(keyword))
})

function pushDemoToast(type = 'info') {
  toastId.value += 1
  toasts.value = [
    ...toasts.value,
    {
      id: toastId.value,
      type,
      title: type === 'error' ? '操作失败' : '预览通知',
      description: type === 'error' ? '这是错误状态的 Toast 样式。' : '这是组件库的全局通知样式。',
      action: { label: '知道了' },
    },
  ].slice(-3)
}

function dismissToast(id) {
  toasts.value = toasts.value.filter(toast => toast.id !== id)
}

function showLoadingPreview() {
  loadingPreview.value = true
  window.setTimeout(() => {
    loadingPreview.value = false
  }, 1400)
}

function componentLabel(name) {
  return name === 'ImageModal' ? 'ImageModal' : name.replace(/^Base/, '')
}

function componentDescription(name) {
  return componentDescriptions[name] || '基础组件库中的可复用 UI 单元。'
}

function componentIcon(name) {
  if (/Table|List|Tree/.test(name)) return 'fa-table-list'
  if (/Modal|Drawer|Popover|Tooltip|Command/.test(name)) return 'fa-window-restore'
  if (/Input|Select|Combobox|Form|Checkbox|Radio|Slider|Upload|Picker/.test(name)) return 'fa-keyboard'
  if (/Button|Menu|Tabs|Pagination|Breadcrumb|Stepper/.test(name)) return 'fa-compass'
  if (/Avatar|Badge|Tag|Stat|Progress|Skeleton|Calendar|Code/.test(name)) return 'fa-shapes'
  return 'fa-cube'
}

function previewKind(name) {
  if (/Button/.test(name)) return 'button'
  if (/Input|Textarea|NumberInput|Form|FieldMessage/.test(name)) return 'input'
  if (/Select|Combobox|Dropdown|Popover/.test(name)) return 'select'
  if (/Checkbox|Radio|Switch|Slider|Upload/.test(name)) return 'control'
  if (/Table|DataTable/.test(name)) return 'table'
  if (/Modal|Drawer|CommandPalette|Popconfirm|Tooltip|Toast/.test(name)) return 'overlay'
  if (/Alert|Progress|Skeleton|Loading/.test(name)) return 'feedback'
  if (/Avatar|Badge|Tag|StatusPill|Stat|EmptyState|Image/.test(name)) return 'identity'
  if (/Calendar|DatePicker|TimePicker/.test(name)) return 'calendar'
  if (/Accordion|Tree|VirtualList|List/.test(name)) return 'list'
  if (/Code|Copy|Kbd/.test(name)) return 'code'
  if (/Stepper|Tabs|Menu|Breadcrumb|Pagination/.test(name)) return 'nav'
  if (/Panel|Card|Surface|Divider|Resizable|Logo/.test(name)) return 'layout'
  return 'generic'
}

function scrollToCatalogGroup(id) {
  activeGroup.value = id
  document.getElementById(`component-catalog-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function handleCatalogSearch() {
  const firstGroup = catalogSections.value[0]
  if (firstGroup) scrollToCatalogGroup(firstGroup.id)
}
</script>

<template>
  <ContentPanel title="组件预览">
    <div class="flex w-full flex-col gap-5 pb-2 pr-1 text-slate-900 dark:text-[#f7f8f8]">
      <section class="flex flex-col gap-4 border-b border-slate-200/70 pb-5 dark:border-white/[0.06] lg:flex-row lg:items-end lg:justify-between">
        <div class="min-w-0">
          <BaseBreadcrumb :items="breadcrumbItems" class="mb-3" />
          <h1 class="text-2xl font-bold tracking-normal text-slate-950 dark:text-[#f7f8f8]">组件预览</h1>
          <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-[#8a8f98]">
            集中查看当前 base 组件的常用状态，方便后续补齐组件库、统一交互和视觉规范。
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <BaseSearchInput v-model="catalogSearch" class="w-60 max-w-full" placeholder="搜索组件" />
          <BaseButton size="sm" variant="primary" @click="handleCatalogSearch">搜索</BaseButton>
        </div>
      </section>

      <section class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <BaseStat label="基础组件" :value="BASE_COMPONENT_COUNT" icon="fa-cubes" tone="accent" />
        <BaseStat label="组件分组" :value="componentGroups.length" icon="fa-table-cells-large" tone="blue" />
        <BaseStat label="API 条目" :value="apiDocs.length" icon="fa-book-open" tone="amber" />
        <BaseStat label="当前状态" value="可注册组件库" icon="fa-code-branch" tone="emerald" />
      </section>

      <section class="grid gap-6 xl:grid-cols-[15rem_minmax(0,1fr)]">
        <aside class="hidden xl:block">
          <div class="sticky top-0 grid gap-5">
            <BasePanel :scroll-body="false" body-class="p-3">
              <template #header>
                <BasePanelTitle icon="fa-list">组件目录</BasePanelTitle>
              </template>
              <div class="grid gap-1">
                <button
                  v-for="group in componentGroups"
                  :key="group.id"
                  type="button"
                  class="flex min-h-10 items-center justify-between gap-3 rounded-lg px-3 text-left text-sm font-semibold transition-colors"
                  :class="activeGroup === group.id
                    ? 'accent-bg-soft accent-text'
                    : 'text-slate-600 hover:bg-slate-100 dark:text-[#a8adb7] dark:hover:bg-white/[0.05]'"
                  @click="scrollToCatalogGroup(group.id)"
                >
                  <span class="truncate">{{ group.label }}</span>
                  <BaseTag size="xs" :tone="activeGroup === group.id ? 'accent' : 'neutral'">{{ group.count }}</BaseTag>
                </button>
              </div>
            </BasePanel>
          </div>
        </aside>

        <div class="grid min-w-0 gap-5">
          <BasePanel body-class="p-5" :scroll-body="false">
            <template #header>
              <div class="flex w-full items-center justify-between gap-3">
                <BasePanelTitle icon="fa-cubes">组件总览</BasePanelTitle>
                <BaseTag tone="accent">{{ BASE_COMPONENT_COUNT }} components</BaseTag>
              </div>
            </template>
            <div class="grid gap-8">
              <section
                v-for="group in catalogSections"
                :id="`component-catalog-${group.id}`"
                :key="group.id"
                class="scroll-mt-4"
              >
                <div class="mb-4 flex items-center gap-3">
                  <span class="flex h-9 w-9 items-center justify-center rounded-lg accent-bg-soft accent-text">
                    <i class="fa-solid text-sm" :class="groupMeta[group.id]?.icon || 'fa-cube'"></i>
                  </span>
                  <div class="min-w-0">
                    <h2 class="text-xl font-bold text-slate-950 dark:text-[#f7f8f8]">
                      {{ group.label }}
                      <BaseTag size="xs" tone="neutral" class="ml-2 align-middle">{{ group.components.length }}</BaseTag>
                    </h2>
                    <p class="mt-1 text-sm text-slate-500 dark:text-[#8a8f98]">{{ groupMeta[group.id]?.subtitle }}</p>
                  </div>
                </div>
                <div class="grid gap-4 sm:grid-cols-2 2xl:grid-cols-3">
                  <article
                    v-for="name in group.components"
                    :key="name"
                    class="group min-h-48 overflow-hidden rounded-xl border border-slate-200 bg-white/70 text-left transition-all hover:-translate-y-0.5 hover:border-[rgb(var(--accent-rgb)/0.35)] hover:bg-white hover:shadow-lg hover:shadow-slate-200/70 dark:border-white/[0.08] dark:bg-white/[0.025] dark:hover:bg-white/[0.05] dark:hover:shadow-black/20"
                  >
                    <div class="flex h-11 items-center justify-between border-b border-slate-200/70 px-4 dark:border-white/[0.06]">
                      <span class="truncate text-sm font-bold text-slate-900 dark:text-[#f7f8f8]">{{ componentLabel(name) }}</span>
                      <span class="text-xs font-semibold text-slate-400 transition-colors group-hover:accent-text">Base</span>
                    </div>
                    <div class="flex min-h-36 flex-col justify-between gap-3 px-4 py-4">
                      <div class="flex min-h-20 items-center">
                        <div v-if="previewKind(name) === 'button'" class="flex flex-wrap items-center gap-2">
                          <BaseButton size="sm" variant="primary">主要</BaseButton>
                          <BaseButton size="sm" variant="secondary">次要</BaseButton>
                          <BaseButton size="sm" variant="ghost">幽灵</BaseButton>
                        </div>

                        <div v-else-if="previewKind(name) === 'input'" class="grid w-full gap-2">
                          <BaseInput model-value="错题订正" placeholder="输入内容" />
                          <div class="grid grid-cols-[1fr_auto] gap-2">
                            <BaseTextarea model-value="说明文本" :rows="2" />
                            <BaseTag tone="rose">必填</BaseTag>
                          </div>
                        </div>

                        <div v-else-if="previewKind(name) === 'select'" class="grid w-full gap-2">
                          <BaseSegmented :model-value="segmented" :options="segmentedOptions" />
                          <div class="flex flex-wrap gap-2">
                            <BaseTag tone="accent">已选择</BaseTag>
                            <BaseTag tone="neutral">可搜索</BaseTag>
                            <BaseTag tone="blue">浮层</BaseTag>
                          </div>
                        </div>

                        <div v-else-if="previewKind(name) === 'control'" class="grid w-full gap-3">
                          <div class="flex flex-wrap items-center gap-4">
                            <BaseCheckbox :model-value="true" label="选中" />
                            <BaseSwitch :model-value="true" label="启用" />
                          </div>
                          <BaseSlider :model-value="62" :show-value="false" />
                        </div>

                        <div v-else-if="previewKind(name) === 'table'" class="w-full overflow-hidden rounded-lg border border-slate-200/80 dark:border-white/[0.08]">
                          <div class="grid grid-cols-[1.2fr_0.8fr_0.8fr] border-b border-slate-200/80 bg-slate-100/80 text-[11px] font-bold text-slate-500 dark:border-white/[0.08] dark:bg-white/[0.05] dark:text-[#8a8f98]">
                            <span class="px-2 py-1.5">组件</span>
                            <span class="px-2 py-1.5">状态</span>
                            <span class="px-2 py-1.5 text-right">覆盖</span>
                          </div>
                          <div class="grid grid-cols-[1.2fr_0.8fr_0.8fr] text-xs text-slate-600 dark:text-[#d0d6e0]">
                            <span class="px-2 py-1.5">Table</span>
                            <span class="px-2 py-1.5"><BaseStatusPill label="完成" tone="success" /></span>
                            <span class="px-2 py-1.5 text-right">90%</span>
                          </div>
                          <div class="grid grid-cols-[1.2fr_0.8fr_0.8fr] border-t border-slate-200/80 text-xs text-slate-500 dark:border-white/[0.08] dark:text-[#8a8f98]">
                            <span class="px-2 py-1.5">DataTable</span>
                            <span class="px-2 py-1.5"><BaseStatusPill label="排序" tone="info" /></span>
                            <span class="px-2 py-1.5 text-right">88%</span>
                          </div>
                        </div>

                        <div v-else-if="previewKind(name) === 'overlay'" class="relative h-24 w-full">
                          <div class="absolute left-3 top-2 h-16 w-28 rounded-xl border border-slate-200 bg-white shadow-lg shadow-slate-200/70 dark:border-white/[0.08] dark:bg-[#1f1f23] dark:shadow-black/30">
                            <div class="h-6 border-b border-slate-200/70 px-3 py-1 dark:border-white/[0.06]">
                              <div class="h-2 w-12 rounded bg-slate-300 dark:bg-white/[0.18]"></div>
                            </div>
                            <div class="space-y-1.5 p-3">
                              <div class="h-1.5 w-full rounded bg-slate-200 dark:bg-white/[0.12]"></div>
                              <div class="h-1.5 w-2/3 rounded bg-slate-200 dark:bg-white/[0.12]"></div>
                            </div>
                          </div>
                          <div class="absolute right-2 top-6 h-14 w-36 rounded-xl border border-[rgb(var(--accent-rgb)/0.25)] accent-bg-soft p-3 shadow-lg shadow-slate-200/60 dark:shadow-black/20">
                            <div class="mb-2 h-2 w-20 rounded accent-bg"></div>
                            <div class="h-1.5 w-full rounded bg-white/45"></div>
                          </div>
                        </div>

                        <div v-else-if="previewKind(name) === 'feedback'" class="grid w-full gap-3">
                          <BaseAlert tone="success" title="保存成功" />
                          <BaseProgress :value="68" size="sm" tone="accent" />
                          <div class="grid gap-1.5">
                            <BaseSkeleton class="h-2 w-full rounded" />
                            <BaseSkeleton class="h-2 w-2/3 rounded" />
                          </div>
                        </div>

                        <div v-else-if="previewKind(name) === 'identity'" class="flex w-full flex-wrap items-center gap-3">
                          <BaseAvatar name="Admin" tone="accent" />
                          <BaseBadge :value="12"><BaseAvatar icon="fa-bell" tone="blue" /></BaseBadge>
                          <BaseTag tone="emerald">Active</BaseTag>
                          <BaseStatusPill label="在线" tone="success" />
                        </div>

                        <div v-else-if="previewKind(name) === 'calendar'" class="grid w-full gap-3">
                          <div class="grid grid-cols-7 gap-1">
                            <span
                              v-for="day in 14"
                              :key="day"
                              class="flex h-6 items-center justify-center rounded-md text-[10px] font-semibold"
                              :class="day === 10 ? 'accent-bg text-white' : 'bg-slate-100 text-slate-500 dark:bg-white/[0.06] dark:text-[#8a8f98]'"
                            >
                              {{ day }}
                            </span>
                          </div>
                          <div class="flex gap-2">
                            <BaseTag tone="accent">2026-06-15</BaseTag>
                            <BaseTag tone="neutral">19:30</BaseTag>
                          </div>
                        </div>

                        <div v-else-if="previewKind(name) === 'list'" class="grid w-full gap-2">
                          <div class="rounded-lg border border-slate-200/80 dark:border-white/[0.08]">
                            <div class="flex items-center justify-between border-b border-slate-200/80 px-3 py-2 dark:border-white/[0.08]">
                              <span class="text-xs font-bold text-slate-700 dark:text-[#d0d6e0]">分组标题</span>
                              <i class="fa-solid fa-chevron-down text-[10px] text-slate-400"></i>
                            </div>
                            <div class="grid gap-1 px-3 py-2">
                              <div class="h-2 w-full rounded bg-slate-200 dark:bg-white/[0.1]"></div>
                              <div class="h-2 w-2/3 rounded bg-slate-200 dark:bg-white/[0.1]"></div>
                            </div>
                          </div>
                        </div>

                        <div v-else-if="previewKind(name) === 'code'" class="grid w-full gap-2">
                          <div class="rounded-lg border border-slate-200 bg-slate-950 p-3 font-mono text-[11px] text-emerald-200 dark:border-white/[0.08]">
                            <div>{ "copyable": true }</div>
                          </div>
                          <div class="flex flex-wrap items-center gap-2">
                            <BaseKbd>⌘</BaseKbd>
                            <BaseKbd>K</BaseKbd>
                            <BaseCopyButton text="BaseCopyButton" />
                          </div>
                        </div>

                        <div v-else-if="previewKind(name) === 'nav'" class="grid w-full gap-3">
                          <BaseStepper :model-value="stepValue" :steps="stepperSteps" />
                          <div class="flex flex-wrap gap-2">
                            <BaseTag tone="accent">概览</BaseTag>
                            <BaseTag tone="neutral">组件</BaseTag>
                            <BaseTag tone="neutral">Token</BaseTag>
                          </div>
                        </div>

                        <div v-else-if="previewKind(name) === 'layout'" class="grid w-full gap-3">
                          <div class="grid grid-cols-[0.65fr_1fr] gap-2 rounded-lg border border-slate-200/80 p-2 dark:border-white/[0.08]">
                            <div class="h-14 rounded-md accent-bg-soft"></div>
                            <div class="grid gap-2">
                              <div class="h-5 rounded-md bg-slate-100 dark:bg-white/[0.06]"></div>
                              <div class="h-7 rounded-md bg-slate-100 dark:bg-white/[0.06]"></div>
                            </div>
                          </div>
                          <BaseDivider label="分隔" />
                        </div>

                        <div v-else class="flex w-full items-center gap-4">
                          <span class="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-500 transition-colors group-hover:accent-bg-soft group-hover:accent-text dark:bg-white/[0.06] dark:text-[#8a8f98]">
                            <i class="fa-solid text-xl" :class="componentIcon(name)"></i>
                          </span>
                          <BaseTag tone="neutral">Preview</BaseTag>
                        </div>
                      </div>
                      <p class="line-clamp-2 text-xs leading-5 text-slate-500 dark:text-[#8a8f98]">{{ componentDescription(name) }}</p>
                    </div>
                  </article>
                </div>
              </section>
            </div>
          </BasePanel>

          <BaseDivider label="详细示例" />
          <BasePanel body-class="p-0" :scroll-body="false">
            <template #header>
              <div class="flex w-full items-center justify-between gap-3">
                <BasePanelTitle icon="fa-wand-magic-sparkles">操作与选择</BasePanelTitle>
                <BaseSegmented v-model="segmented" :options="segmentedOptions" />
              </div>
            </template>

            <div class="grid gap-5 p-5 lg:grid-cols-2">
              <BaseSurface class="p-4">
                <h2 class="text-sm font-bold text-slate-900 dark:text-[#f7f8f8]">按钮</h2>
                <div class="mt-4 flex flex-wrap gap-2">
                  <BaseButton variant="primary">Primary</BaseButton>
                  <BaseButton variant="secondary">Secondary</BaseButton>
                  <BaseButton variant="cta">CTA</BaseButton>
                  <BaseButton variant="ghost">Ghost</BaseButton>
                  <BaseButton disabled>Disabled</BaseButton>
                </div>
                <div class="mt-4 flex flex-wrap gap-2">
                  <BaseToolbarButton icon="fa-pen" title="编辑" />
                  <BaseToolbarButton icon="fa-trash-can" variant="danger" title="删除" />
                  <BaseTooltip text="用于弱操作或图标按钮说明" placement="bottom">
                    <BaseGhostButton>
                      <i class="fa-solid fa-circle-info"></i>
                    </BaseGhostButton>
                  </BaseTooltip>
                </div>
              </BaseSurface>

              <BaseSurface class="p-4">
                <h2 class="text-sm font-bold text-slate-900 dark:text-[#f7f8f8]">选择器</h2>
                <div class="mt-4 grid gap-3 sm:grid-cols-2">
                  <BaseSelect v-model="selectValue" :options="subjects" label="学科" placeholder="全部学科" />
                  <BaseSearchableSelect
                    v-model="searchableValue"
                    :options="tags"
                    placeholder="全部知识点"
                    search-placeholder="搜索知识点"
                    multiple
                  />
                </div>
                <div class="mt-4">
                  <BaseDropdown v-model="dropdownOpen" align="left">
                    <template #trigger>
                      <BaseButton variant="secondary" size="sm">打开下拉菜单</BaseButton>
                    </template>
                    <button class="block w-full px-3 py-2 text-left text-sm text-slate-600 hover:bg-slate-100 dark:text-[#d0d6e0] dark:hover:bg-white/[0.06]">重命名</button>
                    <button class="block w-full px-3 py-2 text-left text-sm text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-500/10">删除</button>
                  </BaseDropdown>
                </div>
              </BaseSurface>
            </div>
          </BasePanel>

          <BasePanel body-class="p-0" :scroll-body="false">
            <template #header>
              <BasePanelTitle icon="fa-keyboard">表单与状态</BasePanelTitle>
            </template>
            <div class="grid gap-5 p-5 lg:grid-cols-[minmax(0,1fr)_20rem]">
              <BaseCard padding="p-4">
                <div class="grid gap-4 sm:grid-cols-2">
                  <BaseInput v-model="inputValue" label="普通输入" placeholder="输入标题" />
                  <BaseInput v-model="password" label="密码输入" type="password" />
                  <BaseInput label="错误状态" placeholder="需要填写内容" error />
                  <div class="flex items-end">
                    <BaseSwitch v-model="switchOn" label="自动保存" />
                  </div>
                </div>
              </BaseCard>

              <BaseListGroup title="设置列表" description="BaseListGroup + BaseListItem 的组合示例。">
                <BaseListItem label="显示密度" description="影响列表与表格的行高" value="紧凑" />
                <BaseListItem label="自动保存" description="离开页面前保存草稿">
                  <BaseSwitch v-model="switchOn" />
                </BaseListItem>
                <BaseListItem label="危险操作" description="二次确认弹层" danger>
                  <BasePopconfirm title="清空预览？" description="仅会清空当前页面 Toast 示例。" confirm-text="清空" danger @confirm="toasts = []">
                    <BaseButton variant="ghost" size="sm">清空</BaseButton>
                  </BasePopconfirm>
                </BaseListItem>
              </BaseListGroup>
            </div>
          </BasePanel>

          <BasePanel body-class="p-0" :scroll-body="false">
            <template #header>
              <BasePanelTitle icon="fa-rectangle-list">新增基础表单组件</BasePanelTitle>
            </template>
            <div class="grid gap-5 p-5 xl:grid-cols-[minmax(0,1fr)_22rem]">
              <BaseForm class="min-w-0" @submit="pushDemoToast('success')">
                <div class="grid gap-4 md:grid-cols-2">
                  <BaseFormItem label="NumberInput" hint="支持 min/max/step 和左右步进按钮。">
                    <BaseNumberInput v-model="numberValue" :min="0" :max="100" :step="5" placeholder="输入分数" />
                  </BaseFormItem>
                  <BaseFormItem label="DatePicker / TimePicker" hint="轻量封装原生日期时间控件。">
                    <div class="grid gap-3 sm:grid-cols-2">
                      <BaseDatePicker v-model="dateValue" />
                      <BaseTimePicker v-model="timeValue" />
                    </div>
                  </BaseFormItem>
                  <BaseFormItem label="Textarea" hint="支持字数统计、错误和禁用状态。">
                    <BaseTextarea v-model="textareaValue" :maxlength="120" resize="none" />
                  </BaseFormItem>
                  <BaseFormItem label="RadioGroup" error="">
                    <BaseRadioGroup v-model="radioValue" :options="radioOptions" name="preview-density" />
                  </BaseFormItem>
                </div>

                <div class="flex flex-wrap items-center gap-4 rounded-xl border border-gray-100 bg-gray-50/80 p-4 dark:border-white/[0.08] dark:bg-white/[0.035]">
                  <BaseCheckbox v-model="checkboxValue" value="wrongbook" label="加入错题库" description="数组模式，适合多选项。" />
                  <BaseCheckbox v-model="switchOn" label="布尔选中" description="布尔模式，适合单个开关。" />
                  <BaseCheckbox label="中间态" indeterminate description="可用于父级半选状态。" />
                </div>

                <div class="flex justify-end">
                  <BaseButton size="sm" type="submit">提交预览表单</BaseButton>
                </div>
              </BaseForm>

              <BaseUpload
                v-model="uploadFiles"
                label="BaseUpload"
                accept=".pdf,.png,.jpg,.jpeg"
                description="拖拽或选择文件；当前只是通用 UI，不绑定业务上传流程。"
                :max-size="10 * 1024 * 1024"
                @reject="pushDemoToast('error')"
              />
            </div>
          </BasePanel>

          <section class="grid gap-5 lg:grid-cols-2">
            <BasePanel body-class="p-0" :scroll-body="false">
              <template #header>
                <BasePanelTitle icon="fa-window-restore">反馈组件</BasePanelTitle>
              </template>
              <BaseTabs v-model="tab" :items="tabItems" />
              <div class="space-y-4 p-5">
                <div class="flex flex-wrap gap-2">
                  <BaseButton size="sm" @click="modalOpen = true">打开 Modal</BaseButton>
                  <BaseButton size="sm" variant="secondary" @click="drawerOpen = true">打开 Drawer</BaseButton>
                  <BaseButton size="sm" variant="secondary" @click="pushDemoToast('success')">成功通知</BaseButton>
                  <BaseButton size="sm" variant="ghost" @click="pushDemoToast('error')">错误通知</BaseButton>
                </div>
                <BaseAlert
                  v-if="alertVisible"
                  tone="success"
                  title="BaseAlert 已接入"
                  description="支持 info、success、warning、danger 四种状态，也支持关闭按钮。"
                  closable
                  @close="alertVisible = false"
                />
                <BaseAlert
                  v-else
                  tone="info"
                  title="Alert 已关闭"
                  description="点击右侧按钮可以重新显示成功提示。"
                >
                  <BaseButton size="sm" variant="ghost" @click="alertVisible = true">重新显示</BaseButton>
                </BaseAlert>
                <div class="flex flex-wrap gap-2">
                  <BaseStatusPill
                    v-for="row in statusRows"
                    :key="row.label"
                    :label="row.label"
                    :ok="row.ok"
                    :loading="row.loading"
                    :placeholder="row.placeholder"
                  />
                </div>
                <BasePagination v-model:page="page" :total-pages="12" />
              </div>
            </BasePanel>

            <BasePanel :scroll-body="false" body-class="p-5">
              <template #header>
                <BasePanelTitle icon="fa-shapes">展示组件</BasePanelTitle>
              </template>
              <div class="space-y-4">
                <div class="flex flex-wrap gap-2">
                  <BaseTag>Neutral</BaseTag>
                  <BaseTag tone="accent">Accent</BaseTag>
                  <BaseTag tone="emerald">Done</BaseTag>
                  <BaseTag tone="amber">Pending</BaseTag>
                  <BaseTag tone="rose">Risk</BaseTag>
                  <BaseTag tone="blue">Info</BaseTag>
                  <BaseBadge :value="8">
                    <BaseButton size="sm" variant="secondary">Badge</BaseButton>
                  </BaseBadge>
                  <BaseBadge dot tone="emerald">
                    <BaseButton size="sm" variant="ghost">Dot</BaseButton>
                  </BaseBadge>
                </div>
                <div class="grid gap-3">
                  <BaseProgress label="学习进度" :value="68" show-value />
                  <BaseProgress label="掌握率" :value="42" tone="emerald" size="sm" show-value />
                  <BaseProgress label="风险项" :value="18" tone="rose" size="lg" show-value />
                </div>
                <div class="grid gap-3 rounded-xl border border-slate-200 bg-white/60 p-4 dark:border-white/[0.06] dark:bg-white/[0.025]">
                  <div class="flex items-center gap-3">
                    <BaseSkeleton variant="circle" />
                    <div class="min-w-0 flex-1">
                      <BaseSkeleton variant="text" :lines="2" />
                    </div>
                  </div>
                  <BaseSkeleton />
                </div>
                <BaseEmptyState
                  icon="fa-regular fa-folder-open"
                  title="暂无组件文档"
                  description="后续可以把 props、事件、插槽说明补到这个预览页。"
                />
              </div>
            </BasePanel>
          </section>

          <BasePanel body-class="p-5" :scroll-body="false">
            <template #header>
              <BasePanelTitle icon="fa-fingerprint">品牌与媒体</BasePanelTitle>
            </template>
            <div class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
              <BaseSurface class="p-4">
                <h2 class="text-sm font-bold text-slate-900 dark:text-[#f7f8f8]">Logo</h2>
                <div class="mt-4 flex items-center gap-4">
                  <BaseLogo size="sm" />
                  <BaseLogo />
                  <BaseLogo size="lg" breathe />
                </div>
              </BaseSurface>

              <BaseSurface class="p-4">
                <h2 class="text-sm font-bold text-slate-900 dark:text-[#f7f8f8]">全局与图片预览</h2>
                <div class="mt-4 flex flex-wrap gap-2">
                  <BaseButton size="sm" variant="secondary" @click="showLoadingPreview">预览 Loading</BaseButton>
                  <BaseButton size="sm" @click="imageModalOpen = true">预览 ImageModal</BaseButton>
                </div>
                <div class="mt-4 flex items-center gap-3 rounded-lg border border-slate-200 bg-white/70 p-3 dark:border-white/[0.06] dark:bg-white/[0.03]">
                  <img src="/logo.svg" alt="logo preview" class="h-10 w-10 rounded-lg bg-slate-900 p-2" />
                  <div class="min-w-0">
                    <p class="text-sm font-semibold text-slate-900 dark:text-[#f7f8f8]">ImageModal</p>
                    <p class="text-xs text-slate-500 dark:text-[#8a8f98]">点击按钮打开，可滚轮缩放。</p>
                  </div>
                </div>
              </BaseSurface>
            </div>
          </BasePanel>

          <BasePanel body-class="p-5" :scroll-body="false">
            <template #header>
              <div class="flex w-full items-center justify-between gap-3">
                <BasePanelTitle icon="fa-table">数据与导航组件</BasePanelTitle>
                <BaseButton size="sm" variant="secondary" @click="commandPaletteOpen = true">打开命令面板</BaseButton>
              </div>
            </template>
            <div class="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(20rem,0.8fr)]">
              <div class="grid gap-5">
                <BaseDataTable
                  :columns="tableColumns"
                  :rows="tableRows"
                  :page-size="4"
                  @row-click="row => pushDemoToast('info')"
                >
                  <template #cell-status="{ value }">
                    <BaseTag :tone="value === '已完成' ? 'emerald' : 'amber'">{{ value }}</BaseTag>
                  </template>
                  <template #cell-coverage="{ value }">
                    <span class="font-semibold">{{ value }}%</span>
                  </template>
                </BaseDataTable>

                <BaseTable :columns="tableColumns.slice(0, 3)" :rows="tableRows.slice(0, 3)" compact>
                  <template #cell-status="{ value }">
                    <BaseStatusPill :label="value" ok />
                  </template>
                </BaseTable>
              </div>

              <div class="grid content-start gap-5">
                <BaseSurface class="p-4">
                  <h2 class="text-sm font-bold text-slate-900 dark:text-[#f7f8f8]">Avatar / Popover</h2>
                  <div class="mt-4 flex items-center gap-3">
                    <BaseAvatar name="小哲" size="lg" />
                    <BaseAvatar name="Math Tutor" tone="blue" />
                    <BaseAvatar icon="fa-user-graduate" tone="emerald" />
                    <BasePopover v-model="popoverOpen" align="right">
                      <template #trigger>
                        <BaseButton size="sm" variant="secondary">筛选说明</BaseButton>
                      </template>
                      <div class="space-y-3">
                        <div>
                          <p class="text-sm font-bold text-slate-900 dark:text-[#f7f8f8]">BasePopover</p>
                          <p class="mt-1 text-sm leading-5 text-slate-500 dark:text-[#8a8f98]">
                            可放说明、轻量表单或筛选条件，比 Dropdown 更自由。
                          </p>
                        </div>
                        <BaseCheckbox v-model="switchOn" label="只看已完成组件" />
                      </div>
                    </BasePopover>
                  </div>
                </BaseSurface>

                <BaseAccordion v-model="accordionValue" :items="accordionItems" />
              </div>
            </div>
          </BasePanel>

          <BasePanel body-class="p-5" :scroll-body="false">
            <template #header>
              <BasePanelTitle icon="fa-compass">导航与辅助组件</BasePanelTitle>
            </template>
            <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_22rem]">
              <div class="grid gap-5">
                <BaseSurface class="p-4">
                  <h2 class="text-sm font-bold text-slate-900 dark:text-[#f7f8f8]">Stepper / Slider</h2>
                  <div class="mt-4 grid gap-5">
                    <BaseStepper v-model="stepValue" :steps="stepperSteps" />
                    <BaseSlider v-model="sliderValue" label="识别置信阈值" :min="0" :max="100" />
                  </div>
                </BaseSurface>

                <BaseSurface class="p-4">
                  <div class="flex flex-wrap items-center gap-2">
                    <BaseBreadcrumbItem label="工作台" icon="fa-house" @click="pushDemoToast('info')" />
                    <i class="fa-solid fa-chevron-right text-[9px] text-slate-400"></i>
                    <BaseBreadcrumbItem label="组件库" current />
                  </div>
                  <BaseDivider class="my-4" label="快捷能力" />
                  <div class="flex flex-wrap items-center gap-3">
                    <span class="text-sm text-slate-600 dark:text-[#a8adb7]">打开命令面板</span>
                    <BaseKbd :keys="['Ctrl', 'K']" />
                    <BaseCopyButton text="http://localhost:5188/app/component-preview" @copy="pushDemoToast('success')" />
                  </div>
                </BaseSurface>

                <BaseCodeBlock
                  title="配置片段"
                  language="json"
                  :code="codeSample"
                  @copy="pushDemoToast('success')"
                />
              </div>

              <BaseMenu v-model="menuValue" :items="menuItems" @select="pushDemoToast('info')" />
            </div>
          </BasePanel>

          <BasePanel body-class="p-5" :scroll-body="false">
            <template #header>
              <BasePanelTitle icon="fa-cubes-stacked">复杂组件</BasePanelTitle>
            </template>
            <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_24rem]">
              <div class="grid gap-5">
                <BaseResizablePanels v-model="panelSize">
                  <template #left>
                    <div class="space-y-3">
                      <h2 class="text-sm font-bold text-slate-900 dark:text-[#f7f8f8]">ResizablePanels</h2>
                      <p class="text-sm leading-6 text-slate-500 dark:text-[#8a8f98]">
                        拖动中间分割条调整左右区域比例，适合编辑器、详情页和对比视图。
                      </p>
                      <BaseProgress label="左侧宽度" :value="panelSize" show-value />
                    </div>
                  </template>
                  <template #right>
                    <BaseCodeBlock
                      title="右侧面板"
                      language="vue"
                      code="<BaseResizablePanels v-model=&quot;size&quot; />"
                    />
                  </template>
                </BaseResizablePanels>

                <BaseSurface class="p-4">
                  <div class="grid gap-4 lg:grid-cols-2">
                    <div>
                      <h2 class="mb-3 text-sm font-bold text-slate-900 dark:text-[#f7f8f8]">VirtualList</h2>
                      <BaseVirtualList :items="virtualItems" :height="260" :item-height="48">
                        <template #default="{ item }">
                          <div class="flex h-full items-center gap-3 border-b border-slate-100 px-4 dark:border-white/[0.05]">
                            <BaseAvatar :name="String(item.id)" size="sm" tone="neutral" />
                            <div class="min-w-0">
                              <p class="truncate text-sm font-semibold text-slate-800 dark:text-[#f7f8f8]">{{ item.label }}</p>
                              <p class="truncate text-xs text-slate-500 dark:text-[#8a8f98]">{{ item.description }}</p>
                            </div>
                          </div>
                        </template>
                      </BaseVirtualList>
                    </div>

                    <div>
                      <h2 class="mb-3 text-sm font-bold text-slate-900 dark:text-[#f7f8f8]">Tree / TooltipProvider</h2>
                      <BaseTooltipProvider :offset="10">
                        <BaseTooltip text="Provider 统一控制 offset、z-index 和禁用状态">
                          <BaseButton class="mb-3" size="sm" variant="secondary">悬停查看 Tooltip</BaseButton>
                        </BaseTooltip>
                      </BaseTooltipProvider>
                      <BaseTree
                        v-model="treeValue"
                        :items="treeItems"
                        :default-expanded="['base', 'features']"
                        @select="pushDemoToast('info')"
                      />
                    </div>
                  </div>
                </BaseSurface>
              </div>

              <div class="grid content-start gap-5">
                <BaseSurface class="p-4">
                  <h2 class="mb-3 text-sm font-bold text-slate-900 dark:text-[#f7f8f8]">Calendar</h2>
                  <BaseCalendar v-model="calendarValue" />
                  <p class="mt-3 text-xs text-slate-500 dark:text-[#8a8f98]">当前选择：{{ calendarValue }}</p>
                </BaseSurface>

                <BaseSurface class="p-4">
                  <h2 class="mb-3 text-sm font-bold text-slate-900 dark:text-[#f7f8f8]">Combobox</h2>
                  <BaseCombobox
                    v-model="comboboxValue"
                    :options="comboboxOptions"
                    placeholder="选择知识点"
                    search-placeholder="搜索知识点"
                  />
                </BaseSurface>
              </div>
            </div>
          </BasePanel>

          <BasePanel body-class="p-5" :scroll-body="false">
            <template #header>
              <div class="flex w-full items-center justify-between gap-3">
                <BasePanelTitle icon="fa-book-open">API 文档</BasePanelTitle>
                <BaseTag tone="accent">入口：components/base/index.js</BaseTag>
              </div>
            </template>
            <div class="grid gap-4">
              <BaseAlert
                tone="info"
                title="组件库入口已建立"
                description="业务代码可以从 @/components/base 按需导入组件；这里先记录核心 props、事件和插槽。"
              />
              <BaseDataTable
                :columns="apiDocColumns"
                :rows="apiDocs"
                :page-size="6"
                :searchable="false"
              >
                <template #cell-component="{ value }">
                  <span class="font-bold text-slate-900 dark:text-[#f7f8f8]">{{ value }}</span>
                </template>
                <template #cell-props="{ value }">
                  <code class="text-xs text-slate-600 dark:text-[#a8adb7]">{{ value }}</code>
                </template>
                <template #cell-emits="{ value }">
                  <code class="text-xs text-slate-600 dark:text-[#a8adb7]">{{ value }}</code>
                </template>
                <template #cell-slots="{ value }">
                  <code class="text-xs text-slate-600 dark:text-[#a8adb7]">{{ value }}</code>
                </template>
              </BaseDataTable>
            </div>
          </BasePanel>

          <BasePanel body-class="p-5" :scroll-body="false">
            <template #header>
              <BasePanelTitle icon="fa-screwdriver-wrench">待补齐组件</BasePanelTitle>
            </template>
            <BaseAlert
              v-if="!plannedComponents.length"
              tone="success"
              title="当前规划组件已补齐"
              description="高优先级、中优先级和复杂组件批次都已加入预览页。"
            />
            <div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              <div
                v-for="name in plannedComponents"
                :key="name"
                class="flex min-h-12 items-center justify-between gap-3 rounded-lg border border-dashed border-slate-200 bg-white/55 px-3 py-2 dark:border-white/[0.08] dark:bg-white/[0.025]"
              >
                <span class="min-w-0 truncate text-sm font-semibold text-slate-700 dark:text-[#d0d6e0]">{{ name }}</span>
                <BaseTag size="xs" tone="amber">待建</BaseTag>
              </div>
            </div>
          </BasePanel>

          <BasePanel body-class="p-5" :scroll-body="false">
            <template #header>
              <BasePanelTitle icon="fa-briefcase">业务组件索引</BasePanelTitle>
            </template>
            <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <BaseCard
                v-for="item in businessComponents"
                :key="item.name"
                padding="p-4"
              >
                <div class="flex h-full flex-col gap-2">
                  <div class="flex items-center justify-between gap-2">
                    <p class="truncate text-sm font-bold text-slate-900 dark:text-[#f7f8f8]">{{ item.name }}</p>
                    <BaseTag size="xs" tone="blue">业务</BaseTag>
                  </div>
                  <p class="text-xs leading-5 text-slate-500 dark:text-[#8a8f98]">{{ item.desc }}</p>
                </div>
              </BaseCard>
            </div>
          </BasePanel>
        </div>
      </section>
    </div>

    <BaseToastContainer :toasts="toasts" @dismiss="dismissToast" />
    <BaseLoading :visible="loadingPreview" />
    <ImageModal
      :open="imageModalOpen"
      src="/logo.svg"
      :scale="imageScale"
      @close="imageModalOpen = false"
      @update:scale="(value) => imageScale = value"
    />
    <BaseDrawer
      :open="drawerOpen"
      title="BaseDrawer"
      description="适合详情、表单、筛选条件等侧边浮层。"
      @close="drawerOpen = false"
    >
      <div class="space-y-4">
        <BaseAlert tone="info" title="抽屉内容" description="这里可以放任意表单、列表或操作区。" />
        <BaseForm @submit="pushDemoToast('success'); drawerOpen = false">
          <BaseFormItem label="标题">
            <BaseInput v-model="inputValue" placeholder="输入标题" />
          </BaseFormItem>
          <BaseFormItem label="说明">
            <BaseTextarea v-model="textareaValue" resize="none" />
          </BaseFormItem>
          <div class="flex justify-end gap-2">
            <BaseButton type="button" variant="secondary" size="sm" @click="drawerOpen = false">取消</BaseButton>
            <BaseButton type="submit" size="sm">保存</BaseButton>
          </div>
        </BaseForm>
      </div>
    </BaseDrawer>
    <BaseCommandPalette
      v-model:open="commandPaletteOpen"
      :items="commandItems"
      placeholder="搜索页面、动作或组件"
      @select="item => pushDemoToast('info')"
    />

    <BaseModal
      :open="modalOpen"
      title="组件弹窗"
      icon="fa-cube"
      icon-bg="accent-bg-soft"
      icon-class="accent-text"
      max-width="max-w-lg"
      @close="modalOpen = false"
    >
      <p class="text-sm leading-6 text-slate-600 dark:text-[#a8adb7]">
        这是 BaseModal 的预览状态。后续可以继续补充表单、滚动内容、危险确认、全屏抽屉等变体。
      </p>
      <template #footer>
        <BaseButton variant="secondary" size="sm" @click="modalOpen = false">取消</BaseButton>
        <BaseButton size="sm" @click="modalOpen = false">确认</BaseButton>
      </template>
    </BaseModal>
  </ContentPanel>
</template>
