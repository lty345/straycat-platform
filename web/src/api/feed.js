// =============================================================================
// src/api/feed.js —— 推荐流接口
// =============================================================================
// 和 content.js 一样：组件里不出现 URL，全部走这里。
// 注意参数名的驼峰→下划线转换（userId → user_id），只在这一层做。
// =============================================================================
import client from './client'

/**
 * 拉取个性化推荐流
 * @param {Object} p
 * @param {number} p.userId   用户 id
 * @param {number} p.page     第几页（从 1 开始）
 * @param {number} p.pageSize 每页几条
 * @returns {Promise<{list:Array, total:number, cold_start:boolean, preferred_mood:string|null}>}
 */
export function fetchFeed({ userId, page = 1, pageSize = 20 } = {}) {
  return client.get('/api/v1/feed', {
    params: { user_id: userId, page, page_size: pageSize },
  })
}
