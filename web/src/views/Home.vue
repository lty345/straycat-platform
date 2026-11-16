<script setup>
// =============================================================================
// views/Home.vue —— 概览页
// =============================================================================
// 从"开发脚手架"改成"项目门面"：
//   ① 一句话说清这个项目是什么
//   ② 三个入口（内容 / 推荐 / 领养）
//   ③ 技术要点（面试官先看这一屏）
//   ④ 后端连通性（保留，方便本地排查）
// =============================================================================
import { onMounted, ref } from 'vue'
import { fetchHealth } from '../api/system'

const status = ref('检测中…')
const detail = ref('')
const failed = ref(false)

const entries = [
  {
    to: '/contents',
    title: '内容',
    desc: '24 篇救助故事与养猫科普，按情绪筛选、分页浏览。',
    tag: '列表 / 详情',
  },
  {
    to: '/feed',
    title: '推荐',
    desc: '标签 + 情绪 + 同城 + 热度，乘时间衰减。换一个人，顺序就变。',
    tag: '规则推荐 · 可解释',
  },
  {
    to: '/cats',
    title: '领养',
    desc: '一只猫只能被一个人申请；申请后进入审核，通过即成为它的家。',
    tag: '并发抢占 · 状态机',
  },
]

const highlights = [
  ['可解释推荐', '每条都返回分数构成，如「标签×3 + 情绪×2 + 同城×1 + 热度×0.5，衰减×0.91」'],
  ['并发安全', '领养用原子 UPDATE + rowcount 抢占，10 个并发只成功 1 个'],
  ['冷启动兜底', '没有标签也没有行为的新用户，按近 7 天热度推荐'],
]

onMounted(async () => {
  try {
    const result = await fetchHealth()
    status.value = result.status === 'healthy' ? '后端在线' : '后端状态异常'
    detail.value = JSON.stringify(result)
  } catch (e) {
    failed.value = true
    status.value = '连不上后端'
    detail.value = e.message + '（后端起了吗？uv run fastapi dev app.py）'
  }
})
</script>

<template>
  <section>
    <p class="eyebrow">STRAY CAT</p>
    <h1 class="h1">给流浪猫做的内容社区</h1>
    <p class="lead">
      看猫、读救助故事、了解养猫知识，然后把它们带回家。<br />
      技术重点不是又一套 CRUD，而是<b>可解释的个性化推荐</b>和<b>并发安全的领养抢占</b>。
    </p>

    <div class="entries">
      <RouterLink v-for="e in entries" :key="e.to" :to="e.to" class="entry">
        <span class="entry-tag">{{ e.tag }}</span>
        <span class="entry-title">{{ e.title }}</span>
        <span class="entry-desc">{{ e.desc }}</span>
        <span class="entry-arrow">→</span>
      </RouterLink>
    </div>

    <div class="card">
      <div class="card-head">
        <span class="dia">◈</span>
        <span>技术要点</span>
      </div>
      <dl class="highlights">
        <template v-for="h in highlights" :key="h[0]">
          <dt>{{ h[0] }}</dt>
          <dd>{{ h[1] }}</dd>
        </template>
      </dl>
    </div>

    <div class="card health" :class="{ bad: failed }">
      <div class="card-head">
        <span class="dia">◈</span>
        <span>后端连通性</span>
        <span class="badge" :class="failed ? 'b-bad' : 'b-ok'">{{ status }}</span>
      </div>
      <pre class="mono">{{ detail || '—' }}</pre>
    </div>
  </section>
</template>

<style scoped>
.eyebrow {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 11px;
  letter-spacing: 3px;
  color: var(--violet-l);
  opacity: 0.7;
  margin: 0 0 10px;
}
.h1 {
  font-size: 26px;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin: 0 0 14px;
}
.lead {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.9;
  margin: 0 0 30px;
}
.lead b {
  color: var(--fg);
  font-weight: 500;
}

/* ---- 三个入口 ---- */
.entries {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 14px;
  margin-bottom: 28px;
}
.entry {
  position: relative;
  border: 1px solid var(--border-soft);
  background: var(--panel);
  box-shadow: var(--card-shadow);
  border-radius: var(--radius);
  padding: 18px;
  text-decoration: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: border-color 0.18s, transform 0.18s;
}
.entry:hover {
  border-color: var(--violet);
  transform: translateY(-2px);
}
.entry-tag {
  font-size: 11px;
  color: var(--violet-l);
  opacity: 0.75;
}
.entry-title {
  font-size: 17px;
  color: var(--fg);
  font-weight: 500;
}
.entry-desc {
  font-size: 12.5px;
  color: var(--muted);
  line-height: 1.8;
}
.entry-arrow {
  position: absolute;
  right: 16px;
  top: 16px;
  color: var(--muted);
  font-size: 13px;
  transition: color 0.18s, transform 0.18s;
}
.entry:hover .entry-arrow {
  color: var(--violet-l);
  transform: translateX(3px);
}

/* ---- 通用卡片 ---- */
.card {
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  box-shadow: var(--card-shadow);
  padding: 18px 20px;
  margin-bottom: 16px;
  background: var(--panel);
}
.card.bad {
  border-color: var(--bad);
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

/* ---- 技术要点 ---- */
.highlights {
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 10px 16px;
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
}
.highlights dt {
  color: var(--violet-l);
  opacity: 0.85;
}
.highlights dd {
  color: var(--muted);
  margin: 0;
}

.mono {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 12px;
  color: var(--muted);
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
