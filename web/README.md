# web/ —— 前端（Vue 3 + Vite）

## 启动

```bash
cd web
npm install          # 首次
npm run dev          # http://localhost:5173
```

**后端要先起**（`uv run fastapi dev app.py`，端口 8000），否则页面会显示"没拿到内容"。

## 当前状态

| 页面 | 状态 |
|---|---|
| `/` 概览 | ✅ 后端连通性检测 |
| `/contents` 内容列表 | ✅ 分页 + 四态 + 点击进详情（mood/keyword 筛选 UI 待做） |
| `/contents/:id` 详情 | ✅ 三态 + 正文 + 返回 |
| 404 | ✅ |

接口已全部接通：`GET /api/v1/contents`、`GET /api/v1/contents/{id}`。

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
    ├── router/index.js   路由表：路径 → 页面组件
    ├── api/              ★ 所有请求只写在这里，组件里不许出现 axios/URL
    │   ├── client.js     axios 实例 + 响应拦截器（统一剥壳、统一报错）
    │   ├── system.js     /health
    │   └── content.js    列表 + 详情
    └── views/            页面（一个文件 = 一个路由）
        ├── Home.vue        概览
        ├── ContentList.vue 内容列表
        ├── ContentDetail.vue 内容详情
        └── NotFound.vue    404
```

## 四条硬规矩

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

变量全在 `src/style.css` 的 `:root` 里（含 mood 四色）。换配色只改那一个文件。

### ③ 请求走 Vite 代理，不硬编码后端地址

`baseURL` 是 `/`，实际请求 `/api/v1/xxx` 由 `vite.config.js` 转发到 `127.0.0.1:8000`。
浏览器看起来是同源请求，开发时用不到 CORS，部署时也不用改代码。

### ④ 每个页面都要有"四态"

出错 / 加载中 / 空 / 有数据——少一种，线上就是白屏或转圈不停。
详情页只有三态，"查不到"是异常不是空数据（后端返回 `success:false` + `api_code:30001`，拦截器会 reject）。

## 常见问题

**页面显示"没拿到内容"**
→ 后端没起，或者端口不是 8000（改了端口要同步改 `vite.config.js`）

**改了后端 CORS 还是报跨域**
→ 走代理的话根本不涉及 CORS；如果硬编码了 `http://127.0.0.1:8000`，那就是跨域请求，要检查后端 CORS 白名单里有没有 `5173`

**PyCharm 里右键没有 "Vue Component"**
→ 正常。项目只有 Python 模块，`package.json` 在 `web/` 子目录。用 `New → File` 直接建 `Xxx.vue`，或者把 `web/` 单独作为项目打开（PyCharm 会按 `package.json` 识别成前端项目）。

**想确认 `.vue` 能不能编译，但不想开浏览器**
→ `node_modules/@vue/compiler-sfc` 可以单独编译模板（绕开 esbuild）。
