<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="nf">
    <div class="dia">◈</div>
    <p class="t">这个页面不存在</p>
    <RouterLink class="back" to="/">回概览</RouterLink>
  </div>
</template>

<style scoped>
.nf {
  text-align: center;
  padding: 80px 20px;
}
.dia {
  color: var(--violet);
  font-size: 20px;
  margin-bottom: 14px;
}
.t {
  color: var(--muted);
  font-size: 14px;
  margin-bottom: 20px;
}
.back {
  color: var(--violet-l);
  font-size: 13px;
}
</style>
