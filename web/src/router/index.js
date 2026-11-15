// 路由表：一个路由 = 一个页面组件
// 页面文件放 src/views/，公共组件放 src/components/
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/Home.vue'),
  },
  {
    path: '/contents',
    name: 'contents',
    component: () => import('../views/ContentList.vue'),
  },
  {
    path: '/contents/:id',           // :id
    name: 'content-detail',            // ← 这个名字第 9 步要用来跳转
    component: () => import('../views/ContentDetail.vue'),
  },
  {
    path: '/feed',
    name: 'feed',
    component: () => import('../views/Feed.vue'),
  },
  {
    path: '/cats',
    name: 'cats',
    component: () => import('../views/CatList.vue'),
  },
  // 404：必须放最后，它兜底
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFound.vue'),
  },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
