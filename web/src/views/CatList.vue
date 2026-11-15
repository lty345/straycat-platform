<script setup>
// =============================================================================
// views/CatList.vue —— 领养列表
// =============================================================================
// 【这一页最值得学的地方：点完按钮之后怎么让界面说真话】
//   天真做法：点了成功 → 本地把 cat.status 改成"审核中"
//   问题：你点之前，猫可能已经被别人抢了。本地改状态 = 界面撒谎。
//   正确做法：不管成功还是失败，都重新拉一次列表，用后端返回的真相渲染。
//             （数据量小，多一次请求换来"界面不说谎"，非常划算）
// =============================================================================
import { ref, onMounted } from 'vue'
import { fetchCats, adoptCat, approveCat, rejectCat } from '../api/cat'
import { fetchUsers } from '../api/user'

// 当前操作人：从用户列表里取第一个（不写死 id，重跑种子脚本也不会错）
const currentUserId = ref(null)

const list = ref([])
const total = ref(0)
const status = ref('待领养')     // '' = 全部
const loading = ref(false)
const error = ref('')
const adoptingId = ref(null)     // 正在申请的那只猫 id（用于按钮 loading）
const notice = ref('')           // 顶部提示条（成功 / 失败文案）

const FILTERS = [
  { value: '待领养', label: '待领养' },
  { value: '审核中', label: '审核中' },
  { value: '已领养', label: '已领养' },
  { value: '', label: '全部' },
]

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchCats({ status: status.value, pageSize: 20 })
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

async function onAdopt(cat) {
  adoptingId.value = cat.id
  notice.value = ''
  try {
    await adoptCat(cat.id, currentUserId.value)
    notice.value = `已申请领养「${cat.name}」，等待审核`
  } catch (e) {
    // 拦截器已经把后端的 message 剥好了：这里就是"这只猫已被他人申请"
    notice.value = e.message
  } finally {
    adoptingId.value = null
    // ★ 不管成败都重新拉：成功要显示"审核中"，失败要知道现在到底是谁抢到了
    await load()
  }
}

function pickStatus(s) {
  status.value = s
  load()
}

// -----------------------------------------------------------------------------
// 审核：状态机的最后一步（真实系统要管理员权限，这里做成演示按钮）
// -----------------------------------------------------------------------------
async function review(cat, action) {
  adoptingId.value = cat.id
  notice.value = ''
  try {
    if (action === 'approve') {
      await approveCat(cat.id)
      notice.value = `「${cat.name}」审核通过，已是已领养`
    } else {
      await rejectCat(cat.id)
      notice.value = `已驳回「${cat.name}」，它重新开放申请`
    }
  } catch (e) {
    notice.value = e.message      // 20003：该申请不存在或已被处理
  } finally {
    adoptingId.value = null
    await load()                  // 和申请一样：成败都重新拉，界面不说谎
  }
}

onMounted(async () => {
  // 先拿"当前操作人"，再拉列表（不写死 id）
  try {
    const users = await fetchUsers()
    currentUserId.value = users.length ? users[0].id : null
  } catch (e) {
    notice.value = e.message
  }
  await load()
})
</script>

