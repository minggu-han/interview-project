<template>
  <div class="container" style="max-width: 420px; padding-top: 80px;">
    <div class="card">
      <h1 style="text-align:center;">智能面试系统</h1>
      <p class="muted" style="text-align:center; margin-bottom: 24px;">管理员 / 面试者 登录</p>
      <form @submit.prevent="onLogin">
        <label>用户名
          <input v-model="username" placeholder="请输入用户名" autocomplete="username" />
        </label>
        <label>密码
          <input v-model="password" type="password" placeholder="请输入密码" autocomplete="current-password" />
        </label>
        <button class="btn" style="width:100%; margin-top:8px;" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
        <p v-if="error" style="color:#dc2626; margin-top:12px; font-size:13px;">{{ error }}</p>
      </form>
      <p class="muted" style="margin-top:16px;">默认管理员：admin / admin123</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const router = useRouter()

async function onLogin() {
  error.value = ''
  loading.value = true
  try {
    const form = new URLSearchParams()
    form.append('username', username.value)
    form.append('password', password.value)
    const { data } = await api.post('/api/auth/login', form)
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('role', data.role)
    localStorage.setItem('username', data.username)
    router.push(data.role === 'admin' ? '/admin' : '/interview')
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>
