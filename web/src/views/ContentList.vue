<script setup>
// =============================================================================
// views/ContentList.vue —— 内容列表（垂直切片的靶子）
// =============================================================================
// 【这个页面现在是什么状态】
//   前端部分已经写好了：加载中 / 出错 / 空列表 / 有数据 四种状态都处理了，
//   分页也接好了。它唯一缺的是——**后端那个接口**。
//
//   所以你打开它会看到「接口不存在（404）」。这不是 bug，
//   这是「前端已经在等后端了」。
//
// 【你要补的后端】
//   GET /api/v1/contents?page=1&page_size=10
//   返回：{ list: [...], total: N, page: 1, page_size: 10 }
//   （和 doctors/hospitals 的分页结构一模一样，照着抄）
// =============================================================================
import { computed, onMounted, ref } from 'vue'
import { fetchContents } from '../api/content'

const PAGE_SIZE = 10

const list = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const error = ref('')

const totalPages = computed(() =>
  total.value === 0 ? 1 : Math.ceil(total.value / PAGE_SIZE)
)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchContents({ page: page.value, pageSize: PAGE_SIZE })
    // 后端返回的是 Page 结构，字段名照抄后端（list / total / page / page_size）
    list.value = data.list ?? []
    total.value = data.total ?? 0
  } catch (e) {
    error.value = e.message
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function prev() {
  if (page.value > 1) {
    page.value -= 1
    load()
  }
}
function next() {
  if (page.value < totalPages.value) {
    page.value += 1
    load()
  }
}

onMounted(load)
</script>

<template>
  <section>
    <div class="head">
      <h1 class="h1">内容</h1>
      <button class="btn" :disabled="loading" @click="load">
        {{ loading ? '加载中…' : '刷新' }}
      </button>
    </div>

    <!-- 状态一：出错 -->
    <div v-if="error" class="state bad">
      <div class="dia">◈</div>
      <p class="state-title">{{ error }}</p>
      <p class="state-tip">
        如果提示「接口不存在」，说明后端还没写
        <code>GET /api/v1/contents</code> —— 这正是你下一步要做的。
      </p>
    </div>

    <!-- 状态二：加载中 -->
    <div v-else-if="loading" class="state">
      <p class="state-title">加载中…</p>
    </div>

    <!-- 状态三：没数据 -->
    <div v-else-if="list.length === 0" class="state">
      <div class="dia">◈</div>
      <p class="state-title">还没有内容</p>
      <p class="state-tip">接口通了，但表里没数据 —— 该造几条种子数据了。</p>
    </div>

    <!-- 状态四：有数据 -->
    <template v-else>
      <ul class="list">
        <li v-for="item in list" :key="item.id" class="item">
          <span class="tag">{{ item.mood || '内容' }}</span>
          <h3 class="title">{{ item.title }}</h3>
          <p class="summary">{{ item.summary }}</p>
          <p class="meta">{{ item.pub_time }}</p>
        </li>
      </ul>

      <div class="pager">
        <button class="btn" :disabled="page <= 1" @click="prev">上一页</button>
        <span class="pageno">{{ page }} / {{ totalPages }}　共 {{ total }} 条</span>
        <button class="btn" :disabled="page >= totalPages" @click="next">下一页</button>
      </div>
    </template>
  </section>
</template>

<style scoped>
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
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
  padding: 6px 16px;
  border-radius: 3px;
  cursor: pointer;
  transition: 0.15s;
}
.btn:hover:not(:disabled) {
  border-color: var(--violet);
  color: var(--violet-l);
}
.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.state {
  border: 1px dashed var(--line);
  border-radius: 4px;
  padding: 36px 24px;
  text-align: center;
}
.state.bad {
  border-style: solid;
  border-color: #5a2b3a;
}
.dia {
  color: var(--violet);
  font-size: 16px;
  margin-bottom: 10px;
}
.state-title {
  font-size: 14px;
  color: var(--fg);
  margin: 0 0 8px;
}
.state-tip {
  font-size: 12px;
  color: var(--muted);
  margin: 0;
  line-height: 1.8;
}
.state-tip code {
  background: #1d1926;
  color: var(--violet-l);
  padding: 1px 6px;
  border-radius: 2px;
}
.list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.item {
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 16px 18px;
  margin-bottom: 12px;
  background: var(--panel);
}
.tag {
  font-size: 11px;
  color: var(--violet-l);
  border: 1px solid var(--line);
  padding: 1px 8px;
  border-radius: 2px;
}
.title {
  font-size: 15px;
  font-weight: 600;
  margin: 10px 0 6px;
  letter-spacing: 0.5px;
}
.summary {
  font-size: 13px;
  color: var(--muted);
  margin: 0 0 8px;
  line-height: 1.7;
}
.meta {
  font-size: 11px;
  color: #5d5668;
  margin: 0;
}
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  margin-top: 22px;
}
.pageno {
  font-size: 12px;
  color: var(--muted);
}
</style>
