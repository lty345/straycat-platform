# web/ —— 前端（Vue 3 + Vite）

## 启动

```bash
cd web
npm install          # 首次
npm run dev          # http://localhost:5173
```

**后端要先起**（`uv run fastapi dev app.py`，端口 8000），否则页面会显示"连不上后端"。

## 目录约定

```
web/
├── index.html
├── vite.config.js        代理配置（/api → 后端 8000）
├── package.json
└── src/
    ├── main.js           入口：创建 app、装路由、挂全局样式
    ├── App.vue           外壳：顶部导航 + <RouterView>
    ├── style.css         全局样式 + 颜色变量（★ 颜色只在这里定义）
    ├── router/
    │   └── index.js      路由表：路径 → 页面组件
    ├── api/              ★ 所有请求只写在这里，组件里不许出现 axios/URL
    │   ├── client.js     axios 实例 + 响应拦截器（统一剥壳、统一报错）
    │   ├── system.js     /health
    │   └── content.js    /api/v1/contents（★ 后端还没写，见下）
    └── views/            页面（一个文件 = 一个路由）
        ├── Home.vue      概览：显示后端连通状态
        ├── ContentList.vue  内容列表（四态齐全，缺后端接口）
        └── NotFound.vue  404
```

## 三条硬规矩

### ① 组件里不许出现 `axios` 和 URL 字符串

```js
// ❌ 页面里直接请求
axios.get('http://127.0.0.1:8000/api/v1/contents')

// ✅ 走 api 层
import { fetchContents } from '../api/content'
const data = await fetchContents({ page: 1 })
```

理由：接口路径改了只改一个文件；以后要换 mock 也只改 api 层。

### ② 颜色只用 CSS 变量

```css
/* ❌ */ color: #9d8cc4;
/* ✅ */ color: var(--violet-l);
```

变量全在 `src/style.css` 的 `:root` 里。换配色只改那一个文件。

### ③ 请求走 Vite 代理，不硬编码后端地址

`baseURL` 是 `/`，实际请求 `/api/v1/xxx` 由 `vite.config.js` 转发到 `127.0.0.1:8000`。

**好处**：浏览器看起来是同源请求，开发时根本用不到 CORS；部署时也不用改代码。

## 你现在要填的

| 位置 | 要做什么 | 依赖 |
|---|---|---|
| 后端 | 写 `GET /api/v1/contents?page=&page_size=`（返回 `list/total/page/page_size`） | 先建 `content` 表 |
| 后端 | 造 20 条种子数据 | `scripts/seed_content.sql` 或 `main.py` 里插 |
| 前端 | `api/content.js` 已经写好了，**不用改** | — |
| 前端 | `ContentList.vue` 已经接好了，接口通就会显示数据 | — |
| 前端 | 列表里的「点击进详情」还没做 | 需要后端 `GET /contents/{id}` |

**垂直切片顺序：建表 → 后端接口 → `/docs` 点通 → 前端页面自动就有数据了。**

## 常见问题

**页面显示"连不上后端"**
→ 后端没起，或者端口不是 8000（改了端口要同步改 `vite.config.js`）

**页面显示"接口不存在（404）"**
→ 正常，`/api/v1/contents` 还没实现

**改了后端 CORS 还是报跨域**
→ 走代理的话根本不涉及 CORS；如果你硬编码了 `http://127.0.0.1:8000`，那就是跨域请求，要检查后端 CORS 白名单里有没有 `5173`
