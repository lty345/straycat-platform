<script setup>
import { postEvent } from '../api/event'
import { computed, ref, onMounted,onUnmounted } from 'vue'                 // 注意：没有 computed，也不需要 list
import { useRoute, useRouter } from 'vue-router'     // 读参数 + 返回
import { fetchContentDetail } from '../api/content'
import { fetchUsers } from '../api/user'
import { fetchContents } from '../api/content'
import { fullTime } from '../utils/time'

const contentId = ref(null)
const item = ref(null)        // 详情对象；null = 还没有
const loading = ref(true)
const error = ref('')
const enterAt = ref(0)     // 进入时间戳；0 = 还没开始计时
const userId = ref(null)   // 当前演示用户
const related = ref([])    // 同情绪的其他内容

// 按 350 字/分钟估算阅读时长（比显示字数更贴近读者直觉）
const readMinutes = computed(() => {
  const n = (item.value?.body || '').length
  return n ? Math.max(1, Math.round(n / 350)) : 0
})
const route = useRoute()      // 地址牌：读 params
const router = useRouter()    // 遥控器：做 back()

async function load() {
  loading.value = true
  error.value = ''
  try {
    contentId.value = Number(route.params.id)
    item.value = await fetchContentDetail(route.params.id)
    enterAt.value = Date.now()      // 内容加载成功才开始计时
    const users = await fetchUsers()
    userId.value = users.length ? users[0].id : null

    // 相关阅读：同情绪的另外几篇（拿不到就留空，不影响正文）
    try {
      const same = await fetchContents({ mood: item.value.mood || '', pageSize: 6 })
      related.value = (same.list ?? [])
        .filter((x) => x.id !== contentId.value)
        .slice(0, 3)
    } catch {
      related.value = []
    }
  } catch (e) {
    error.value = e.message       // "内容不存在" / "参数错误" 都在这里
    item.value = null             // ← 别忘：失败要把旧数据清掉
  } finally {
    loading.value = false
  }
}

let reported = false          // 防止重复上报

async function reportView() {
  // 空1：什么情况下不发？
  if (reported==true||!item.value||!userId.value||!enterAt.value) return
  reported = true

  try {
    await postEvent({
      user_id: userId.value,                      // 空2
      target_type: 'content',
      target_id: contentId.value,
      event: 'view',
      duration_ms: Date.now()-enterAt.value                 // 空3：停留了多久
    })
  } catch (e) {
                                     // 空4：失败了怎么办
  }
}

onUnmounted(reportView)       // 离开页面时上报
onMounted(load)
</script>

<template>
  <section>
    <div class="page-head">
      <button class="btn" type="button" @click="router.back()">← 返回</button>
    </div>

    <!-- ① 出错 -->
    <div v-if="error" class="state state-bad">
      <div class="state-title">没拿到这条内容</div>
      <p class="state-text">{{ error }}</p>
      <p class="state-hint">可能是内容已被删除，或地址里的 id 不存在</p>
    </div>

    <!-- ② 加载中 -->
    <div v-else-if="loading" class="state">
      <div class="state-title">载入中…</div>
    </div>

    <!-- ③ 有数据 -->
    <article v-else class="article">
      <img v-if="item.cover_url" :src="item.cover_url" :alt="item.title" class="hero" />
      <h1 class="title">{{ item.title }}</h1>
      <div class="meta">
        <span class="dia">◈</span>
        <span>{{ fullTime(item.pub_time) }}</span>
        <span v-if="item.mood" class="mood" :data-mood="item.mood">{{ item.mood }}</span>
        <span v-if="readMinutes" class="reading">{{ readMinutes }} 分钟读完</span>
        <span v-if="item.tags" class="tags">{{ item.tags }}</span>
      </div>
      <p class="body">{{ item.body }}</p>
    </article>

    <!-- 相关阅读：给读者一条继续往下走的路径 -->
    <section v-if="related.length" class="related">
      <h2 class="related-title">你可能也喜欢</h2>
      <div class="related-list">
        <RouterLink
          v-for="r in related"
          :key="r.id"
          class="rel-card"
          :to="{ name: 'content-detail', params: { id: r.id } }"
        >
          <div class="rel-cover">
            <img v-if="r.cover_url" :src="r.cover_url" :alt="r.title" loading="lazy" />
          </div>
          <span class="rel-title">{{ r.title }}</span>
        </RouterLink>
      </div>
    </section>

    <!-- ★ 出口放在三态之外：正常、出错、加载中都能返回 -->
    <div class="foot">
      <button class="btn" type="button" @click="router.back()">返回列表</button>
    </div>
  </section>
</template>

