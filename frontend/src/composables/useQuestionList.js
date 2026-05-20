import { ref, reactive, nextTick } from 'vue'
import { typesetMath as _typesetMathEl } from '@/utils/index.js'

/**
 * useQuestionList.js
 * 维护分割结果里的题目列表、选中集合、拖拽排序和公式渲染。
 */
export function useQuestionList() {
  const questions = ref([])
  const selectedIds = reactive(new Set())
  const questionListRef = ref(null)

  /**
   * 切换单道题目的选中状态。
   */
  const toggleQuestion = (id) => { selectedIds.has(id) ? selectedIds.delete(id) : selectedIds.add(id) }

  /**
   * 选中当前列表里的所有题目。
   */
  const selectAll = () => { for (const q of questions.value) selectedIds.add(q.uid) }

  /**
   * 清空当前题目选择。
   */
  const deselectAll = () => { selectedIds.clear() }

  /**
   * 根据拖拽前后的索引重新排列题目。
   */
  const reorderQuestions = (oldIndex, newIndex) => {
    const arr = questions.value.slice()
    const [moved] = arr.splice(oldIndex, 1)
    arr.splice(newIndex, 0, moved)
    questions.value = arr
  }

  /**
   * 等待列表 DOM 更新后，对题目区域重新执行 MathJax 排版。
   */
  const typesetMath = async () => {
    await nextTick()
    const el = questionListRef.value?.questionsBoxEl
    await _typesetMathEl(el || undefined)
  }

  return {
    questions, selectedIds, questionListRef,
    toggleQuestion, selectAll, deselectAll, reorderQuestions, typesetMath,
  }
}
