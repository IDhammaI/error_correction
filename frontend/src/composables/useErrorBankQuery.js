import { computed, reactive, ref } from 'vue'
import * as api from '@/api/index.js'

/**
 * useErrorBankQuery
 * 管理错题库列表查询、筛选项、分页和当前选中题目。
 */
export function useErrorBankQuery({ activeQuestionProjectId, pushToast, typesetMath }) {
  const filters = reactive({
    subject: [],
    knowledge_tag: [],
    question_type: [],
    keyword: '',
    review_status: '',
  })
  const page = ref(1)
  const pageSize = ref(10)
  const items = ref([])
  const total = ref(0)
  const grandTotal = ref(0)
  const totalPages = ref(0)
  const loading = ref(false)
  const subjects = ref([])
  const questionTypes = ref([])
  const tagNames = ref([])
  const selectedTags = reactive(new Set())
  const activeQuestionId = ref(null)
  let debounceTimer = null

  const activeQuestion = computed(() =>
    items.value.find(q => String(q.id) === String(activeQuestionId.value)) || items.value[0] || null
  )
  const contentBlocks = computed(() => activeQuestion.value?.content_json || [])
  const optionList = computed(() => activeQuestion.value?.options_json || [])
  const knowledgeTags = computed(() => activeQuestion.value?.knowledge_tags || [])

  const reviewStatusOptions = ['待复习', '复习中', '已掌握']

  /**
   * 按当前筛选条件查询错题列表。
   */
  const doQuery = async () => {
    if (!activeQuestionProjectId.value) {
      items.value = []
      total.value = 0
      grandTotal.value = 0
      totalPages.value = 0
      loading.value = false
      activeQuestionId.value = null
      return
    }
    loading.value = true
    try {
      const params = { page: page.value, page_size: pageSize.value, project_id: activeQuestionProjectId.value }
      if (filters.subject?.length) params.subject = filters.subject
      if (filters.knowledge_tag?.length) params.knowledge_tag = filters.knowledge_tag
      if (filters.question_type?.length) params.question_type = filters.question_type
      if (filters.keyword) params.keyword = filters.keyword
      if (filters.review_status) params.review_status = filters.review_status

      const data = await api.fetchErrorBank(params)
      items.value = data.items || []
      total.value = data.total || 0
      grandTotal.value = data.grand_total ?? data.total ?? 0
      totalPages.value = data.total_pages || 0

      if (!items.value.some(q => String(q.id) === String(activeQuestionId.value))) {
        activeQuestionId.value = items.value[0]?.id || null
      }
    } catch (error) {
      pushToast('error', error instanceof Error ? error.message : String(error))
    } finally {
      loading.value = false
      await typesetMath()
    }
  }

  /**
   * 根据当前学科刷新知识点标签。
   */
  const refreshTags = async () => {
    if (!activeQuestionProjectId.value) {
      tagNames.value = []
      return
    }
    const raw = await api.fetchTagNames(filters.subject?.length === 1 ? filters.subject[0] : undefined, activeQuestionProjectId.value)
    tagNames.value = [...new Set(raw)]
  }

  /**
   * 加载学科、题型、知识点筛选项。
   */
  const loadFilters = async () => {
    if (!activeQuestionProjectId.value) {
      subjects.value = []
      questionTypes.value = []
      tagNames.value = []
      return
    }
    try {
      const [subjectRows, typeRows] = await Promise.all([
        api.fetchSubjects(activeQuestionProjectId.value),
        api.fetchQuestionTypes(activeQuestionProjectId.value),
      ])
      subjects.value = subjectRows
      questionTypes.value = typeRows
      await refreshTags()
    } catch (_) {
      pushToast('error', '加载筛选项失败')
    }
  }

  /**
   * 防抖触发查询，避免输入或多筛选项变化时频繁请求。
   */
  const debouncedQuery = (delay = 300) => {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(async () => {
      page.value = 1
      await doQuery()
    }, delay)
  }

  /**
   * 重置筛选条件，并回到第一页。
   */
  const resetFilters = () => {
    filters.subject = []
    filters.knowledge_tag = []
    filters.question_type = []
    filters.keyword = ''
    filters.review_status = ''
    selectedTags.clear()
    page.value = 1
    doQuery()
  }

  /**
   * 跳转分页，越界或重复页码不请求。
   */
  const goPage = (nextPage) => {
    if (nextPage < 1 || nextPage > totalPages.value || nextPage === page.value) return
    page.value = nextPage
    doQuery()
  }

  /**
   * 销毁组件前清理防抖定时器。
   */
  const dispose = () => {
    if (debounceTimer) clearTimeout(debounceTimer)
  }

  return {
    filters,
    page,
    pageSize,
    items,
    total,
    grandTotal,
    totalPages,
    loading,
    subjects,
    questionTypes,
    tagNames,
    selectedTags,
    activeQuestionId,
    activeQuestion,
    contentBlocks,
    optionList,
    knowledgeTags,
    reviewStatusOptions,
    doQuery,
    loadFilters,
    refreshTags,
    debouncedQuery,
    resetFilters,
    goPage,
    dispose,
  }
}
