// =============================================================================
// src/api/client.js —— 全局唯一的 HTTP 客户端
// =============================================================================
// 【为什么要包一层，而不是每个页面直接 axios.get】
//   1) 后端返回的是统一格式：{ code, success, message, result, timestamp }
//      如果每个页面都自己 body.result，代码会到处重复，改格式时全班返工。
//      这里用「响应拦截器」统一剥壳 → 页面里直接拿到 result，不用管外壳。
//   2) 出错统一处理：网络超时、400 参数错、401 未登录、500 服务端错，
//      都在一个地方映射成人话，页面只需 catch 后显示 e.message。
//
// 【拦截器做了什么】
//   成功：res.data 是 { success: true, result: ... } → 返回 result
//   失败：success 为 false 或 HTTP 非 2xx → Promise.reject(new Error(可读消息))
// =============================================================================
import axios from 'axios'

const client = axios.create({
  // 用相对路径，走 Vite 的 proxy（见 vite.config.js）
  // ★ 不要写死 http://127.0.0.1:8000 —— 部署时会全部返工
  baseURL: '/',
  timeout: 10000,
})

client.interceptors.response.use(
  // ---- ① 拿到响应（HTTP 2xx）----
  (res) => {
    const body = res.data

    // 后端约定：success=true 才算成功；false 时 message 是可读的错误原因
    if (body && body.success === false) {
      return Promise.reject(new Error(body.message || '请求失败'))
    }

    // 剥壳：页面里只关心 result
    return body && 'result' in body ? body.result : body
  },

  // ---- ② 出错（网络错误 / 非 2xx）----
  (err) => {
    const status = err.response?.status
    const raw = err.response?.data?.message

    const messages = {
      400: '参数不对（检查一下页码、请求体）',
      401: '未登录或登录已过期',
      404: '接口不存在（后端可能还没实现这个路径）',
      500: '服务端出错了',
    }

    const message =
      raw ||
      messages[status] ||
      (err.code === 'ECONNABORTED' ? '请求超时' : err.message || '网络错误')

    // 挂上 status，页面里想知道具体状态码可以取 e.status
    const e = new Error(message)
    e.status = status
    return Promise.reject(e)
  }
)

export default client
