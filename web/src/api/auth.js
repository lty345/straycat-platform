// =============================================================================
// src/api/auth.js —— 认证接口封装
// =============================================================================
// 注意：后端 Pydantic 字段是 interest_tags（下划线），
// 前端习惯 camelCase，所以在这一层做映射 —— 页面里保持 camelCase。
// =============================================================================
import client from './client'

export function register({ username, password, nickname, city, interestTags }) {
  return client.post('/api/v1/auth/register', {
    username,
    password,
    nickname,
    city,
    interest_tags: interestTags,
  })
}

export function login({ username, password }) {
  return client.post('/api/v1/auth/login', { username, password })
}

export function fetchMe() {
  return client.get('/api/v1/auth/me')
}
