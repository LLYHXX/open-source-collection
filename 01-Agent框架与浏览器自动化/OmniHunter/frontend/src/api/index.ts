import axios from 'axios'

const http = axios.create({ baseURL: '/api', timeout: 30000 })

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('aififteen_hunter_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  // 公网访问会话令牌（密码登录后签发），本地访问可无
  const session = localStorage.getItem('aififteen_hunter_session')
  if (session) config.headers['X-Access-Session'] = session
  return config
})

// 401 拦截：公网访问未登录/会话失效 → 清会话并跳登录页
http.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('aififteen_hunter_session')
      const path = window.location.pathname
      if (path !== '/access') {
        // 动态导入避免与 router 循环依赖
        import('@/router').then((m) => {
          m.default.push({ path: '/access', query: { mode: 'login' } })
        })
      }
    }
    return Promise.reject(err)
  }
)

export const api = {
  // access 访问控制（公网密码保护）
  accessStatus: () => http.get('/access/status').then((r) => r.data),
  accessSetup: (data: { password: string }) =>
    http.post('/access/setup', data).then((r) => r.data),
  accessLogin: (data: { password: string }) =>
    http.post('/access/login', data).then((r) => r.data),
  accessLogout: () => http.post('/access/logout').then((r) => r.data),
  // tasks
  listTasks: () => http.get('/tasks').then((r) => r.data),
  getTask: (id: string) => http.get(`/tasks/${id}`).then((r) => r.data),
  createTask: (data: any) => http.post('/tasks', data).then((r) => r.data),
  startTask: (id: string) => http.post(`/tasks/${id}/start`).then((r) => r.data),
  startSingle: (id: string, url: string) =>
    http.post(`/tasks/${id}/single-site`, null, { params: { url } }).then((r) => r.data),
  deleteTask: (id: string) => http.delete(`/tasks/${id}`).then((r) => r.data),
  // agents
  listRuns: (taskId?: string) =>
    http.get('/agents/runs', { params: { task_id: taskId } }).then((r) => r.data),
  listMessages: (runId?: string, targetId?: string) =>
    http
      .get('/agents/messages', { params: { run_id: runId, target_id: targetId } })
      .then((r) => r.data),
  // vulns
  listVulns: (taskId?: string, status?: string) =>
    http.get('/vulns', { params: { task_id: taskId, status } }).then((r) => r.data),
  reviewVuln: (id: string, data: any) => http.patch(`/vulns/${id}`, data).then((r) => r.data),
  deleteVuln: (id: string) => http.delete(`/vulns/${id}`).then((r) => r.data),
  // intel
  listIntel: (kind?: string) =>
    http.get('/intel', { params: { kind } }).then((r) => r.data),
  retireIntel: (id: string) => http.delete(`/intel/${id}`).then((r) => r.data),
  // external 外接工具集成 + POC 扩展（持续挖掘）
  externalUpload: (file: File, host = '') => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('host', host)
    return http.post('/external/upload', fd).then((r) => r.data)
  },
  pocExpand: (data: { target_url: string; poc_text: string; match_regex?: string; task_id?: string }) =>
    // 变体复验耗时较长（最多 40 个 × 10s），单独放宽超时
    http.post('/poc-expand', data, { timeout: 600000 }).then((r) => r.data),
  // settings
  listSettings: () => http.get('/settings').then((r) => r.data),
  saveSetting: (data: any) => http.put('/settings', data).then((r) => r.data),
  testAssetPlatform: (platform: string, query = '') =>
    http.post('/settings/asset-platforms/test', { platform, query }).then((r) => r.data),

  // android lab（移动靶场）
  androidStatus: () => http.get('/android/status').then((r) => r.data),
  androidBootstrap: (includeEmulator = true) =>
    http.post('/android/bootstrap', null, { params: { include_emulator: includeEmulator } }).then((r) => r.data),
  androidJob: (id: string) => http.get(`/android/jobs/${id}`).then((r) => r.data),
  androidInstallImage: (pkg: string) => http.post('/android/images/install', { pkg }).then((r) => r.data),
  androidAvds: () => http.get('/android/avds').then((r) => r.data),
  androidCreateAvd: (data: any) => http.post('/android/avds', data).then((r) => r.data),
  androidDeleteAvd: (name: string) => http.delete(`/android/avds/${name}`).then((r) => r.data),
  androidStartAvd: (name: string, data: any) => http.post(`/android/avds/${name}/start`, data).then((r) => r.data),
  androidStopAvd: (name: string) => http.post(`/android/avds/${name}/stop`).then((r) => r.data),
  androidDevices: () => http.get('/android/devices').then((r) => r.data),
  androidInstallApk: (serial: string, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('serial', serial)
    return http.post('/android/apps/install', fd).then((r) => r.data)
  },
  androidListApps: (serial: string) =>
    http.get('/android/apps/list', { params: { serial } }).then((r) => r.data),
  androidLaunchApp: (data: any) => http.post('/android/apps/launch', data).then((r) => r.data),
  androidUninstallApp: (data: any) => http.post('/android/apps/uninstall', data).then((r) => r.data),
  androidTrafficStart: (port = 8082) =>
    http.post('/android/traffic/start', null, { params: { port, duration: 3600 } }).then((r) => r.data),
  androidTrafficStop: () => http.post('/android/traffic/stop').then((r) => r.data),
  androidTraffic: (filter = '') =>
    http.get('/android/traffic', { params: { filter } }).then((r) => r.data),
  health: () => http.get('/health').then((r) => r.data),
  // schedules 定时任务
  listSchedules: () => http.get('/schedules').then((r) => r.data),
  createSchedule: (data: any) => http.post('/schedules', data).then((r) => r.data),
  extendSchedule: (id: string, days: number) =>
    http.post(`/schedules/${id}/extend`, { extend_days: days }).then((r) => r.data),
  toggleSchedule: (id: string) => http.post(`/schedules/${id}/toggle`).then((r) => r.data),
  runScheduleNow: (id: string) => http.post(`/schedules/${id}/run`).then((r) => r.data),
  deleteSchedule: (id: string) => http.delete(`/schedules/${id}`).then((r) => r.data),
  // reports 报告模板
  listTemplates: () => http.get('/reports/templates').then((r) => r.data),
  createTemplate: (data: any) => http.post('/reports/templates', data).then((r) => r.data),
  updateTemplate: (id: string, data: any) =>
    http.put(`/reports/templates/${id}`, data).then((r) => r.data),
  deleteTemplate: (id: string) => http.delete(`/reports/templates/${id}`).then((r) => r.data),
  generateReport: (taskId: string, templateId?: string) =>
    http
      .post('/reports/generate', { task_id: taskId, template_id: templateId })
      .then((r) => r.data),
  // system 系统
  version: () => http.get('/system/version').then((r) => r.data),
  systemUpdate: () => http.post('/system/update').then((r) => r.data),
  // 自研检测引擎
  engineDetectors: () => http.get('/tasks/engine/detectors').then((r) => r.data),
  engineScan: (url: string, adminCookie = '', userCookie = '') =>
    http
      .post(
        `/tasks/engine-scan-url?url=${encodeURIComponent(url)}` +
          `&admin_cookie=${encodeURIComponent(adminCookie)}` +
          `&user_cookie=${encodeURIComponent(userCookie)}`,
      )
      .then((r) => r.data),
}
