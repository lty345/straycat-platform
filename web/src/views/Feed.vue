<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchFeed } from '../api/feed'

// 演示用的三个用户（id 来自 scripts/seed_users_events.py，重跑脚本后 id 会变）
const USERS = [
  { id: 4, name: '小橘', desc: '橘猫 / 日常' },
  { id: 5, name: '阿救', desc: '救助 / 科普' },
  { id: 6, name: '路过的新人', desc: '冷启动' },
]

const userId = ref(4)
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

onMounted(load)
</script>

<template>
  <section>
    <h1>推荐</h1>

    <!-- 用户切换：点一下换一个人，看顺序怎么变 -->
    <div class="users">
      <button v-for="u in USERS" :key="u.id"
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
      <li v-for="it in items" :key="it.id" class="card">
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
}
.card {
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 4px;
  padding: 16px 18px;
  margin-bottom: 12px;
  transition: border-color 0.15s;
}
.card:hover {
  border-color: var(--violet);
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
  margin: 0 0 10px;
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