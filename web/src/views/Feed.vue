<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchFeed } from '../api/feed'
import { fetchUsers } from '../api/user'
import { useRouter } from 'vue-router'

// ★ 不再硬编码 id：种子脚本重跑、id 变化后界面就点不动了
const users = ref([])
const userId = ref(null)
const data = ref(null)      // 接口返回的整个 result
const loading = ref(false)
const error = ref('')
const router = useRouter()
const items   = computed(() => data.value?.list ?? [])              // data 里的 list
const coldStart = computed(() => data.value?.cold_start ?? false)            // data 里的 cold_start
const preferredMood = computed(() => data.value?.preferred_mood ?? null)        // data 里的 preferred_mood

async function load() {
  if (!userId.value) return
  loading.value = true
  error.value = ''
  try {
    data.value = await fetchFeed({ userId: userId.value, pageSize: 10 })
  } catch (e) {
    error.value = e.message
    data.value = null
  } finally {
    loading.value = false
  }
}

function openDetail(it) {
  router.push({ name: 'content-detail', params: { id: it.id } })
}

function switchUser(id) {
  userId.value = id
  load()          // 换人立刻重拉
}

onMounted(async () => {
  try {
    const list = await fetchUsers()
    users.value = list.map((u) => ({
      id: u.id,
      name: u.nickname,
      desc: u.interest_tags || '冷启动',
    }))
    if (users.value.length) userId.value = users.value[0].id
  } catch (e) {
    error.value = e.message
  }
  await load()
})
</script>

<template>
  <section>
    <h1>推荐</h1>

    <!-- 用户切换：点一下换一个人，看顺序怎么变 -->
    <div class="users">
      <button v-for="u in users" :key="u.id"
              :class="{ on: userId === u.id }"
              @click="switchUser(u.id)">
        {{ u.name }}<small>{{ u.desc }}</small>
      </button>
    </div>

    <!-- 冷启动提示：只有走兜底时才出现 -->
    <p v-if="coldStart" class="cold">
      这个用户没有兴趣标签也没有行为记录，按「近 7 天热门」推荐
    </p>

    <!-- 四态 -->
    <p v-if="error">出错了：{{ error }}</p>
    <p v-else-if="loading">加载中…</p>
    <p v-else-if="items.length === 0">还没有可推荐的内容</p>
    <ul v-else class="list">
      <li v-for="it in items" :key="it.id" class="card" @click="openDetail(it)">
        <img
          v-if="it.cover_url"
          class="thumb"
          :src="it.cover_url"
          :alt="it.title"
          loading="lazy"
        />
        <div class="body">
          <div class="top">
            <span class="title">{{ it.title }}</span>
            <span class="score">{{ it.score }}</span>
          </div>
          <p class="summary">{{ it.summary }}</p>
          <div class="meta">
            <span>{{ it.mood }}</span>
            <span>{{ it.city }}</span>
            <span v-if="preferredMood">偏好情绪：{{ preferredMood }}</span>
          </div>
          <p class="reason">{{ it.reason }}</p>   <!-- ★ 这一行是这一页的灵魂 -->
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped>
/* 颜色只用 src/style.css 里的变量 */
h1 {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 1px;
  margin: 0 0 20px;
}

/* ---- 用户切换 ---- */
.users {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}
.users button {
  background: transparent;
  border: 1px solid var(--line);
  color: var(--muted);
  font-size: 13px;
  padding: 7px 14px;
  border-radius: 2px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;
  text-align: left;
  transition: color 0.15s, border-color 0.15s;
}
.users button:hover {
  color: var(--fg);
}
.users button.on {
  color: var(--violet-l);
  border-color: var(--violet);
}
.users button small {
  font-size: 11px;
  opacity: 0.6;
}

/* ---- 冷启动提示条 ---- */
.cold {
  border-left: 2px solid var(--violet);
  background: var(--panel);
  color: var(--muted);
  font-size: 12px;
  padding: 8px 12px;
  margin: 0 0 16px;
}

/* ---- 列表 ---- */
.list {
  list-style: none;
  margin: 0;
  padding: 0;
  align-items: stretch;
  /* 宽屏两列，窄屏一列 */
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(480px, 100%), 1fr))  /* min(...)：窄屏时列宽不超过视口，否则横向溢出 */;
  gap: 12px;
}
.card {
  cursor: pointer;
  display: flex;
  gap: 14px;
  border: 1px solid var(--border-soft);
  background: var(--panel);
  box-shadow: var(--card-shadow);
  border-radius: var(--radius);
  padding: 12px;
  transition: border-color 0.18s, transform 0.18s, box-shadow 0.18s;
}
.card:hover {
  border-color: var(--violet);
  transform: translateY(-2px);
  box-shadow: var(--card-shadow-hover);
}
/* 封面缩略图：固定尺寸 + object-fit，任何图都不变形 */
.thumb {
  flex-shrink: 0;
  width: 132px;
  height: 100px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  background: var(--bg-soft);
}
.body {
  flex: 1;
  min-width: 0;
}
.top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}
.title {
  font-size: 15px;
  color: var(--fg);
}
/* 分数用等宽 + 亮紫色，让人一眼看到排序依据 */
.score {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 14px;
  color: var(--violet-l);
  flex-shrink: 0;
}
.summary {
  color: var(--muted);
  font-size: 13px;
  line-height: 1.7;
  margin: 0 0 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.meta {
  display: flex;
  gap: 14px;
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 8px;
}

/* ---- ★ 推荐理由：这一页的重点 ---- */
.reason {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 11px;
  line-height: 1.6;
  color: var(--muted);
  border-left: 2px solid var(--line);
  padding: 2px 0 2px 10px;
  margin: 0;
  /* 按词换行：break-all 会把 "热度×0.00" 从中间劈开，很难看 */
  word-break: normal;
  overflow-wrap: anywhere;
}

/* ---- 窄屏 ---- */
@media (max-width: 640px) {
  .card {
    padding: 13px 14px;
  }
  .top {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  .meta {
    flex-wrap: wrap;
    gap: 8px;
  }
}

/* 手机端：缩略图缩小，正文多一点宽度 */
@media (max-width: 560px) {
  .thumb {
    width: 92px;
    height: 92px;
  }
  .card {
    gap: 10px;
    padding: 10px;
  }
  .reason {
    font-size: 10.5px;
  }
}
</style>