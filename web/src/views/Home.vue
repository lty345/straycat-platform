<script setup>
// =============================================================================
// views/Home.vue —— 概览页（项目门面）
// =============================================================================
// 设计目标：一屏之内让人知道"这是什么、有什么、点哪里"。
//   ① Hero：标题 + 一句话 + 两个入口按钮 + 猫咪照片墙（留白不再空荡）
//   ② 三个入口卡：带序号，一眼看出有哪三块
//   ③ 技术要点：三栏并列，扫一眼就懂
//   ④ 后端状态：压成一行小字放到最后，不抢戏
// =============================================================================
import { onMounted, ref } from 'vue'
import { fetchHealth } from '../api/system'

const status = ref('检测中…')
const detail = ref('')
const failed = ref(false)
const ready = ref(false)

const entries = [
  {
    no: '01',
    to: '/contents',
    title: '内容',
    desc: '24 篇救助故事与养猫科普，按情绪筛选、分页浏览。',
    tag: '列表 / 详情',
  },
  {
    no: '02',
    to: '/feed',
    title: '推荐',
    desc: '标签 + 情绪 + 同城 + 热度，乘时间衰减。换一个人，顺序就变。',
    tag: '规则推荐 · 可解释',
  },
  {
    no: '03',
    to: '/cats',
    title: '领养',
    desc: '一只猫只能被一个人申请；申请后进入审核，通过即成为它的家。',
    tag: '并发抢占 · 状态机',
  },
]

const highlights = [
  { key: '可解释推荐', desc: '每条都返回分数构成，如「标签×3 + 情绪×2 + 同城×1 + 热度×0.5，衰减×0.91」' },
  { key: '并发安全', desc: '领养用原子 UPDATE + rowcount 抢占，10 个并发只成功 1 个' },
  { key: '冷启动兜底', desc: '没有标签也没有行为的新用户，按近 7 天热度推荐' },
]

// 门面用的三张猫图（都在 public/covers 里，构建时一起打包）
const photos = ['/covers/p03.jpg', '/covers/p07.jpg', '/covers/p12.jpg']

onMounted(async () => {
  try {
    const result = await fetchHealth()
    status.value = result.status === 'healthy' ? '后端在线' : '后端状态异常'
    detail.value = JSON.stringify(result)
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
  <section class="home">
    <!-- ① Hero -->
    <div class="hero">
      <div class="hero-text">
        <p class="eyebrow">STRAY&nbsp;CAT · 初尧</p>
        <h1 class="title">
          给流浪猫做的<br />内容社区
        </h1>
        <p class="lead">
          看猫、读救助故事、了解养猫知识，然后把它们带回家。
        </p>
        <div class="cta">
          <RouterLink class="btn cta-main" to="/contents">逛逛内容</RouterLink>
          <RouterLink class="btn cta-sub" to="/feed">看看推荐</RouterLink>
        </div>
        <p class="hero-note">
          技术重点不是又一套 CRUD，而是<b>可解释的个性化推荐</b>与<b>并发安全的领养抢占</b>。
        </p>
      </div>

      <div class="hero-media" aria-hidden="true">
        <img class="photo photo-1" :src="photos[0]" alt="" />
        <img class="photo photo-2" :src="photos[1]" alt="" />
        <img class="photo photo-3" :src="photos[2]" alt="" />
      </div>
    </div>

    <!-- ② 三个出口 -->
    <div class="entries">
      <RouterLink v-for="e in entries" :key="e.to" :to="e.to" class="entry">
        <span class="entry-no">{{ e.no }}</span>
        <span class="entry-tag">{{ e.tag }}</span>
        <span class="entry-title">{{ e.title }}</span>
        <span class="entry-desc">{{ e.desc }}</span>
        <span class="entry-arrow">→</span>
      </RouterLink>
    </div>

    <!-- ③ 技术要点：三栏 -->
    <div class="feature-strip">
      <div v-for="h in highlights" :key="h.key" class="feature">
        <div class="feature-key">{{ h.key }}</div>
        <p class="feature-desc">{{ h.desc }}</p>
      </div>
    </div>

    <!-- ④ 后端状态：一行 -->
    <p class="status" :class="{ bad: failed }">
      <span class="dot"></span>
      <span class="status-text">{{ status }}</span>
      <span v-if="failed" class="status-detail">{{ detail }}</span>
      <span v-else class="status-detail">
        接口正常响应 <code>GET /health</code>
      </span>
      <details v-if="ready && !failed" class="status-raw">
        <summary>原始响应</summary>
        <pre class="mono">{{ detail }}</pre>
      </details>
    </p>
  </section>
</template>

<style scoped>
/* ---------- Hero ---------- */
.hero {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 48px;
  align-items: center;
  padding: 10px 0 44px;
}

.eyebrow {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 11px;
  letter-spacing: 3px;
  color: var(--violet-l);
  opacity: 0.75;
  margin: 0 0 14px;
}

.title {
  font-size: 40px;
  line-height: 1.25;
  font-weight: 600;
  letter-spacing: 1px;
  margin: 0 0 18px;
  color: var(--fg);
}

.lead {
  font-size: 15px;
  line-height: 1.9;
  color: var(--muted);
  margin: 0 0 26px;
  max-width: 26em;
}

.cta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 22px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 22px;
  border-radius: 999px;
  font-size: 14px;
  text-decoration: none;
  transition: background 0.18s, color 0.18s, transform 0.18s, box-shadow 0.18s;
}

.cta-main {
  background: var(--violet-l);
  color: #fff;
  box-shadow: 0 6px 16px rgba(164, 95, 36, 0.22);
}
.cta-main:hover {
  background: var(--violet);
  transform: translateY(-1px);
}

.cta-sub {
  border: 1px solid var(--line);
  color: var(--fg);
  background: var(--panel);
}
.cta-sub:hover {
  border-color: var(--violet);
  color: var(--violet-l);
  transform: translateY(-1px);
}

.hero-note {
  font-size: 12.5px;
  line-height: 1.9;
  color: var(--muted);
  opacity: 0.9;
  margin: 0;
}
.hero-note b {
  color: var(--fg);
  font-weight: 500;
}

/* ---------- 照片墙 ---------- */
.hero-media {
  position: relative;
  height: 300px;
}
.photo {
  position: absolute;
  object-fit: cover;
  border-radius: 14px;
  box-shadow: 0 12px 30px rgba(70, 50, 30, 0.16);
  border: 4px solid var(--panel);
  background: var(--bg-soft);
}
.photo-1 {
  width: 74%;
  height: 100%;
  right: 0;
  top: 0;
  transform: rotate(1.5deg);
}
.photo-2 {
  width: 46%;
  height: 56%;
  left: 0;
  bottom: -6px;
  transform: rotate(-4deg);
}
.photo-3 {
  width: 30%;
  height: 36%;
  left: 26%;
  top: -10px;
  transform: rotate(5deg);
}

/* ---------- 三个出口 ---------- */
.entries {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr));
  gap: 14px;
  margin-bottom: 28px;
}

