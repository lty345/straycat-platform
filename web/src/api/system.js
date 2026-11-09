// src/api/system.js —— 系统类接口
import client from './client'

/** 健康检查：后端活着吗（这个接口现在已经有了） */
export function fetchHealth() {
  return client.get('/health')
}
