<script setup>
// =============================================================================
// views/Home.vue —— 概览页（用户视角）
// =============================================================================
// 这一段只放"访客关心的事"：
//   ① Hero：这是什么 + 两个入口
//   ② 三个频道入口
//   ③ 最新救助故事（真实数据，3 条）
//   ④ 等待一个家的猫（真实数据，3 只）
//
// 技术要点 / 后端健康检查 / 埋点统计 → 挪到 /about（给面试官看，不在首页）
// =============================================================================
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchContents } from '../api/content'
import { fetchCats } from '../api/cat'

const router = useRouter()

const entries = [
  {
    no: '01',
    to: '/contents',
    title: '内容',
    desc: '24 篇救助故事与养猫科普，按情绪筛选、分页浏览。',
    tag: '故事 · 科普',
  },
  {
    no: '02',
    to: '/feed',
    title: '推荐',
    desc: '按你喜欢的标签和情绪，挑出可能对胃口的几篇。',
    tag: '为你挑选',
  },
  {
    no: '03',
    to: '/cats',
    title: '领养',
    desc: '一只猫只能被一个人申请；申请后进入审核，通过即成为它的家。',
    tag: '找个家',
  },
]

const photos = ['/covers/p03.jpg', '/covers/p07.jpg', '/covers/p12.jpg']

const stories = ref([])
const cats = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const [contentRes, catRes] = await Promise.all([
      fetchContents({ page: 1, pageSize: 3 }),
      fetchCats({ status: '待领养', pageSize: 3 }),
    ])
    stories.value = contentRes.list ?? []
    cats.value = catRes.list ?? []
  } catch (e) {
    stories.value = []
    cats.value = []
  } finally {
    loading.value = false
  }
}

function openStory(it) {
  router.push({ name: 'content-detail', params: { id: it.id } })
}

onMounted(load)
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
        <p class="lead">看猫、读救助故事、了解养猫知识，然后把它们带回家。</p>
        <div class="cta">
          <RouterLink class="btn cta-main" to="/contents">逛逛内容</RouterLink>
          <RouterLink class="btn cta-sub" to="/cats">看看待领养的猫</RouterLink>
        </div>
      </div>

      <div class="hero-media" aria-hidden="true">
        <img class="photo photo-1" :src="photos[0]" alt="" />
        <img class="photo photo-2" :src="photos[1]" alt="" />
        <img class="photo photo-3" :src="photos[2]" alt="" />
      </div>
    </div>

    <!-- ② 三个频道 -->
    <div class="entries">
      <RouterLink v-for="e in entries" :key="e.to" :to="e.to" class="entry">
        <span class="entry-no">{{ e.no }}</span>
        <span class="entry-tag">{{ e.tag }}</span>
        <span class="entry-title">{{ e.title }}</span>
        <span class="entry-desc">{{ e.desc }}</span>
        <span class="entry-arrow">→</span>
      </RouterLink>
    </div>

    <!-- ③ 最新故事 -->
    <section class="block">
      <div class="block-head">
        <h2 class="block-title">最新故事</h2>
        <RouterLink class="more" to="/contents">全部 24 篇 →</RouterLink>
      </div>

      <p v-if="loading" class="hint">载入中…</p>
      <p v-else-if="!stories.length" class="hint">暂时没有内容</p>
      <div v-else class="story-grid">
        <article
          v-for="it in stories"
          :key="it.id"
          class="story"
          role="link"
          tabindex="0"
          @click="openStory(it)"
          @keyup.enter="openStory(it)"
        >
          <div class="story-cover">
            <img v-if="it.cover_url" :src="it.cover_url" :alt="it.title" loading="lazy" />
          </div>
          <div class="story-body">
            <h3 class="story-title">{{ it.title }}</h3>
            <p class="story-summary">{{ it.summary }}</p>
            <div class="story-meta">
              <span v-if="it.mood" class="mood" :data-mood="it.mood">{{ it.mood }}</span>
              <span>{{ it.city }}</span>
            </div>
          </div>
        </article>
      </div>
    </section>

    <!-- ④ 等待一个家 -->
    <section class="block">
      <div class="block-head">
        <h2 class="block-title">等待一个家的猫</h2>
        <RouterLink class="more" to="/cats">全部待领养 →</RouterLink>
      </div>

      <p v-if="loading" class="hint">载入中…</p>
      <p v-else-if="!cats.length" class="hint">现在没有待领养的猫</p>
      <div v-else class="cat-grid">
        <RouterLink v-for="cat in cats" :key="cat.id" to="/cats" class="mini-cat">
          <div class="mini-cover">
            <img v-if="cat.cover_url" :src="cat.cover_url" :alt="cat.name" loading="lazy" />
          </div>
          <div class="mini-body">
            <div class="mini-name">
              {{ cat.name }}
              <span class="mini-breed">{{ cat.breed }}</span>
            </div>
            <p class="mini-meta">{{ cat.age_month }} 个月 · {{ cat.city }}</p>
            <p class="mini-health">{{ cat.health }}</p>
          </div>
        </RouterLink>
      </div>
    </section>
  </section>
