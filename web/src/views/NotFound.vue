<script setup>
import { RouterLink } from 'vue-router'
import CatFace from '../components/CatFace.vue'
</script>

<template>
  <div class="nf">
    <CatFace :size="64" class="nf-cat" />
    <p class="t">这个页面不存在</p>
    <RouterLink class="back" to="/">回概览</RouterLink>
  </div>
</template>

<style scoped>
.nf {
  text-align: center;
  padding: 80px 20px;
}
.nf-cat {
  margin: 0 auto 16px;
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