<style scoped>
.hero {
  width: 100%;
  max-height: 420px;   /* 宽屏下 16:9 会到 560px，太高了 */
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 4px;
  margin-bottom: 24px;
}
/* 颜色只用变量：var(--panel) var(--line) var(--fg) var(--muted) var(--violet) var(--violet-l) */
.page-head {
  margin-bottom: 18px;
}

.btn {
  background: transparent;
  border: 1px solid var(--line);
  color: var(--muted);
  font-size: 13px;
  padding: 5px 14px;
  border-radius: 2px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}
.btn:hover {
  color: var(--violet-l);
  border-color: var(--violet);
}

/* ---- 状态块：和列表页同一套长相 ---- */
.state {
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 4px;
  padding: 28px 20px;
  text-align: center;
}
.state-bad {
  border-color: var(--violet);
}
.state-title {
  font-size: 14px;
  margin-bottom: 8px;
}
.state-text {
  color: var(--muted);
  font-size: 13px;
  margin: 0 0 8px;
}
.state-hint {
  color: var(--muted);
  font-size: 12px;
  margin: 0;
}

/* ---- 正文 ---- */
.article {
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 4px;
  padding: 26px 28px;
}
.title {
  font-size: 21px;
  font-weight: 600;
  letter-spacing: 0.5px;
  line-height: 1.4;
  margin: 0 0 12px;
}
.meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--muted);
  padding-bottom: 16px;
  margin-bottom: 18px;
  border-bottom: 1px solid var(--line);
}
.dia {
  color: var(--violet);
  font-size: 10px;
}
.mood {
  border: 1px solid var(--line);
  border-radius: 2px;
  padding: 1px 7px;
}
.mood[data-mood='治愈'] {
  color: var(--mood-cure);
  border-color: var(--mood-cure);
}
.mood[data-mood='科普'] {
  color: var(--mood-sci);
  border-color: var(--mood-sci);
}
.mood[data-mood='揪心'] {
  color: var(--mood-hurt);
  border-color: var(--mood-hurt);
}
.mood[data-mood='欢乐'] {
  color: var(--mood-fun);
  border-color: var(--mood-fun);
}
.tags {
  color: var(--violet-l);
  opacity: 0.8;
}

/* ★ pre-wrap：正文里的换行和连续空格都保留，否则段落会挤成一坨 */
.body {
  color: var(--fg);
  font-size: 14px;
  line-height: 1.9;
  white-space: pre-wrap;
  margin: 0;
}

.foot {
  margin-top: 20px;
}

/* ---- 轻量过渡 ---- */
@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
.article,
.state {
  animation: fade-up 0.25s ease-out both;
}

/* ---- 窄屏（手机演示）---- */
@media (max-width: 640px) {
  .article {
    padding: 18px 16px;
  }
  .title {
    font-size: 18px;
  }
  .meta {
    flex-wrap: wrap;
    gap: 8px;
  }
  .body {
    font-size: 13px;
    line-height: 1.8;
  }
}

/* ===== UI 升级：阅读体验 ===== */
/* 一行 60~75 个字符最舒服；原来整屏 1000px 宽，一行 80+ 字，读起来累 */
.article {
  max-width: 780px;
  margin: 0 auto;
  padding: 30px 34px 34px;
}
.hero {
  max-height: 340px;
  width: 100%;
  object-fit: cover;
}
.title {
  font-size: 26px;
  line-height: 1.45;
  letter-spacing: 0.3px;
  margin-bottom: 14px;
}
.body {
  white-space: pre-wrap;
  font-size: 15.5px;
  line-height: 1.95;
  letter-spacing: 0.2px;
  color: #3b332c;
  margin: 0;
}

/* 相关阅读 */
.related {
  max-width: 780px;
  margin: 26px auto 0;
}
.related-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--muted);
  letter-spacing: 1px;
  margin: 0 0 12px;
}
.related-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(200px, 100%), 1fr));
  gap: 12px;
}
.rel-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-decoration: none;
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  background: var(--panel);
  overflow: hidden;
  transition: border-color 0.18s, transform 0.18s, box-shadow 0.18s;
}
.rel-card:hover {
  border-color: var(--violet);
  transform: translateY(-2px);
  box-shadow: var(--card-shadow-hover);
}
.rel-cover { aspect-ratio: 16 / 10; background: var(--bg-soft); }
.rel-cover img { width: 100%; height: 100%; object-fit: cover; display: block; }
.rel-title {
  font-size: 13px;
  color: var(--fg);
  line-height: 1.5;
  padding: 0 12px 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.reading {
  font-size: 12px;
  color: var(--muted);
  opacity: 0.85;
}
</style>
