<script setup>
// =============================================================================
// views/ContentList.vue —— 内容列表【待你实现】
// =============================================================================
// 【这个页面要覆盖的四种状态】（少一种，线上就会出白屏或转圈不停）
//   ① 出错    —— 显示 e.message + 一句引导
//   ② 加载中  —— loading 时显示提示，按钮禁用
//   ③ 空列表  —— 接口通了但没数据
//   ④ 有数据  —— 列表 + 分页条
//
// 【参考实现】：git 里有我这版（commit 434a638）
//   git show 434a638:web/src/views/ContentList.vue
//   先自己写，卡住再看；看完再重写一遍，别直接抄回来。
// =============================================================================

import { ref, computed, onMounted } from 'vue'
import { fetchContents } from '../api/content'

const list = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const PAGE_SIZE = 10
const error = ref('')


const totalPages = computed(() => {
    const n = Math.ceil(total.value / PAGE_SIZE)
    return n === 0 ? 1 : n
})

async function load() {
    loading.value = true
    error.value = ''
    try{
        const data = await fetchContents({ page: page.value, pageSize: PAGE_SIZE })
        list.value = data.list ?? []
        total.value = data.total ?? 0
    } catch (e) {
        error.value = e.message
        total.value=0
        list.value = []
    } finally {
        loading.value = false
    }
}

function prev() {
    if (page.value > 1) {
        page.value--
        load()
    }
}

function next() {
    if (page.value < totalPages.value) {
        page.value++
        load()
    }
}

import { useRouter } from 'vue-router'
const router = useRouter()

function openDetail(item) {
  router.push({ name: 'content-detail', params: { id: item.id } })
}

onMounted(() => {
    load()
})



</script>

<template>
  <section>
    <div class="page-head">
      <h1 class="h1">内容</h1>
      <button class="btn" type="button" :disabled="loading" @click="load">
        {{ loading ? '加载中…' : '刷新' }}
      </button>
    </div>

    <!-- ① 出错 -->
    <div v-if="error" class="state state-bad">
      <div class="state-title">没拿到内容</div>
      <p class="state-text">{{ error }}</p>
      <p class="state-hint">后端起了吗？<code>uv run fastapi dev app.py</code></p>
    </div>

    <!-- ② 加载中 -->
    <div v-else-if="loading" class="state">
      <div class="state-title">载入中…</div>
    </div>

    <!-- ③ 空列表 -->
    <div v-else-if="list.length === 0" class="state">
      <div class="state-title">还没有内容</div>
      <p class="state-hint">换个筛选条件试试，或先跑种子脚本 <code>scripts/seed_content.py</code></p>
    </div>

    <!-- ④ 有数据 -->
    <template v-else>
      <ul class="list">
        <li v-for="item in list" :key="item.id" class="card" @click="openDetail(item)">
          <div class="card-top">
            <span class="title">{{ item.title }}</span>
            <span v-if="item.mood" class="mood" :data-mood="item.mood">{{ item.mood }}</span>
          </div>
          <p v-if="item.summary" class="summary">{{ item.summary }}</p>
          <div class="meta">
            <span class="dia">◈</span>
            <span>{{ item.pub_time }}</span>
            <span v-if="item.tags" class="tags">{{ item.tags }}</span>
          </div>
        </li>
      </ul>

      <div class="pager">
        <button class="btn" @click="prev" :disabled="page <= 1">上一页</button>
        <span class="pager-info">第 {{ page }} / {{ totalPages }} 页　共 {{ total }} 条</span>
        <button class="btn" @click="next" :disabled="page >= totalPages">下一页</button>
      </div>
    </template>

  </section>
</template>

<style scoped>
/* 颜色只用 src/style.css 里的变量，不写死 #hex */
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.h1 {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 1px;
  margin: 0;
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
.btn:hover:not(:disabled) {
  color: var(--violet-l);
  border-color: var(--violet);
}
.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* ---- 状态块 ---- */
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
.state-hint code {
  background: #1d1926;
  color: var(--violet-l);
  padding: 1px 6px;
  border-radius: 2px;
}

/* ---- 列表 ---- */
.list {
  list-style: none;
  margin: 0 0 20px;
  padding: 0;
}
.card {
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 4px;
  padding: 16px 18px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: border-color 0.15s;
}
.card:hover {
  border-color: var(--violet);
}
.card-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.title {
  font-size: 15px;
  color: var(--fg);
}
.mood {
  font-size: 11px;
  color: var(--muted);
  border: 1px solid var(--line);
  border-radius: 2px;
  padding: 1px 7px;
}
/* 情绪分色：用 data-mood 属性选择器，颜色全部来自 style.css 的变量 */
.mood[data-mood='治愈'] {
  color: var(--mood-cure);
  border-color: var(--mood-cure);
  opacity: 0.85;
}
.mood[data-mood='科普'] {
  color: var(--mood-sci);
  border-color: var(--mood-sci);
  opacity: 0.85;
}
.mood[data-mood='揪心'] {
  color: var(--mood-hurt);
  border-color: var(--mood-hurt);
  opacity: 0.85;
}
.mood[data-mood='欢乐'] {
  color: var(--mood-fun);
  border-color: var(--mood-fun);
  opacity: 0.85;
}
.summary {
  color: var(--muted);
  font-size: 13px;
  line-height: 1.7;
  margin: 0 0 10px;
}
.meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--muted);
}
.dia {
  color: var(--violet);
  font-size: 10px;
}
.tags {
  color: var(--violet-l);
  opacity: 0.75;
}

/* ---- 分页 ---- */
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
}
.pager-info {
  color: var(--muted);
  font-size: 13px;
}

/* ---- 轻量过渡：列表淡入 + 卡片 hover 微抬 ----
   ★ 只做 CSS，不引入 <transition> 组件——数据只有 20 条，
     上层过渡动画属于"演示加分、工程无用"的那一类 */
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
.card {
  animation: fade-up 0.25s ease-out both;
}
.card:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
}
.card,
.card:hover {
  transition: border-color 0.15s, transform 0.15s, box-shadow 0.15s;
}

/* ---- 窄屏（手机演示）：一档就够了 ---- */
@media (max-width: 640px) {
  .page-head {
    margin-bottom: 14px;
  }
  .card {
    padding: 14px;
    margin-bottom: 10px;
  }
  .summary {
    font-size: 12px;
  }
  .pager {
    gap: 10px;
    flex-wrap: wrap;
  }
  .pager-info {
    order: 3;
    width: 100%;
    text-align: center;
  }
}
</style>
