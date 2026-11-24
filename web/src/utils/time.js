// =============================================================================
// src/utils/time.js —— 时间显示
// =============================================================================
// 为什么不用原始的 "2026-11-13 22:12:13"：
//   列表页里精确到秒没有意义，反而抢注意力。成熟产品（小红书 / 掘金 / 知乎）
//   列表一律显示"3 天前"，详情页才给具体时间。
// =============================================================================

/** 后端返回的 "2026-11-13 22:12:13"（无时区）→ 相对时间 */
export function fromNow(input) {
  if (!input) return ''
  const text = String(input).replace(' ', 'T')
  const t = new Date(text)
  if (Number.isNaN(t.getTime())) return String(input)

  const diff = (Date.now() - t.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  if (diff < 86400 * 30) return `${Math.floor(diff / 86400)} 天前`

  const y = t.getFullYear()
  const m = String(t.getMonth() + 1).padStart(2, '0')
  const d = String(t.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/** 详情页用：完整时间 */
export function fullTime(input) {
  if (!input) return ''
  return String(input).slice(0, 16)   // 去掉秒
}
