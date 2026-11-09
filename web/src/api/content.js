// =============================================================================
// src/api/content.js —— 内容模块的接口封装
// =============================================================================
// 【规矩】
//   页面组件里不要出现 axios / URL 字符串，全部走这里。
//   好处：接口路径变了只改这一个文件；也方便以后换成 mock。
//
// ★ 下面这个 fetchContents 对应的后端接口【还没写】。
//   它是你下一步要做的垂直切片：
//     后端：apis/content/api/content.py  →  GET /api/v1/contents?page=&page_size=
//     前端：这个文件 → ContentList.vue
//   在它没实现之前，页面会显示"接口不存在（404）"，这是正常的。
// =============================================================================
import client from './client'

/**
 * 分页拉内容列表
 * @param {Object} p
 * @param {number} p.page     第几页（从 1 开始）
 * @param {number} p.pageSize 每页几条（后端上限 100）
 * @returns {Promise<{list:Array, total:number, page:number, page_size:number}>}
 */
export function fetchContents({ page = 1, pageSize = 10 } = {}) {
  return client.get('/api/v1/contents', {
    params: { page, page_size: pageSize },
  })
}
