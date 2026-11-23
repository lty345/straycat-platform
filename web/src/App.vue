<script setup>
// App.vue 做三件事：外壳（导航条）+ 装饰（爪印/小猫）+ 出口（router-view）
import { onMounted, onUnmounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'

import CatFace from './components/CatFace.vue'
import { auth, doLogout, restoreSession } from './auth/store'
import pawUrl from './assets/paw.svg'

const route = useRoute()
const router = useRouter()

// 页面加载时：本地有 token 就换回用户信息（刷新页面不掉登录态）
onMounted(() => {
  restoreSession()
  window.addEventListener('auth:expired', onExpired)
})

// ★ 必须解绑，否则热更新会重复监听
onUnmounted(() => {
  window.removeEventListener('auth:expired', onExpired)
})

// token 过期（client.js 发出的事件）→ 跳登录，登录后回到当前页
function onExpired() {
  if (route.name === 'login') return
  router.replace({ name: 'login', query: { redirect: route.fullPath } })
}

function onLogout() {
  doLogout()
  if (route.name !== 'home') router.push('/')
}

// 背景爪印：位置、大小、旋转、动画延迟都写在这里，模板只负责渲染
// （fixed 定位 + 低透明度，只在视觉边缘出现，不挡内容）
const paws = [
  { top: '16%', left: '4%', size: 34, rot: -18, delay: '0s' },
  { top: '34%', left: '92%', size: 26, rot: 22, delay: '1.2s' },
  { top: '62%', left: '6%', size: 22, rot: 12, delay: '2.4s' },
  { top: '78%', left: '88%', size: 32, rot: -26, delay: '0.6s' },
  { top: '48%', left: '96%', size: 18, rot: 8, delay: '1.8s' },
  { top: '88%', left: '14%', size: 20, rot: -8, delay: '3s' },
]
</script>

<template>
  <div class="shell">
    <!-- 背景爪印：会缓慢上下浮动 -->
    <div class="deco" aria-hidden="true">
      <img
        v-for="(p, i) in paws"
        :key="i"
        :src="pawUrl"
        class="paw"
        alt=""
        draggable="false"
        :style="{
          top: p.top,
          left: p.left,
          width: p.size + 'px',
          height: p.size + 'px',
          '--rot': p.rot + 'deg',
          animationDelay: p.delay,
        }"
      />
    </div>

    <header class="topbar">
      <div class="brand">
        <CatFace :size="26" class="brand-cat" />
        <span class="name">初尧</span>
        <span class="sub" title="陆游《十一月四日风雨大作·其一》：溪柴火软蛮毡暖，我与狸奴不出门">
          我与狸奴不出门
        </span>
      </div>
      <nav class="nav">
        <RouterLink to="/">概览</RouterLink>
        <RouterLink to="/contents">内容</RouterLink>
        <RouterLink to="/feed">推荐</RouterLink>
        <RouterLink to="/cats">领养</RouterLink>

        <RouterLink
          v-if="!auth.user"
          class="nav-login"
          :to="{ name: 'login', query: { redirect: route.fullPath } }"
        >登录</RouterLink>

        <span v-else class="nav-user">
          <span class="nav-name">{{ auth.user.nickname || auth.user.username }}</span>
          <button class="nav-out" type="button" @click="onLogout">退出</button>
        </span>
      </nav>
    </header>

    <main class="main">
      <RouterView />
    </main>

    <footer class="foot">
      <span>初尧 · 给流浪猫找个家</span>
    <RouterLink class="foot-link" to="/about">关于这个项目</RouterLink>
    </footer>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* ---- 背景爪印 ---- */
.deco {
  position: fixed;
  inset: 0;
  pointer-events: none;   /* 关键：不挡点击 */
  z-index: 0;
}
.paw {
  position: absolute;
  opacity: 0.14;
  transform: rotate(var(--rot));
  animation: drift 9s ease-in-out infinite;
}
@keyframes drift {
  0%,
  100% {
    transform: translateY(0) rotate(var(--rot));
  }
  50% {
    transform: translateY(-10px) rotate(var(--rot));
  }
}
@media (prefers-reduced-motion: reduce) {
  .paw {
    animation: none;
  }
}

/* ---- 顶栏 ---- */
.topbar {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 28px;
  border-bottom: 1px solid var(--border-soft);
  background: rgba(255, 253, 248, 0.72);
  backdrop-filter: blur(6px);
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-cat {
  transition: transform 0.25s;
}
.brand:hover .brand-cat {
  transform: rotate(-8deg) scale(1.06);
}
.name {
  font-size: 17px;
  letter-spacing: 2px;
  color: var(--fg);
}
.sub {
  font-size: 12px;
  letter-spacing: 1px;
  color: var(--muted);
  opacity: 0.85;
  cursor: default;
}
.nav {
  display: flex;
  gap: 22px;
}
.nav a {
  color: var(--muted);
  font-size: 14px;
  text-decoration: none;
  padding-bottom: 3px;
  border-bottom: 1px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}
.nav a:hover {
  color: var(--fg);
}
/* 窄屏：导航会挤爆（390px 宽时"推荐/领养"被裁掉） */
@media (max-width: 640px) {
  .topbar {
    padding: 12px 16px;
    gap: 10px;
    flex-wrap: wrap;
  }
  .sub {
    display: none;
  }
  .nav {
    gap: 14px;
  }
  .nav a {
    font-size: 13px;
  }
}

.nav a.router-link-active {
  color: var(--violet-l);
  border-bottom-color: var(--violet);
}

/* ---- 内容区 ---- */
.main {
  position: relative;
  z-index: 1;
  flex: 1;
  padding: 36px 28px 56px;
  max-width: 1080px;
  width: 100%;
  margin: 0 auto;
}
.foot {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 16px 28px;
  border-top: 1px solid var(--border-soft);
  font-size: 12px;
  color: var(--muted);
}

.foot-link {
  color: var(--muted);
  text-decoration: none;
  font-size: 12px;
  opacity: 0.8;
}
.foot-link:hover {
  color: var(--violet-l);
}

/* ---- 登录态 ---- */
.nav-login {
  padding: 3px 14px;
  border: 1px solid var(--line);
  border-radius: 999px;
  color: var(--violet-l);
}
.nav-login:hover {
  border-color: var(--violet);
  background: var(--bg-soft);
}
.nav-user {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.nav-name {
  color: var(--fg);
  font-size: 13.5px;
}
.nav-out {
  border: none;
  background: none;
  color: var(--muted);
  font-size: 12px;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.nav-out:hover {
  color: var(--bad);
}
</style>
