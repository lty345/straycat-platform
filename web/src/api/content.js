// =============================================================================
// src/api/content.js —— 内容模块的接口封装【待你实现】
// =============================================================================
// 【先把 client 搞清楚再动手】
//   ../api/client.js 里已经配好了 axios 实例和响应拦截器：
//     - 拦截器会把后端统一响应 { code, success, message, result } 剥壳
//     - 所以你在页面里 await 拿到的是**直接的 result**，不是整个外壳
//     - 出错时拦截器已经 reject 了一个带人话 message 的 Error
//   也就是说：这里不需要 try/catch，也不需要 body.result。
//
// 【你要写的】
//   用 client.get('/api/v1/contents', { params: { page, page_size } })
//   把请求发出去，并把 Promise 返回给调用方。
//
// 【后端接口（还没实现，这是你要做的另一半）】
//   GET /api/v1/contents?page=1&page_size=10
//   → { list: [...], total: 20, page: 1, page_size: 10 }
//   注意：查询参数名是 page_size（下划线），前端这边习惯写 pageSize（驼峰），
//        两边的命名差异就在这里做一次转换，不要让它漏到页面里去。
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
  // TODO(你)：一行代码，去掉下面这行 throw，换成真正的请求
  throw new Error('fetchContents 还没实现')
}
