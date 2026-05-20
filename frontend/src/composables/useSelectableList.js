import { reactive, ref } from 'vue'

/**
 * useSelectableList — 列表多选模式 composable
 * @param {Object} options
 * @param {string} options.idKey - 项目 ID 字段名，默认 'id'
 * @returns {{ selectMode, selectedIds, toggleSelectMode, toggleSelect, selectAllItems, clearSelection }}
 */
export function useSelectableList({ idKey = 'id' } = {}) {
  const selectMode = ref(false)
  const selectedIds = reactive(new Set())

  /**
   * 切换多选模式；退出多选时清空已选项。
   */
  const toggleSelectMode = () => {
    selectMode.value = !selectMode.value
    if (!selectMode.value) selectedIds.clear()
  }

  /**
   * 切换单个项目的选中状态。
   */
  const toggleSelect = (id) => {
    selectedIds.has(id) ? selectedIds.delete(id) : selectedIds.add(id)
  }

  /**
   * 将传入列表里的项目全部加入选中集合。
   */
  const selectAllItems = (items) => {
    items.forEach((item) => selectedIds.add(item[idKey]))
  }

  /**
   * 清空当前所有选中项。
   */
  const clearSelection = () => {
    selectedIds.clear()
  }

  return {
    selectMode,
    selectedIds,
    toggleSelectMode,
    toggleSelect,
    selectAllItems,
    clearSelection,
  }
}
