<script setup>
// =============================================================================
// views/Login.vue —— 登录 / 注册（同一个页面切换）
// =============================================================================
// 设计点：
//   ① redirect 查询参数：从 /cats 点登录 → /login?redirect=/cats，登录后回跳
//   ② 错误只用一个 error 变量：后端所有失败都返回可读 message
//   ③ autocomplete 写对，浏览器密码管理器才认（不然每次都要手输）
// =============================================================================
import { computed, reactive, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { auth, doLogin, doRegister } from '../auth/store'

const route = useRoute()
const router = useRouter()

const mode = ref('login')            // 'login' | 'register'
const form = reactive({
  username: '',
  password: '',
  nickname: '',
  city: '',
  interest_tags: '',
})
const error = ref('')
const submitting = ref(false)
// 字段级错误：提交前就能提示，不用等后端
const fieldErrors = reactive({ username: '', password: '' })

function validate() {
  const name = form.username.trim()
  fieldErrors.username = /^[A-Za-z0-9_]{3,32}$/.test(name)
    ? ''
    : '用户名 3~32 位，只能包含字母、数字、下划线'
  fieldErrors.password = form.password.length >= 8 ? '' : '密码至少 8 位'
  return !fieldErrors.username && !fieldErrors.password
}

const isRegister = computed(() => mode.value === 'register')

// 已经登录了就别停在登录页
onMounted(() => {
  if (auth.user) router.replace('/')
})

function switchMode(next) {
  mode.value = next
  error.value = ''
}

async function submit() {
  error.value = ''
  if (!validate()) return          // 前端先拦一道，省一次请求也更好懂
  submitting.value = true
  try {
    if (isRegister.value) {
      await doRegister({
        username: form.username.trim(),
        password: form.password,
        nickname: form.nickname.trim() || undefined,
        city: form.city.trim() || undefined,
        interestTags: form.interest_tags.trim() || undefined,
      })
    } else {
      await doLogin({ username: form.username.trim(), password: form.password })
    }
    const target = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.replace(target)
  } catch (e) {
    // 后端如果指明了哪个字段，就显示在对应输入框下面
    if (e.field && e.field in fieldErrors) {
      fieldErrors[e.field] = e.message
    } else {
      error.value = e.message
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="auth">
    <div class="auth-card">
      <div class="tabs">
        <button type="button" :class="{ on: !isRegister }" @click="switchMode('login')">登录</button>
        <button type="button" :class="{ on: isRegister }" @click="switchMode('register')">注册</button>
      </div>

      <form @submit.prevent="submit">
        <label class="field">
          <span>用户名</span>
          <input
            v-model="form.username" @input="fieldErrors.username = ''"
            autocomplete="username"
            placeholder="3~32 位，字母数字下划线"
            required
          />
          <small v-if="fieldErrors.username" class="field-err">{{ fieldErrors.username }}</small>
        </label>

        <label class="field">
          <span>密码</span>
          <input
            v-model="form.password" @input="fieldErrors.password = ''"
            type="password"
            :autocomplete="isRegister ? 'new-password' : 'current-password'"
            :placeholder="isRegister ? '至少 8 位' : '输入密码'"
            required
          />
          <small v-if="fieldErrors.password" class="field-err">{{ fieldErrors.password }}</small>
        </label>

        <template v-if="isRegister">
          <label class="field">
            <span>昵称 <small>选填</small></span>
            <input v-model="form.nickname" placeholder="不填就用用户名" />
          </label>
          <label class="field">
            <span>城市 <small>选填，影响推荐</small></span>
            <input v-model="form.city" placeholder="如 广州" />
          </label>
          <label class="field">
            <span>兴趣标签 <small>选填，影响推荐</small></span>
            <input v-model="form.interest_tags" placeholder="逗号分隔，如 橘猫,日常,治愈向" />
          </label>
        </template>

        <p v-if="error" class="err">{{ error }}</p>

        <button class="submit" type="submit" :disabled="submitting">
          {{ submitting ? '处理中…' : isRegister ? '注册并登录' : '登录' }}
        </button>
      </form>

      <p class="tip">
        {{ isRegister ? '注册后自动登录，可以直接去推荐页看效果' : '还没有账号？点上面的「注册」' }}
      </p>
    </div>
  </section>
</template>

<style scoped>
.auth {
  display: flex;
  justify-content: center;
  padding: 20px 0 40px;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  background: var(--panel);
  box-shadow: var(--card-shadow);
  padding: 26px 26px 22px;
}

.tabs {
  display: flex;
  gap: 6px;
  padding: 4px;
  background: var(--bg-soft);
  border-radius: 999px;
  margin-bottom: 22px;
}

.tabs button {
  flex: 1;
  padding: 8px 0;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.18s, color 0.18s;
}

.tabs button.on {
  background: var(--panel);
  color: var(--violet-l);
  box-shadow: var(--card-shadow);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.field > span {
  font-size: 12.5px;
  color: var(--muted);
}

.field small {
  font-size: 11px;
  opacity: 0.75;
}

.field input {
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background: var(--panel);
  color: var(--fg);
  font-size: 14px;
  outline: none;
  transition: border-color 0.18s, box-shadow 0.18s;
}

.field input:focus {
  border-color: var(--violet);
  box-shadow: 0 0 0 3px rgba(192, 122, 62, 0.12);
}

.field-err {
  color: var(--bad);
  font-size: 11.5px;
  margin-top: 2px;
}
.field input:focus + .field-err,
.field.err input {
  border-color: var(--bad);
}

.err {
  margin: 0 0 14px;
  padding: 9px 12px;
  border: 1px solid var(--bad);
  border-radius: var(--radius-sm);
  color: var(--bad);
  font-size: 12.5px;
  background: rgba(192, 86, 63, 0.06);
}

.submit {
  width: 100%;
  padding: 11px 0;
  border: none;
  border-radius: 999px;
  background: var(--violet-l);
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.18s, transform 0.18s;
}

.submit:hover:not(:disabled) {
  background: var(--violet);
  transform: translateY(-1px);
}

.submit:disabled {
  opacity: 0.65;
  cursor: default;
}

.tip {
  margin: 16px 0 0;
  text-align: center;
  font-size: 12px;
  color: var(--muted);
}
</style>
