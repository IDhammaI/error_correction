export { default as BaseAccordion } from './BaseAccordion.vue'
export { default as BaseAlert } from './BaseAlert.vue'
export { default as BaseAvatar } from './BaseAvatar.vue'
export { default as BaseBadge } from './BaseBadge.vue'
export { default as BaseBreadcrumb } from './BaseBreadcrumb.vue'
export { default as BaseBreadcrumbItem } from './BaseBreadcrumbItem.vue'
export { default as BaseButton } from './BaseButton.vue'
export { default as BaseCalendar } from './BaseCalendar.vue'
export { default as BaseCard } from './BaseCard.vue'
export { default as BaseCheckbox } from './BaseCheckbox.vue'
export { default as BaseCodeBlock } from './BaseCodeBlock.vue'
export { default as BaseCombobox } from './BaseCombobox.vue'
export { default as BaseCommandPalette } from './BaseCommandPalette.vue'
export { default as BaseCopyButton } from './BaseCopyButton.vue'
export { default as BaseDataTable } from './BaseDataTable.vue'
export { default as BaseDatePicker } from './BaseDatePicker.vue'
export { default as BaseDivider } from './BaseDivider.vue'
export { default as BaseDrawer } from './BaseDrawer.vue'
export { default as BaseDropdown } from './BaseDropdown.vue'
export { default as BaseEmptyState } from './BaseEmptyState.vue'
export { default as BaseFieldMessage } from './BaseFieldMessage.vue'
export { default as BaseForm } from './BaseForm.vue'
export { default as BaseFormItem } from './BaseFormItem.vue'
export { default as BaseGhostButton } from './BaseGhostButton.vue'
export { default as BaseInput } from './BaseInput.vue'
export { default as BaseKbd } from './BaseKbd.vue'
export { default as BaseListGroup } from './BaseListGroup.vue'
export { default as BaseListItem } from './BaseListItem.vue'
export { default as BaseLoading } from './BaseLoading.vue'
export { default as BaseLogo } from './BaseLogo.vue'
export { default as BaseMenu } from './BaseMenu.vue'
export { default as BaseModal } from './BaseModal.vue'
export { default as BaseNumberInput } from './BaseNumberInput.vue'
export { default as BasePagination } from './BasePagination.vue'
export { default as BasePanel } from './BasePanel.vue'
export { default as BasePanelTitle } from './BasePanelTitle.vue'
export { default as BasePopconfirm } from './BasePopconfirm.vue'
export { default as BasePopover } from './BasePopover.vue'
export { default as BaseProgress } from './BaseProgress.vue'
export { default as BaseRadio } from './BaseRadio.vue'
export { default as BaseRadioGroup } from './BaseRadioGroup.vue'
export { default as BaseResizablePanels } from './BaseResizablePanels.vue'
export { default as BaseSearchableSelect } from './BaseSearchableSelect.vue'
export { default as BaseSearchInput } from './BaseSearchInput.vue'
export { default as BaseSegmented } from './BaseSegmented.vue'
export { default as BaseSelect } from './BaseSelect.vue'
export { default as BaseSkeleton } from './BaseSkeleton.vue'
export { default as BaseSlider } from './BaseSlider.vue'
export { default as BaseStat } from './BaseStat.vue'
export { default as BaseStatusPill } from './BaseStatusPill.vue'
export { default as BaseStepper } from './BaseStepper.vue'
export { default as BaseSurface } from './BaseSurface.vue'
export { default as BaseSwitch } from './BaseSwitch.vue'
export { default as BaseTable } from './BaseTable.vue'
export { default as BaseTabs } from './BaseTabs.vue'
export { default as BaseTag } from './BaseTag.vue'
export { default as BaseTextarea } from './BaseTextarea.vue'
export { default as BaseTimePicker } from './BaseTimePicker.vue'
export { default as BaseToastContainer } from './BaseToastContainer.vue'
export { default as BaseToolbarButton } from './BaseToolbarButton.vue'
export { default as BaseTooltip } from './BaseTooltip.vue'
export { default as BaseTooltipProvider } from './BaseTooltipProvider.vue'
export { default as BaseTree } from './BaseTree.vue'
export { default as BaseUpload } from './BaseUpload.vue'
export { default as BaseVirtualList } from './BaseVirtualList.vue'
export { default as ImageModal } from './ImageModal.vue'
export {
  BASE_COMPONENT_API_DOCS,
  BASE_COMPONENT_COUNT,
  BASE_COMPONENT_GROUPS,
  BASE_COMPONENT_GROUP_SUMMARY,
} from './registry.js'

const componentModules = import.meta.glob('./*.vue', { eager: true })

export const baseComponents = Object.fromEntries(
  Object.entries(componentModules).map(([path, module]) => {
    const name = path.split('/').pop().replace(/\.vue$/, '')
    return [name, module.default]
  }),
)

export function install(app) {
  Object.entries(baseComponents).forEach(([name, component]) => {
    app.component(name, component)
  })
}

export default { install }
