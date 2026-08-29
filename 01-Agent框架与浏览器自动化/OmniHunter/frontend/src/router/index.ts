import { createRouter, createWebHistory } from 'vue-router'
import { api } from '@/api'

const routes = [
  // 访问控制页：设置密码 / 登录（公网访问入口）
  { path: '/access', name: 'access', component: () => import('@/views/Access.vue') },
  { path: '/', name: 'dashboard', component: () => import('@/views/Dashboard.vue') },
  { path: '/tasks', name: 'tasks', component: () => import('@/views/Tasks.vue') },
  { path: '/tasks/:id', name: 'taskDetail', component: () => import('@/views/TaskDetail.vue') },
  { path: '/schedules', name: 'schedules', component: () => import('@/views/Schedules.vue') },
  { path: '/vulns', name: 'vulns', component: () => import('@/views/Vulns.vue') },
  { path: '/reports', name: 'reports', component: () => import('@/views/Reports.vue') },
  { path: '/intel', name: 'intel', component: () => import('@/views/Intel.vue') },
  { path: '/hunting', name: 'hunting', component: () => import('@/views/Hunting.vue') },
  { path: '/androidlab', name: 'androidlab', component: () => import('@/views/AndroidLab.vue') },
  { path: '/settings', name: 'settings', component: () => import('@/views/Settings.vue') },
]

const router = createRouter({ history: createWebHistory(), routes })

// 判断当前是否本地/私网访问（依据浏览器 hostname）
function isLocalAccess(): boolean {
  const h = window.location.hostname
  if (h === 'localhost' || h === '127.0.0.1' || h === '::1') return true
  if (h.startsWith('192.168.') || h.startsWith('10.')) return true
  const m = h.match(/^172\.(\d+)\./)
  if (m && +m[1] >= 16 && +m[1] <= 31) return true
  return false
}

// 路由守卫：公网访问未设密码→设置页；已设未登录→登录页；本地或已登录→放行
router.beforeEach(async (to) => {
  if (to.path === '/access') return true
  const local = isLocalAccess()
  // 本地访问：无需密码，直接放行
  if (local) return true
  // 公网访问：查询密码状态
  try {
    const s = await api.accessStatus()
    if (!s.password_set) {
      // 未设密码 → 引导设置
      return { path: '/access', query: { mode: 'setup' } }
    }
    // 已设密码但无会话 → 引导登录
    if (!localStorage.getItem('aififteen_hunter_session')) {
      return { path: '/access', query: { mode: 'login' } }
    }
    return true
  } catch {
    // 状态查询失败（后端不可达等）→ 放行，避免彻底锁死
    return true
  }
})

export default router
