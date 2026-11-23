// =============================================================================
// src/auth/store.js —— 全局登录态
// =============================================================================
// 为什么用 reactive 而不是 Pinia：
//   整个项目只有一个"当前用户"对象，Pinia 是"为了以后可能变复杂"。
//   能用 20 行解决的不引库。
// =============================================================================
import { reactive } from 'vue'

import { fetchMe, login as apiLogin, register as apiRegister } from '../api/auth'
import { clearToken, getToken, setToken } from '../api/token'

export const auth = reactive({
  user: null,     // 当前登录用户，未登录 = null
  ready: false,   // 是否已经尝试过恢复登录态（防止重复请求 /me）
})

/** 页面刷新后，用 localStorage 里的 token 换回用户信息 */
export async function restoreSession() {
  if (auth.ready) return
  if (!getToken()) {
    auth.ready = true
    return
  }
  try {
    auth.user = await fetchMe()
  } catch {
    auth.user = null
    clearToken()          // token 失效就清掉，别一直带着坏 token
  } finally {
    auth.ready = true
  }
}

export async function doLogin(payload) {
  const data = await apiLogin(payload)   // { token, expires_in, user }
  setToken(data.token)
  auth.user = data.user
  return data.user
}

export async function doRegister(payload) {
  const data = await apiRegister(payload)
  setToken(data.token)
  auth.user = data.user
  return data.user
}

export function doLogout() {
  clearToken()
  auth.user = null
}
