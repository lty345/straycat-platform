<script setup>
import { ref, onMounted } from 'vue'                 // 注意：没有 computed，也不需要 list
import { useRoute, useRouter } from 'vue-router'     // 读参数 + 返回
import { fetchContentDetail } from '../api/content'


const item = ref(null)        // 详情对象；null = 还没有
const loading = ref(true)
const error = ref('')

const route = useRoute()      // 地址牌：读 params
const router = useRouter()    // 遥控器：做 back()

async function load() {
  loading.value = true
  error.value = ''
  try {
    item.value = await fetchContentDetail(route.params.id)
  } catch (e) {
    error.value = e.message       // "内容不存在" / "参数错误" 都在这里
    item.value = null             // ← 别忘：失败要把旧数据清掉
  } finally {
    loading.value = false
  }
}

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
      <h1 class="title">{{ item.title }}</h1>
      <div class="meta">
        <span class="dia">◈</span>
        <span>{{ item.pub_time }}</span>
        <span v-if="item.mood" class="mood" :data-mood="item.mood">{{ item.mood }}</span>
        <span v-if="item.tags" class="tags">{{ item.tags }}</span>
      </div>
      <p class="body">{{ item.body }}</p>
    </article>

    <!-- ★ 出口放在三态之外：正常、出错、加载中都能返回 -->
    <div class="foot">
      <button class="btn" type="button" @click="router.back()">返回列表</button>
    </div>
  </section>
</template>

<style scoped>
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
</style>
