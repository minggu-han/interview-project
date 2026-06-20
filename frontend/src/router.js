import { createRouter, createWebHashHistory } from 'vue-router'
import Login from './views/Login.vue'
import AdminDashboard from './views/AdminDashboard.vue'
import AdminReport from './views/AdminReport.vue'
import InterviewRoom from './views/InterviewRoom.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/admin', component: AdminDashboard, meta: { role: 'admin' } },
  { path: '/admin/report/:interviewId', component: AdminReport, meta: { role: 'admin' } },
  { path: '/interview', component: InterviewRoom, meta: { role: 'candidate' } },
]

const router = createRouter({ history: createWebHashHistory(), routes })

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')
  if (to.meta.role) {
    if (!token) return '/login'
    if (to.meta.role !== role) return '/login'
  }
  return true
})

export default router
