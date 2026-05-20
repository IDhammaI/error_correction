/**
 * 题目分割历史 API。
 *
 * 用于查看历史分割记录及其详情，和当前上传会话解耦。
 */
import { assertJsonSuccess } from './client.js'

/** 获取最近的题目分割历史记录。 */
export async function fetchSplitRecords(limit = 10) {
  const qs = new URLSearchParams({ limit })
  const resp = await fetch(`/api/split-records?${qs}`)
  const data = await assertJsonSuccess(resp, '获取分割历史失败')
  return data.records
}

/** 获取单条分割历史的完整详情。 */
export async function fetchSplitRecordDetail(recordId) {
  const resp = await fetch(`/api/split-records/${recordId}`)
  const data = await assertJsonSuccess(resp, '获取分割记录详情失败')
  return data.record
}
