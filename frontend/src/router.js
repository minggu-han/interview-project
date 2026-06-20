// 前端路由表：使用 hash 模式（URL 形如 /#/admin），无需后端额外配置即可直接刷新
import { createRouter, createWebHashHistory } from 'vue-router'
import Login from './views/Login.vue'
import AdminDashboard from './views/AdminDashboard.vue'
import AdminReport from './views/AdminReport.vue'
import InterviewRoom from './views/InterviewRoom.vue'

// meta.role 标注该页面要求的角色，供下方全局守卫做权限校验
const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/admin', component: AdminDashboard, meta: { role: 'admin' } },           // 管理后台
  { path: '/admin/report/:interviewId', component: AdminReport, meta: { role: 'admin' } }, // 管理员查看某场面试报告
  { path: '/interview', component: InterviewRoom, meta: { role: 'candidate' } },    // 面试者答题间
]

const router = createRouter({ history: createWebHashHistory(), routes })

// 全局前置守卫：进入需要权限的页面前，校验本地是否登录且角色匹配，否则打回登录页
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')
  if (to.meta.role) {
    if (!token) return '/login'              // 未登录
    if (to.meta.role !== role) return '/login' // 角色不符（如面试者访问管理页）
  }
  return true
})

export default router