</template>

<style scoped>
/* ---------- Hero ---------- */
.hero {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 48px;
  align-items: center;
  padding: 10px 0 46px;
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
  max-width: 24em;
}

.cta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
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

/* ---------- 三个频道 ---------- */
.entries {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr));
  gap: 14px;
  margin-bottom: 40px;
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

/* ---------- 区块通用 ---------- */
.block {
  margin-bottom: 44px;
}
.block-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}
.block-title {
  font-size: 19px;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin: 0;
  color: var(--fg);
}
.more {
  font-size: 12.5px;
  color: var(--muted);
  text-decoration: none;
}
.more:hover {
  color: var(--violet-l);
}
.hint {
  color: var(--muted);
  font-size: 13px;
}

/* ---------- 最新故事 ---------- */
.story-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr));
  gap: 16px;
}

.story {
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  background: var(--panel);
  box-shadow: var(--card-shadow);
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.18s, transform 0.18s, box-shadow 0.18s;
}
.story:hover {
  border-color: var(--violet);
  transform: translateY(-3px);
  box-shadow: var(--card-shadow-hover);
}
.story:focus-visible {
  outline: 2px solid var(--violet);
  outline-offset: 2px;
}

.story-cover {
  aspect-ratio: 16 / 10;
  background: var(--bg-soft);
}
.story-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.story-body {
  padding: 14px 16px 16px;
}
.story-title {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.5;
  margin: 0 0 8px;
  color: var(--fg);
}
.story-summary {
  font-size: 12.5px;
  line-height: 1.8;
  color: var(--muted);
  margin: 0 0 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.story-meta {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 11.5px;
  color: var(--muted);
}
.mood {
  padding: 1px 8px;
  border-radius: 999px;
  border: 1px solid currentColor;
  font-size: 11px;
}
.mood[data-mood='治愈'] { color: var(--mood-cure); }
.mood[data-mood='揪心'] { color: var(--mood-heart); }
.mood[data-mood='欢乐'] { color: var(--mood-fun); }
.mood[data-mood='科普'] { color: var(--mood-know); }

/* ---------- 等待领养 ---------- */
.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr));
  gap: 16px;
}
.mini-cat {
  display: flex;
  gap: 14px;
  padding: 12px;
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  background: var(--panel);
  box-shadow: var(--card-shadow);
  text-decoration: none;
  transition: border-color 0.18s, transform 0.18s, box-shadow 0.18s;
}
.mini-cat:hover {
  border-color: var(--violet);
  transform: translateY(-3px);
  box-shadow: var(--card-shadow-hover);
}
.mini-cover {
  width: 96px;
  height: 96px;
  flex-shrink: 0;
  border-radius: 10px;
  overflow: hidden;
  background: var(--bg-soft);
}
.mini-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.mini-body {
  min-width: 0;
}
.mini-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--fg);
  margin-bottom: 6px;
}
.mini-breed {
  font-size: 11.5px;
  font-weight: 400;
  color: var(--muted);
  margin-left: 4px;
}
.mini-meta,
.mini-health {
  margin: 0 0 4px;
  font-size: 12px;
  color: var(--muted);
  line-height: 1.7;
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
