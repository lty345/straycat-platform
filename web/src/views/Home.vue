<script setup>
// =============================================================================
// views/Home.vue —— 概览页
// =============================================================================
// 这一页只做一件事：证明「前端能通到后端」。
// 它调 /health（后端已经有这个接口），显示后端状态。
//
// ★ 这是垂直切片的第一片，也是最便宜的一次全链路验证。
// =============================================================================
import { onMounted, ref } from 'vue'
import { fetchHealth } from '../api/system'

const status = ref('检测中…')
const detail = ref('')
const failed = ref(false)

onMounted(async () => {
  try {
    const result = await fetchHealth() // 拦截器已剥壳，直接是 result
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
    <h1 class="h1">概览</h1>
    <p class="lead">
      给流浪猫做的内容社区。技术重点是个性化推荐，不是又一套 CRUD。
    </p>

    <div class="card" :class="{ bad: failed }">
      <div class="card-head">
        <span class="dia">◈</span>
        <span>后端连通性</span>
        <span class="badge" :class="failed ? 'b-bad' : 'b-ok'">{{ status }}</span>
      </div>
      <pre class="mono">{{ detail || '—' }}</pre>
    </div>

    <div class="card">
      <div class="card-head">
        <span class="dia">◈</span>
        <span>下一步（垂直切片）</span>
      </div>
      <ol class="steps">
        <li>
          <b>后端</b>：建 <code>content</code> 表 → 写
          <code>GET /api/v1/contents</code>（分页）→ 在 <code>/docs</code> 里点通
        </li>
        <li>
          <b>前端</b>：把 <code>api/content.js</code> 的 <code>fetchContents</code>
          接到这个页面的「内容」列表
        </li>
        <li><b>验证</b>：页面能翻页、能看到 20 条内容</li>
      </ol>
    </div>
  </section>
</template>

<style scoped>
.h1 {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 1px;
  margin: 0 0 8px;
}
.lead {
  color: var(--muted);
  font-size: 14px;
  margin: 0 0 28px;
  line-height: 1.7;
}
.card {
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 18px 20px;
  margin-bottom: 18px;
  background: var(--panel);
}
.card.bad {
  border-color: #5a2b3a;
}
.card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  margin-bottom: 12px;
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
  border: 1px solid var(--line);
  color: var(--muted);
}
.b-ok {
  color: #7fae8f;
  border-color: #2f4a38;
}
.b-bad {
  color: #c98a96;
  border-color: #5a2b3a;
}
.mono {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 12px;
  color: var(--muted);
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
.steps {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  line-height: 2;
  color: var(--muted);
}
.steps code {
  background: #1d1926;
  color: var(--violet-l);
  padding: 1px 6px;
  border-radius: 2px;
  font-size: 12px;
}
</style>
