import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],

  server: {
    port: 5173, // 和后端 CORS 白名单里那个端口保持一致
    proxy: {
      // ★ 关键：开发时把 /api 开头的请求转给 FastAPI
      //   好处有两个：
      //   ① 浏览器看到的是「同源请求」，不会触发跨域检查
      //   ② 前端代码里写相对路径就行，不用硬编码 http://127.0.0.1:8000
      //      （部署到服务器时也不用改代码）
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // 健康检查在根路径，没带 /api 前缀，单独转一下
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
