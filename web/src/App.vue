<script setup>
// App.vue 只做两件事：外壳（导航条）+ 出口（router-view）
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="shell">
    <header class="topbar">
      <div class="brand">
        <span class="dia">◈</span>
        <span class="name">初尧</span>
        <span class="sub">stray cat</span>
      </div>
      <nav class="nav">
        <RouterLink to="/">概览</RouterLink>
        <RouterLink to="/contents">内容</RouterLink>
      </nav>
    </header>

    <main class="main">
      <RouterView />
    </main>

    <footer class="foot">
      <span>MVP 开发中 · 只做了地基</span>
    </footer>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 28px;
  border-bottom: 1px solid var(--line);
}
.brand {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.dia {
  color: var(--violet);
  font-size: 13px;
}
.name {
  font-size: 17px;
  letter-spacing: 2px;
  color: var(--fg);
}
.sub {
  font-size: 11px;
  letter-spacing: 1.5px;
  color: var(--muted);
  text-transform: uppercase;
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
.nav a.router-link-active {
  color: var(--violet-l);
  border-bottom-color: var(--violet);
}
.main {
  flex: 1;
  padding: 32px 28px 48px;
  max-width: 1080px;
  width: 100%;
  margin: 0 auto;
}
.foot {
  padding: 16px 28px;
  border-top: 1px solid var(--line);
  font-size: 12px;
  color: var(--muted);
}
</style>
