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

import { clearToken, getToken } from './token'

// 开发时留空 → 走 Vite 的 proxy（见 vite.config.js）
// 部署时用 VITE_API_BASE 指向后端公网地址，例如 https://xxx.ap-shanghai.app.tcloudbase.com
const API_BASE = import.meta.env.VITE_API_BASE || '/'

const client = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

// ---- 请求拦截器：每次请求自动带上 token ----
// 没登录（没 token）就不加这个头，后端返回 10401，前端跳登录

// 后端 400 时返回的是 Pydantic 的原始 detail（英文 + 字段路径），
// 直接甩给用户没人看得懂。这里翻译成"哪个字段、错在哪"。
const FIELD_NAMES = {
  username: '用户名',
  password: '密码',
  nickname: '昵称',
  city: '城市',
  interest_tags: '兴趣标签',
}

function describeDetail(detail) {
  if (!Array.isArray(detail) || !detail.length) return null
  const d = detail[0]
  const field = FIELD_NAMES[d.loc?.[1]] || d.loc?.[1] || ''
  const type = String(d.type || '')
  if (type.includes('min_length')) return `${field}至少 ${d.ctx?.min_length ?? ''} 位`
  if (type.includes('max_length')) return `${field}最多 ${d.ctx?.max_length ?? ''} 位`
  if (type.includes('pattern_mismatch')) return `${field}只能包含字母、数字、下划线，3~32 位`
  if (type.includes('missing')) return `请填写${field}`
  return `${field}格式不正确`
}

client.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  // ---- ① 拿到响应（HTTP 2xx）----
  (res) => {
    const body = res.data

    // 后端约定：success=true 才算成功；false 时 message 是可读的错误原因
    if (body && body.success === false) {
      const friendly = describeDetail(body.result?.detail)
      const e = new Error(friendly || body.message || '请求失败')
      e.apiCode = body.api_code          // 把业务码带出去，页面可据此分支
      e.field = body.result?.detail?.[0]?.loc?.[1] || null   // 哪个字段出错
      // ★ 后端约定业务失败也返回 HTTP 200，所以"登录失效"要在这一层判断
      if (body.api_code === 10401) {
        clearToken()
        window.dispatchEvent(new CustomEvent('auth:expired'))
      }
      return Promise.reject(e)
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

    // 挂上 status / apiCode，页面里想知道具体码可以取 e.status / e.apiCode
    const e = new Error(message)
    e.status = status
    e.apiCode = err.response?.data?.api_code
    if (status === 401) {
      clearToken()
      window.dispatchEvent(new CustomEvent('auth:expired'))
    }
    return Promise.reject(e)
  }
)

export default client
