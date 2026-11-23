<script setup>
// =============================================================================
// views/About.vue —— 关于本项目（技术向，给面试官/感兴趣的人看）
// =============================================================================
// 首页只放访客关心的内容；技术定位、后端健康检查、数据统计都收在这里，
// 想看的人自然会点进来。地址：/about
// =============================================================================
import { onMounted, ref } from 'vue'
import { fetchHealth } from '../api/system'
import { fetchContents } from '../api/content'
import { fetchUsers } from '../api/user'

const status = ref('检测中…')
const detail = ref('')
const failed = ref(false)
const ready = ref(false)

const stats = ref({ contents: 0, users: 0 })

const highlights = [
  {
    key: '可解释推荐',
    desc: '每条推荐都返回分数构成：标签×3 + 情绪×2 + 同城×1 + 热度×0.5，再乘时间衰减。不是黑盒排序。',
  },
  {
    key: '并发安全',
    desc: '领养用原子 UPDATE ... WHERE status=\'待领养\' + rowcount 判定，10 个并发请求只会有 1 个成功。',
  },
  {
    key: '冷启动兜底',
    desc: '没有标签也没有行为记录的新用户，退化成「近 7 天热度 Top20」，不会给出空列表。',
  },
  {
    key: '分层与测试',
    desc: 'apis / services / db 三层，repo 不提交事务；16 个自动化测试覆盖分页、埋点、推荐与并发抢占。',
  },
]

onMounted(async () => {
  try {
    const [health, contents, users] = await Promise.all([
      fetchHealth(),
      fetchContents({ page: 1, pageSize: 1 }),
      fetchUsers(),
    ])
    status.value = health.status === 'healthy' ? '后端在线' : '后端状态异常'
    detail.value = JSON.stringify(health, null, 2)
    stats.value = { contents: contents.total ?? 0, users: users.length ?? 0 }
  } catch (e) {
    failed.value = true
    status.value = '连不上后端'
    detail.value = e.message
  } finally {
    ready.value = true
  }
})
</script>

<template>
  <section class="about">
    <p class="eyebrow">ABOUT</p>
    <h1 class="title">关于这个项目</h1>
    <p class="lead">
      初尧是一个给流浪猫做的内容社区。技术重点不是又一套 CRUD，
      而是<b>可解释的个性化推荐</b>和<b>并发安全的领养抢占</b>。
    </p>

    <div class="stats">
      <div class="stat">
        <span class="stat-num">{{ stats.contents || '—' }}</span>
        <span class="stat-label">篇内容</span>
      </div>
      <div class="stat">
        <span class="stat-num">{{ stats.users || '—' }}</span>
        <span class="stat-label">位用户</span>
      </div>
      <div class="stat">
        <span class="stat-num" :class="{ bad: failed }">{{ failed ? '离线' : '在线' }}</span>
        <span class="stat-label">后端状态</span>
      </div>
    </div>

    <div class="feature-grid">
      <div v-for="h in highlights" :key="h.key" class="feature">
        <div class="feature-key">{{ h.key }}</div>
        <p class="feature-desc">{{ h.desc }}</p>
      </div>
    </div>

    <div class="card">
      <div class="card-head">
        <span class="dia">◈</span>
        <span>后端连通性</span>
        <span class="badge" :class="failed ? 'b-bad' : 'b-ok'">{{ status }}</span>
      </div>
      <p class="health-line">
        <span class="dot" :class="failed ? 'b-bad' : 'b-ok'"></span>
        <span v-if="failed">{{ detail }}</span>
        <span v-else>接口正常响应（<code>GET /health</code>）</span>
      </p>
      <details v-if="ready && !failed" class="raw">
        <summary>查看原始响应</summary>
        <pre class="mono">{{ detail }}</pre>
      </details>
    </div>
  </section>
</template>

<style scoped>
.eyebrow {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 11px;
  letter-spacing: 3px;
  color: var(--violet-l);
  opacity: 0.75;
  margin: 0 0 12px;
}
.title {
  font-size: 28px;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin: 0 0 14px;
}
.lead {
  font-size: 14px;
  line-height: 1.9;
  color: var(--muted);
  margin: 0 0 28px;
  max-width: 40em;
}
.lead b {
  color: var(--fg);
  font-weight: 500;
}

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(140px, 100%), 1fr));
  gap: 1px;
  background: var(--border-soft);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 28px;
}
.stat {
  background: var(--panel);
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.stat-num {
  font-size: 24px;
  font-weight: 600;
  color: var(--violet-l);
}
.stat-num.bad {
  color: var(--bad);
}
.stat-label {
  font-size: 12px;
  color: var(--muted);
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(230px, 100%), 1fr));
  gap: 14px;
  margin-bottom: 28px;
}
.feature {
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  background: var(--panel);
  box-shadow: var(--card-shadow);
  padding: 18px 20px;
}
.feature-key {
  font-size: 13px;
  color: var(--violet-l);
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}
.feature-desc {
  margin: 0;
  font-size: 12.5px;
  line-height: 1.85;
  color: var(--muted);
}

.card {
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  box-shadow: var(--card-shadow);
  padding: 18px 20px;
  background: var(--panel);
}
.card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  margin-bottom: 14px;
}
.dia {
  color: var(--violet);
  font-size: 12px;
}
.badge {
  margin-left: auto;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 2px;
  border: 1px solid var(--border-soft);
  color: var(--muted);
}
.b-ok {
  color: var(--ok);
  border-color: var(--ok);
}
.b-bad {
  color: var(--bad);
  border-color: var(--bad);
}
.health-line {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 13px;
  color: var(--muted);
}
.health-line code {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 12px;
  padding: 1px 5px;
  border-radius: 3px;
  background: var(--bg-soft);
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot.b-ok { background: var(--ok, #4f9d69); }
.dot.b-bad { background: var(--bad, #c0563f); }

.raw {
  margin-top: 12px;
  font-size: 12px;
  color: var(--muted);
}
.raw summary {
  cursor: pointer;
  user-select: none;
}
.mono {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 11px;
  color: var(--muted);
  margin: 8px 0 0;
  padding: 10px;
  background: var(--bg-soft);
  border-radius: var(--radius-sm);
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
