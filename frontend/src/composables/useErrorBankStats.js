import { computed, ref } from 'vue'
import * as api from '@/api/index.js'

/**
 * useErrorBankStats
 * 管理错题库统计数据和顶部统计卡片展示数据。
 */
export function useErrorBankStats({ activeQuestionProjectId, grandTotal, total }) {
  const stats = ref(null)

  const reviewStats = computed(() => stats.value?.review_stats || {})
  const totalQuestions = computed(() => Number(stats.value?.total_questions ?? grandTotal.value ?? 0))
  const masteredCount = computed(() => Number(reviewStats.value['已掌握'] || 0))
  const pendingCount = computed(() => Number(reviewStats.value['待复习'] || 0))
  const reviewingCount = computed(() => Number(reviewStats.value['复习中'] || 0))
  const masteryRate = computed(() => {
    if (!totalQuestions.value) return 0
    return Math.round((masteredCount.value / totalQuestions.value) * 100)
  })
  const pendingRate = computed(() => {
    if (!totalQuestions.value) return 0
    return Math.round((pendingCount.value / totalQuestions.value) * 1000) / 10
  })
  const todayMastered = computed(() => Number(stats.value?.today_mastered || 0))
  const continuousDays = computed(() => {
    const rows = stats.value?.daily_counts || []
    let count = 0
    for (let i = rows.length - 1; i >= 0; i--) {
      const row = rows[i]
      if (Number(row.count || 0) > 0 || Number(row.mastered || 0) > 0) count += 1
      else if (count > 0) break
    }
    return count
  })

  const statsCards = computed(() => [
    {
      label: '题目总数',
      value: totalQuestions.value,
      suffix: '',
      hint: `当前筛选 ${total.value || 0} 题`,
      icon: 'fa-layer-group',
      tone: 'blue',
    },
    {
      label: '待复习占比',
      value: pendingRate.value,
      suffix: '%',
      hint: `待复习 ${pendingCount.value} 题`,
      icon: 'fa-fire',
      tone: 'rose',
    },
    {
      label: '掌握程度',
      value: masteryRate.value,
      suffix: '%',
      hint: masteredCount.value ? '继续加油' : '从第一题开始',
      icon: 'fa-award',
      tone: 'amber',
    },
    {
      label: '今日掌握',
      value: todayMastered.value,
      suffix: '题',
      hint: reviewingCount.value ? `复习中 ${reviewingCount.value} 题` : '暂无复习中题目',
      icon: 'fa-rotate',
      tone: 'emerald',
    },
    {
      label: '连续学习',
      value: continuousDays.value,
      suffix: '天',
      hint: '根据近 30 天记录估算',
      icon: 'fa-hands-clapping',
      tone: 'orange',
    },
  ])

  /**
   * 加载当前错题库项目的统计数据。
   */
  const loadStats = async () => {
    if (!activeQuestionProjectId.value) {
      stats.value = null
      return
    }
    try {
      stats.value = await api.fetchDashboardStats(undefined, activeQuestionProjectId.value)
    } catch (_) {
      stats.value = null
    }
  }

  return {
    stats,
    statsCards,
    loadStats,
  }
}
