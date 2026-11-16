<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchFeed } from '../api/feed'
import { fetchUsers } from '../api/user'
import CatFace from '../components/CatFace.vue'

// ★ 用户列表从接口拿，不写死 id：
//   种子脚本重跑会让 id 变（4/5/6 → 7/8/9），写死就会"用户不存在"。
const users = ref([])
const userId = ref(null)

const data = ref(null)      // 接口返回的整个 result
const loading = ref(false)
const error = ref('')

const items   = computed(() => data.value?.list ?? [])                 // data 里的 list
const coldStart = computed(() => data.value?.cold_start ?? false)      // ★ 后端是下划线：cold_start
const preferredMood = computed(() => data.value?.preferred_mood ?? null)  // ★ 后端是下划线：preferred_mood

async function load() {
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

function switchUser(id) {
  userId.value = id
  load()          // 换人立刻重拉
}

onMounted(async () => {
  loading.value = true   // 先进加载态，避免"共 0 只"闪一下
  try {
    users.value = await fetchUsers()
    if (users.value.length === 0) {
      error.value = '还没有用户，先跑 scripts/seed_users_events.py'
      return
    }
    userId.value = users.value[0].id       // 默认选第一个
    await load()
  } catch (e) {
    error.value = e.message
  }
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
        {{ u.nickname }}<small>{{ u.interest_tags || '冷启动' }}</small>
      </button>
    </div>

    <!-- 冷启动提示：只有走兜底时才出现 -->
    <p v-if="coldStart" class="cold">
      这个用户没有兴趣标签也没有行为记录，按「近 7 天热门」推荐
    </p>

    <!-- 四态 -->
    <p v-if="error">出错了：{{ error }}</p>
    <p v-else-if="loading">加载中…</p>
    <div v-else-if="items.length === 0" class="empty">
      <CatFace :size="52" />
      <p>还没有可推荐的内容</p>
    </div>
    <ul v-else class="list">
      <li v-for="it in items" :key="it.id" class="card">
        <img v-if="it.cover_url" class="thumb" :src="it.cover_url" alt="" loading="lazy" />
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
  border: 1px solid var(--border-soft);
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
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 56px 0;
  color: var(--muted);
  font-size: 13px;
}
.empty p {
  margin: 0;
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
  /* 宽屏两列：单列时右侧一大片空白，看着"不饱满" */
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
  gap: 12px;
}
/* 左缩略图 + 右内容 */
.card {
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
  font-size: 16px;
  font-weight: 500;
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
  /* 最多两行，超出省略——列表里不需要整段摘要 */
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
  word-break: break-all;
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
</style>