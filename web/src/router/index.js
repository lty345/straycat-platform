// 路由表：一个路由 = 一个页面组件
// 页面文件放 src/views/，公共组件放 src/components/
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home', meta: { title: '概览' },
    component: () => import('../views/Home.vue'),
  },
  {
    path: '/contents',
    name: 'contents', meta: { title: '内容' },
    component: () => import('../views/ContentList.vue'),
  },
  {
    path: '/contents/:id',           // :id
    name: 'content-detail', meta: { title: '内容详情' },            // ← 这个名字第 9 步要用来跳转
    component: () => import('../views/ContentDetail.vue'),
  },
  {
    path: '/feed',
    name: 'feed', meta: { title: '推荐' },
    component: () => import('../views/Feed.vue'),
  },
  {
    path: '/cats',
    name: 'cats', meta: { title: '领养' },
    component: () => import('../views/CatList.vue'),
  },
  // 404：必须放最后，它兜底
  {
    path: '/about',
    name: 'about',
    component: () => import('../views/About.vue'),
    meta: { title: '关于' },
  },

  {
    path: '/:pathMatch(.*)*',
    name: 'not-found', meta: { title: '页面不存在' },
    component: () => import('../views/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由切换时同步浏览器标签标题：方便在多个标签间区分，也是 SEO/分享的基础
const SITE = '初尧 · 流浪猫内容社区'
router.afterEach((to) => {
  const t = to.meta && to.meta.title
  document.title = t ? `${t} · 初尧` : SITE
})

export default router
