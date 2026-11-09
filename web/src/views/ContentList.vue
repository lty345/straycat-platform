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

// TODO(你) 1：从 'vue' 里 import 需要的 API（ref / computed / onMounted）
// TODO(你) 2：import { fetchContents } from '../api/content'

// TODO(你) 3：定义状态
//   list  : 内容数组，初始 []
//   total : 总数，初始 0
//   page  : 当前页，初始 1
//   loading : 是否加载中，初始 false
//   error : 错误消息字符串，初始 ''

// TODO(你) 4：totalPages 用 computed 算出来
//   公式提示：总数 / 每页条数，向上取整；total 为 0 时至少是 1 页
//   （Math.ceil 是向上取整，别用 Math.round）

// TODO(你) 5：写 load()
//   进入时 loading = true、error = ''
//   调 fetchContents({ page: page.value, pageSize: 10 })
//   成功：把返回的 data.list / data.total 填进状态
//   失败：error.value = e.message，并把 list 清空
//   不论成败，最后都要 loading = false（想想要放哪 —— finally）

// TODO(你) 6：写 prev() / next()
//   边界：第 1 页不能上一页；最后一页不能下一页；翻页后要重新 load()

// TODO(你) 7：onMounted 时调用一次 load()

const PAGE_SIZE = 10
</script>

<template>
  <section>
    <!-- TODO(你)：标题「内容」+ 一个刷新按钮（loading 时禁用、文字变「加载中…」） -->

    <!-- TODO(你)：v-if 出错 → 显示 error + 引导文案
         （后端接口没实现时会是 404，文案要告诉用户「这是正常的，接口还没写」） -->

    <!-- TODO(你)：v-else-if 加载中 -->

    <!-- TODO(你)：v-else-if 空列表 -->

    <!-- TODO(你)：v-else → 列表（标题 / 摘要 / 时间 / mood 标签）+ 分页条
         列表项字段和后端 content 表对齐：title / summary / pub_time / mood
         v-for 记得加 :key -->

    <!-- TODO(你)：分页条 -->
    <!-- 上一页 | 第 x / y 页　共 n 条 | 下一页 -->
  </section>
</template>

<style scoped>
/* 颜色变量已经在 src/style.css 里定义好了，直接用：
     var(--bg)       页面底色
     var(--panel)    卡片底色
     var(--line)     边框
     var(--fg)       主文字
     var(--muted)    次要文字
     var(--violet)   紫罗兰（点缀、◈）
     var(--violet-l) 亮紫罗兰（链接、高亮）
   规矩：不要在这里写死 #hex，一律用变量。 */
</style>
