<script setup>
// =============================================================================
// components/CatFace.vue —— 会眨眼的小猫（纯 SVG + CSS 动画，零依赖）
// =============================================================================
// 为什么用 SVG 而不是图片：
//   ① 颜色直接用 CSS 变量，换主题不用重做图
//   ② 动画可以只作用于局部（这里只让"眼睛"眨），图片做不到
//   ③ 体积几乎为 0，任意放大不糊
//
// 构图顺序很重要：耳朵 → 头 → 五官。
//   耳朵先画、头后画，耳朵的下半截就被头盖住，看起来是"长在头上"。
// =============================================================================
defineProps({
  size: { type: Number, default: 24 },
})
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 48 48"
    class="cat-face"
    role="img"
    aria-label="小猫"
  >
    <!-- 1. 外耳 -->
    <path class="ear" d="M13 20 L8.5 5 L22 12 Z" />
    <path class="ear" d="M35 20 L39.5 5 L26 12 Z" />
    <!-- 2. 内耳（浅色，让耳朵有层次） -->
    <path class="ear-inner" d="M14 19 L11.6 9.5 L19.8 14 Z" />
    <path class="ear-inner" d="M34 19 L36.4 9.5 L28.2 14 Z" />
    <!-- 3. 头（盖住耳朵根部） -->
    <ellipse class="head" cx="24" cy="28" rx="13.6" ry="12" />
    <!-- 4. 眼睛：白眼球 + 深瞳孔 + 高光，靠 scaleY 做眨眼 -->
    <g class="eyes">
      <ellipse class="eye-white" cx="19" cy="26.5" rx="2.7" ry="3.2" />
      <ellipse class="eye-white" cx="29" cy="26.5" rx="2.7" ry="3.2" />
      <ellipse class="pupil" cx="19" cy="27" rx="1.5" ry="2.1" />
      <ellipse class="pupil" cx="29" cy="27" rx="1.5" ry="2.1" />
      <circle class="spark" cx="19.7" cy="25.8" r="0.55" />
      <circle class="spark" cx="29.7" cy="25.8" r="0.55" />
    </g>
    <!-- 5. 鼻子 + 嘴 -->
    <path class="nose" d="M24 31.2 l-1.5 1.5 h3 Z" />
    <path class="mouth" d="M24 32.7 v1.3 M24 34 q-1.6 1.6 -3 0 M24 34 q1.6 1.6 3 0" />
    <!-- 6. 胡须 -->
    <path class="whisker" d="M12.5 30.5 h-6.5 M12.5 33.5 h-6.5 M35.5 30.5 h6.5 M35.5 33.5 h6.5" />
  </svg>
</template>

<style scoped>
.cat-face {
  display: block;
  overflow: visible;
}
.head {
  fill: var(--violet);
}
.ear {
  fill: var(--violet);
  opacity: 0.8;
}
.ear-inner {
  fill: var(--bg);
  opacity: 0.55;
}
.eye-white {
  fill: #fffaf0;
}
.pupil {
  fill: #3a2a1c;
}
.spark {
  fill: #fffaf0;
}
.nose {
  fill: #fffaf0;
  opacity: 0.95;
}
.mouth {
  fill: none;
  stroke: var(--bg);
  stroke-width: 1;
  stroke-linecap: round;
  opacity: 0.75;
}
.whisker {
  stroke: var(--violet-l);
  stroke-width: 1;
  stroke-linecap: round;
  opacity: 0.5;
}

/* 眨眼：以两眼中间为原点纵向压扁（5 秒一次，一次 0.3 秒，不会太闹） */
.eyes {
  transform-origin: 24px 26.5px;
  animation: blink 5s ease-in-out infinite;
}
@keyframes blink {
  0%,
  90%,
  100% {
    transform: scaleY(1);
  }
  93% {
    transform: scaleY(0.12);
  }
  96% {
    transform: scaleY(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .eyes {
    animation: none;
  }
}
</style>