<template>
  <section>
    <div class="head">
      <h1>领养</h1>
      <span class="count">共 {{ total }} 只</span>
    </div>

    <div class="chips">
      <button
        v-for="f in FILTERS"
        :key="f.value"
        class="chip"
        :class="{ on: status === f.value }"
        @click="pickStatus(f.value)"
      >
        {{ f.label }}
      </button>
    </div>

    <p v-if="notice" class="notice">{{ notice }}</p>

    <p v-if="error">出错了：{{ error }}</p>
    <p v-else-if="loading">加载中…</p>
    <p v-else-if="list.length === 0">这个条件下还没有猫</p>
    <ul v-else class="list">
      <li v-for="cat in list" :key="cat.id" class="card">
        <!-- 左图右文：图片用 object-fit: cover，任何尺寸都不会变形 -->
        <div class="cover-wrap">
          <img v-if="cat.cover_url" class="cover" :src="cat.cover_url" :alt="cat.name" loading="lazy" />
          <div class="badge" :data-status="cat.status">{{ cat.status }}</div>
        </div>

        <div class="body">
          <div class="top">
            <span class="name">{{ cat.name }}</span>
            <span class="breed">{{ cat.breed }}</span>
          </div>
          <p class="meta">{{ cat.age_month }} 个月 · {{ cat.city }}</p>
          <p class="health">{{ cat.health }}</p>

          <div class="actions">
            <button
              v-if="cat.status === '待领养'"
              class="btn"
              :disabled="adoptingId === cat.id"
              @click="onAdopt(cat)"
            >
              {{ adoptingId === cat.id ? '申请中…' : '申请领养' }}
            </button>

            <!-- 审核中：管理员视角的两个出口（演示用，真实系统这里必须鉴权） -->
            <template v-else-if="cat.status === '审核中'">
              <span class="state-text">申请人 #{{ cat.applicant_id }} 等待审核</span>
              <button class="btn" :disabled="adoptingId === cat.id" @click="review(cat, 'approve')">
                通过
              </button>
              <button class="btn btn-ghost" :disabled="adoptingId === cat.id" @click="review(cat, 'reject')">
                驳回
              </button>
            </template>

            <span v-else class="state-text">
              已有家啦<template v-if="cat.applicant_id">（领养人 #{{ cat.applicant_id }}）</template>
            </span>
          </div>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 18px;
}
h1 {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 1px;
  margin: 0;
}
.count {
  color: var(--muted);
  font-size: 12px;
}

.chips {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.chip {
  background: transparent;
  border: 1px solid var(--line);
  color: var(--muted);
  font-size: 13px;
  padding: 5px 14px;
  border-radius: 2px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}
.chip:hover {
  color: var(--fg);
}
.chip.on {
  color: var(--violet-l);
  border-color: var(--violet);
}

.notice {
  border-left: 2px solid var(--violet);
  background: var(--panel);
  color: var(--violet-l);
  font-size: 12px;
  padding: 8px 12px;
  margin: 0 0 14px;
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
  /* 宽屏两列、窄屏一列：比整行拉满好看，也少留白 */
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(430px, 1fr));
  gap: 14px;
}

/* 卡片：左边图片，右边信息 */
.card {
  display: flex;
  gap: 16px;
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 6px;
  padding: 12px;
  transition: border-color 0.18s, transform 0.18s;
}
.card:hover {
  border-color: var(--violet);
  transform: translateY(-1px);
}

.cover-wrap {
  position: relative;
  flex-shrink: 0;
  width: 150px;
  height: 116px;
  border-radius: 4px;
  overflow: hidden;
  background: #0d0b14;
}
.cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
/* 状态徽章压在图片右下角 */
.cover-wrap .badge {
  position: absolute;
  right: 8px;
  bottom: 8px;
  background: rgba(10, 8, 16, 0.82);
  backdrop-filter: blur(2px);
}

.body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.top {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 6px;
}
.name {
  font-size: 17px;
  font-weight: 500;
  color: var(--fg);
}
.breed {
  font-size: 12px;
  color: var(--muted);
}
.badge {
  font-size: 11px;
  color: var(--muted);
  border: 1px solid var(--line);
  border-radius: 2px;
  padding: 1px 7px;
}
.badge[data-status='待领养'] {
  color: var(--mood-cure);
  border-color: var(--mood-cure);
}
.badge[data-status='审核中'] {
  color: var(--mood-fun);
  border-color: var(--mood-fun);
}

.actions {
  margin-top: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.meta {
  color: var(--muted);
  font-size: 13px;
  margin: 0 0 4px;
}
.health {
  color: var(--muted);
  font-size: 12px;
  margin: 0 0 12px;
}
.btn {
  background: transparent;
  border: 1px solid var(--violet);
  color: var(--violet-l);
  font-size: 13px;
  padding: 5px 16px;
  border-radius: 2px;
  cursor: pointer;
  transition: opacity 0.15s;
}
.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.state-text {
  color: var(--muted);
  font-size: 12px;
}

/* 审核中那一排：说明 + 两个按钮 */
.review {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.review .state-text {
  margin-right: 4px;
}
.btn-ghost {
  border-color: var(--line);
  color: var(--muted);
}
.btn-ghost:hover {
  color: var(--fg);
}
</style>
