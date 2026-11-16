<script setup>
// =============================================================================
// components/CatFace.vue —— 小猫图案
// =============================================================================
// 图形来自 Twemoji（🐱 U+1F431），CC-BY 4.0 许可，见 README「素材来源」。
// 为什么用现成的而不是自己画：手绘的 SVG 在小尺寸下五官挤在一起，
// 现成的 emoji 图形在 16~64px 都经得住看。
//
// 动画：整只猫轻微上下浮 + 摆头，3.2 秒一个来回。
//      （图片没法做"眨眼"，所以换成整体的小晃动，观感更自然）
// =============================================================================
import catUrl from '../assets/cat-face.svg'

defineProps({
  size: { type: Number, default: 24 },
})
</script>

<template>
  <img
    :src="catUrl"
    :width="size"
    :height="size"
    class="cat-face"
    alt=""
    aria-hidden="true"
    draggable="false"
  />
</template>

<style scoped>
.cat-face {
  display: block;
  user-select: none;
  transform-origin: 50% 92%;
  animation: bob 3.2s ease-in-out infinite;
}

@keyframes bob {
  0%,
  100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-2px) rotate(-4deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .cat-face {
    animation: none;
  }
}
</style>