.entry {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 22px 20px 20px;
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  background: var(--panel);
  box-shadow: var(--card-shadow);
  text-decoration: none;
  transition: border-color 0.18s, transform 0.18s, box-shadow 0.18s;
}
.entry:hover {
  border-color: var(--violet);
  transform: translateY(-3px);
  box-shadow: var(--card-shadow-hover);
}

.entry-no {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 12px;
  color: var(--violet);
  opacity: 0.65;
  letter-spacing: 1px;
}
.entry-tag {
  font-size: 11.5px;
  color: var(--muted);
}
.entry-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--fg);
  letter-spacing: 0.5px;
}
.entry-desc {
  font-size: 12.5px;
  line-height: 1.85;
  color: var(--muted);
}
.entry-arrow {
  position: absolute;
  right: 20px;
  top: 20px;
  color: var(--muted);
  transition: color 0.18s, transform 0.18s;
}
.entry:hover .entry-arrow {
  color: var(--violet-l);
  transform: translateX(4px);
}

/* ---------- 技术要点 ---------- */
.feature-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr));
  gap: 1px;
  background: var(--border-soft);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 24px;
}
.feature {
  background: var(--panel);
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
  line-height: 1.8;
  color: var(--muted);
}

/* ---------- 后端状态 ---------- */
.status {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin: 0;
  padding: 12px 2px 0;
  border-top: 1px solid var(--border-soft);
  font-size: 12px;
  color: var(--muted);
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--ok, #4f9d69);
  flex-shrink: 0;
}
.status.bad .dot {
  background: var(--bad, #c0563f);
}
.status code {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 11px;
  padding: 1px 5px;
  border-radius: 3px;
  background: var(--bg-soft);
}
.status-raw summary {
  cursor: pointer;
  color: var(--muted);
}
.mono {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 11px;
  color: var(--muted);
  margin: 8px 0 0;
  white-space: pre-wrap;
  word-break: break-all;
}

/* ---------- 窄屏 ---------- */
@media (max-width: 860px) {
  .hero {
    grid-template-columns: 1fr;
    gap: 26px;
    padding-bottom: 30px;
  }
  .title {
    font-size: 30px;
  }
  .hero-media {
    height: 210px;
    order: -1;
  }
}
</style>
