<script setup lang="ts">
import { computed, inject, onMounted, onUnmounted, provide, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const router = useRouter()
const route = useRoute()

const theme = ref<string>('default')

// ===== Cyber 短标签体系（提供给所有子视图 inject 复用）=====
const uiLabels = reactive({
  isCyber: computed(() => theme.value === 'cyber'),
  isMono: computed(() => theme.value === 'mono'),
  // === 菜单短标签 ===
  menu: {
    '/':          { full: '控制台',     cyber: 'HOME' },
    '/tasks':     { full: '任务',       cyber: 'TASKS' },
    '/schedules': { full: '定时任务',   cyber: 'CRON' },
    '/vulns':     { full: '漏洞',       cyber: 'VULNS' },
    '/reports':   { full: '报告',       cyber: 'REP' },
    '/intel':     { full: '情报库',     cyber: 'INTEL' },
    '/memory':    { full: '记忆管理',   cyber: 'MEM' },
    '/hunting':   { full: '持续挖掘',   cyber: 'MINE' },
    '/androidlab':{ full: '移动靶场',   cyber: 'LAB' },
    '/settings':  { full: '设置',       cyber: 'CFG' },
  } as Record<string, { full: string; cyber: string }>,
  // === 通用动作短标签 ===
  actions: {
    new:    { full: '新增',      cyber: 'NEW' },
    edit:   { full: '编辑',      cyber: 'EDIT' },
    retire: { full: '退役',      cyber: 'RETIRE' },
    purge:  { full: '删除',      cyber: 'PURGE' },
    in:     { full: '导入',      cyber: 'IN' },
    out:    { full: '导出',      cyber: 'OUT' },
    search: { full: '查询',      cyber: 'SRCH' },
    reset:  { full: '重置',      cyber: 'RST' },
    save:   { full: '保存',      cyber: 'SAVE' },
    cancel: { full: '取消',      cyber: 'CANCEL' },
    confirm:{ full: '确认',      cyber: 'OK' },
    approve:{ full: '批准',      cyber: 'APPR' },
    reject: { full: '拒绝',      cyber: 'REJECT' },
    trigger:{ full: '触发一次',  cyber: 'TRIGGER' },
  } as Record<string, { full: string; cyber: string }>,
  // === Memory 四卡统计短标签 ===
  memoryRubric: {
    total:      { full: '记忆条目',          cyber: 'CNT' },
    lifecycle:  { full: '生命周期',          cyber: 'CNF' },
    kind:       { full: '类型分布（Top 6）', cyber: 'Σ/KIND DIST' },
    daily:      { full: '近 7 日增量',       cyber: 'Δ7D' },
    total_hits: { full: '命中次数',          cyber: 'ΣHITS' },
    active:     { full: '活跃',              cyber: 'L.ACT' },
    stale:      { full: '陈旧',              cyber: 'L.STL' },
    retired:    { full: '退役',              cyber: 'L.RET' },
  } as Record<string, { full: string; cyber: string }>,
  // === Lifecycle 短标签 ===
  lifecycle: {
    active:  { full: '活跃',   cyber: 'L.ACT' },
    stale:   { full: '陈旧',   cyber: 'L.STL' },
    retired: { full: '退役',   cyber: 'L.RET' },
  } as Record<string, { full: string; cyber: string }>,
  // === 状态显示 ===
  status: {
    pending_approval: { full: '待审批',   cyber: 'PENDING APPR' },
    rejected:         { full: '已拒绝',   cyber: 'REJECTED' },
    pending:          { full: '待执行',   cyber: 'QUEUED' },
    running:          { full: '执行中',   cyber: 'RUN' },
    success:          { full: '完成',     cyber: 'DONE' },
    failed:           { full: '失败',     cyber: 'FAIL' },
  } as Record<string, { full: string; cyber: string }>,
})

provide('uiLabels', uiLabels)

// 也允许子视图没有 inject 时通过 inject 拿默认
try { inject('uiLabels', uiLabels) } catch { /* ignore */ }

// 访问页（设置密码/登录）全屏渲染，不套侧边栏布局
const isAccessPage = computed(() => route.path === '/access')
const isCyber = computed(() => uiLabels.isCyber.value)

const menuItems = [
  { index: '/',          title: '控制台',     cyber: 'HOME',     icon: 'Monitor' },
  { index: '/tasks',     title: '任务',       cyber: 'TASKS',    icon: 'List' },
  { index: '/schedules', title: '定时任务',   cyber: 'CRON',     icon: 'Timer' },
  { index: '/vulns',     title: '漏洞',       cyber: 'VULNS',    icon: 'Warning' },
  { index: '/reports',   title: '报告',       cyber: 'REP',      icon: 'Document' },
  { index: '/intel',     title: '情报库',     cyber: 'INTEL',    icon: 'Coin' },
  { index: '/memory',    title: '记忆管理',   cyber: 'MEM',      icon: 'Collection' },
  { index: '/hunting',   title: '持续挖掘',   cyber: 'MINE',     icon: 'MagicStick' },
  { index: '/androidlab',title: '移动靶场',   cyber: 'LAB',      icon: 'Cellphone' },
  { index: '/settings',  title: '设置',       cyber: 'CFG',      icon: 'Setting' },
]

function menuLabel(m: any) { return isCyber.value ? m.cyber : m.title }
const logoSub = computed(() => isCyber.value ? 'SYS V:0x00000001 · OK' : '确定性引擎 · 工具为主')
const headerTitle = computed(() => isCyber.value ? 'CNTRL:OPERATIONS_CONSOLE' : '多 Agent 协同漏洞挖掘平台')
const headerBadge = computed(() => isCyber.value ? 'ENGINE · DETERM · CVSS 3.1' : '自研引擎 · 检测命中必复现 · CVSS 自动定级')
const asideFootText = computed(() => isCyber.value ? 'ENGINE · 0xA PLUGINS · RDY' : '引擎 10 插件待命')

function applyTheme(t: string, persist = true) {
  if (!t || !['default', 'cyber', 'mono'].includes(t)) t = 'default'
  theme.value = t
  try {
    document.documentElement.setAttribute('data-theme', t)
    if (t === 'cyber' || t === 'mono') document.body.setAttribute('data-theme', t)
    else document.body.removeAttribute('data-theme')
    if (persist) localStorage.setItem('ui.theme', t)
  } catch { /* ignore */ }
}

// 主题切换：子页面 PUT ui.theme 后通过自定义事件广播
function _onThemeChange(e: any) {
  const t = e?.detail?.theme
  if (t) applyTheme(t, true)
}

onMounted(async () => {
  // 1) 先从 localStorage 取（main.ts 已经写过 data-theme，这里同步 ref）
  let t = 'default'
  try { t = localStorage.getItem('ui.theme') || document.documentElement.getAttribute('data-theme') || 'default' } catch {}
  applyTheme(t, false)
  // 2) 再从 Setting 表覆盖（ui.theme 优先级最高，若存在）
  //    listSettings 后端 response_model=list[SettingOut]，直接返回数组，非 StandardResponse
  try {
    const res: any = await api.listSettings()
    if (Array.isArray(res)) {
      const row = res.find((s: any) => s.key && s.key.toLowerCase() === 'ui.theme')
      if (row?.value) applyTheme(row.value, true)
    }
  } catch { /* ignore */ }

  window.addEventListener('aif-theme-change', _onThemeChange as any)
})
onUnmounted(() => {
  window.removeEventListener('aif-theme-change', _onThemeChange as any)
})

// watch 提供给 inject 方响应式：theme 变了就重写 isCyber
watch(theme, (nv) => { applyTheme(nv, true) })

function go(index: string) {
  router.push(index)
}
</script>

<template>
  <router-view v-if="isAccessPage" />
  <el-container v-else style="height: 100vh">
    <el-aside width="216px" class="aside">
      <div class="logo-wrap">
        <div class="logo-badge">
          <el-icon :size="20"><Aim /></el-icon>
        </div>
        <div>
          <div class="logo">aififteen <span class="logo-hl">Hunter</span></div>
          <div class="logo-sub">{{ logoSub }}</div>
        </div>
      </div>
      <el-menu
        :default-active="route.path"
        background-color="transparent"
        text-color="#9aa5bd"
        active-text-color="#ffffff"
        class="menu"
        @select="go"
      >
        <el-menu-item v-for="m in menuItems" :key="m.index" :index="m.index">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ menuLabel(m) }}</span>
        </el-menu-item>
      </el-menu>
      <div class="aside-foot">
        <div class="foot-dot" />
        {{ asideFootText }}
      </div>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span class="header-title">{{ headerTitle }}</span>
        <el-tag effect="dark" size="small" type="primary" class="header-badge">
          {{ headerBadge }}
        </el-tag>
        <span v-if="isCyber" class="blink-cursor" style="margin-left:10px;font-size:14px;color:var(--accent,#00e5ff);">■</span>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.aside {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #0d1226 0%, #0b1020 100%);
  border-right: 1px solid rgba(148, 163, 184, 0.1);
}
:global([data-theme='cyber']) .aside,
:global([data-theme='mono']) .aside {
  background: var(--bg-0, #050608);
  border-right: 1px solid var(--border-1, #1a1d24);
  border-radius: 0;
}
.logo-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 16px 14px;
}
.logo-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: var(--radius-button, 10px);
  color: #fff;
  background: linear-gradient(135deg, #22d3ee, #3b82f6);
  box-shadow: 0 4px 14px rgba(34, 211, 238, 0.35);
  flex-shrink: 0;
}
:global([data-theme='cyber']) .logo-badge {
  background: transparent;
  border: 1px solid var(--accent, #00e5ff);
  color: var(--accent, #00e5ff);
  box-shadow: 0 0 12px rgba(0,229,255,0.25);
  border-radius: 0;
}
.logo {
  color: #fff;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.2px;
  white-space: nowrap;
}
:global([data-theme='cyber']) .logo {
  font-family: var(--font-mono, Consolas, monospace);
  letter-spacing: 0.04em;
}
.logo-hl {
  background: linear-gradient(90deg, #22d3ee, #60a5fa);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
:global([data-theme='cyber']) .logo-hl {
  background: none;
  -webkit-text-fill-color: var(--accent, #00e5ff);
}
.logo-sub {
  font-size: 11px;
  color: #64748b;
  margin-top: 1px;
  white-space: nowrap;
}
:global([data-theme='cyber']) .logo-sub {
  color: var(--text-3, #7f8ea3);
  font-family: var(--font-mono, Consolas, monospace);
}
.menu {
  border-right: none;
  padding: 4px 8px;
  flex: 1;
}
.menu :deep(.el-menu-item) {
  border-radius: var(--radius-button, 10px);
  margin: 3px 0;
  height: 44px;
  transition: background 0.15s ease;
}
.menu :deep(.el-menu-item:hover) {
  background: rgba(59, 130, 246, 0.12);
}
:global([data-theme='cyber']) .menu :deep(.el-menu-item:hover),
:global([data-theme='mono']) .menu :deep(.el-menu-item:hover) {
  background: transparent;
  border: 1px solid var(--accent, #00e5ff);
  color: var(--accent, #00e5ff);
  border-radius: 0;
}
.menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(34, 211, 238, 0.22), rgba(59, 130, 246, 0.22));
  border: 1px solid rgba(59, 130, 246, 0.35);
  font-weight: 600;
}
:global([data-theme='cyber']) .menu :deep(.el-menu-item.is-active),
:global([data-theme='mono']) .menu :deep(.el-menu-item.is-active) {
  background: transparent;
  border: 1px solid var(--accent, #00e5ff);
  color: var(--accent, #00e5ff);
  border-radius: 0;
  box-shadow: 0 0 10px rgba(0,229,255,0.15) inset;
}
.aside-foot {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 18px;
  font-size: 12px;
  color: #64748b;
  border-top: 1px solid rgba(148, 163, 184, 0.08);
}
:global([data-theme='cyber']) .aside-foot {
  font-family: var(--font-mono, Consolas, monospace);
  color: var(--text-2, #9fb0c7);
  border-top: 1px solid var(--border-1, #1a1d24);
}
.foot-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 8px #34d399;
  animation: pulse 2s infinite;
}
:global([data-theme='cyber']) .foot-dot { border-radius: 0; background: var(--accent, #00e5ff); box-shadow: 0 0 10px var(--accent, #00e5ff); }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}
.header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  height: 58px;
  background: rgba(13, 18, 38, 0.82);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}
:global([data-theme='cyber']) .header,
:global([data-theme='mono']) .header {
  background: var(--bg-1, #0a0c10);
  border-bottom: 1px solid var(--border-1, #1a1d24);
  backdrop-filter: none;
  border-radius: 0;
}
.header-title {
  font-size: 13px;
  color: #8b94a8;
}
:global([data-theme='cyber']) .header-title {
  font-family: var(--font-mono, Consolas, monospace);
  color: var(--text-2, #9fb0c7);
  letter-spacing: 0.02em;
}
.header-badge {
  border: 1px solid rgba(59, 130, 246, 0.4);
}
:global([data-theme='cyber']) .header-badge,
:global([data-theme='mono']) .header-badge {
  border-radius: 0;
  border: 1px solid var(--accent, #00e5ff);
  background: transparent;
  color: var(--accent, #00e5ff);
}
.main {
  position: relative;
  z-index: 1;
  padding: 20px 22px;
}
</style>
