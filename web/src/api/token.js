// =============================================================================
// src/api/token.js —— token 的存取（只有这三个函数，方便以后换存储方式）
// =============================================================================
// 为什么用 localStorage：
//   关掉浏览器再打开还在，7 天内免登录。
// 代价：
//   localStorage 里的 token 有 XSS 风险（页面被注入脚本能读走）。
//   所以后端所有输出都经过 Vue 转义、不用 v-html 渲染用户内容。
//   要更安全就换 HttpOnly Cookie + CSRF token。
// =============================================================================

const KEY = 'straycat_token'

export function getToken() {
  return localStorage.getItem(KEY) || ''
}

export function setToken(token) {
  localStorage.setItem(KEY, token)
}

export function clearToken() {
  localStorage.removeItem(KEY)
}
