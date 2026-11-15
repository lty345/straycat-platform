// =============================================================================
// src/api/cat.js —— 领养模块接口
// =============================================================================
import client from './client'

/**
 * 分页查猫
 * @param {Object} p
 * @param {string} p.status   待领养 / 审核中 / 已领养（空 = 全部）
 * @param {string} p.city     城市（空 = 不限）
 * @param {number} p.page
 * @param {number} p.pageSize
 */
export function fetchCats({ status = '', city = '', page = 1, pageSize = 20 } = {}) {
  const params = { page, page_size: pageSize }
  if (status) params.status = status
  if (city) params.city = city
  return client.get('/api/v1/cats', { params })
}

/**
 * 申请领养一只猫
 *
 * ★ 失败时（比如 20001「这只猫已被他人申请」）拦截器会 reject，
 *   调用方 catch 到的 e.message 就是后端那句话，直接显示即可。
 */
export function adoptCat(catId, userId) {
  return client.post(`/api/v1/cats/${catId}/adopt`, { user_id: userId })
}
