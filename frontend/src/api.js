// axios 实例：统一封装后端 API 调用。
// baseURL 为 '/'，配合 vite.config.js 的 proxy 把 /api、/ws 转发到后端，避免开发环境跨域。
import axios from 'axios'

const api = axios.create({ baseURL: '/' })

// 请求拦截器：每次请求自动带上登录后保存的 JWT（Authorization: Bearer xxx）
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截器：遇到 401（token 失效/过期）时清掉本地登录态并跳回登录页
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response && err.response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      if (location.hash !== '#/login') location.hash = '#/login'
    }
    return Promise.reject(err)
  }
)

export default api
