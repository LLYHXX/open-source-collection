<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const router = useRouter()
const route = useRoute()

// 访问页（设置密码/登录）全屏渲染，不套侧边栏布局
const isAccessPage = computed(() => route.path === '/access')

const menuItems = [
  { index: '/', title: '控制台', icon: 'Monitor' },
  { index: '/tasks', title: '任务', icon: 'List' },
  { index: '/schedules', title: '定时任务', icon: 'Timer' },
  { index: '/vulns', title: '漏洞', icon: 'Warning' },
  { index: '/reports', title: '报告', icon: 'Document' },
  { index: '/intel', title: '情报库', icon: 'Coin' },
  { index: '/hunting', title: '持续挖掘', icon: 'MagicStick' },
  { index: '/androidlab', title: '移动靶场', icon: 'Cellphone' },
  { index: '/settings', title: '设置', icon: 'Setting' },
]

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
          <div class="logo-sub">确定性引擎 · 工具为主</div>
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
          <span>{{ m.title }}</span>
        </el-menu-item>
      </el-menu>
      <div class="aside-foot">
        <div class="foot-dot" />
        引擎 10 插件待命
      </div>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span class="header-title">多 Agent 协同漏洞挖掘平台</span>
        <el-tag effect="dark" size="small" type="primary" class="header-badge">
          自研引擎 · 检测命中必复现 · CVSS 自动定级
        </el-tag>
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
  border-radius: 10px;
  color: #fff;
  background: linear-gradient(135deg, #22d3ee, #3b82f6);
  box-shadow: 0 4px 14px rgba(34, 211, 238, 0.35);
  flex-shrink: 0;
}
.logo {
  color: #fff;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.2px;
  white-space: nowrap;
}
.logo-hl {
  background: linear-gradient(90deg, #22d3ee, #60a5fa);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.logo-sub {
  font-size: 11px;
  color: #64748b;
  margin-top: 1px;
  white-space: nowrap;
}
.menu {
  border-right: none;
  padding: 4px 8px;
  flex: 1;
}
.menu :deep(.el-menu-item) {
  border-radius: 10px;
  margin: 3px 0;
  height: 44px;
  transition: background 0.15s ease;
}
.menu :deep(.el-menu-item:hover) {
  background: rgba(59, 130, 246, 0.12);
}
.menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(34, 211, 238, 0.22), rgba(59, 130, 246, 0.22));
  border: 1px solid rgba(59, 130, 246, 0.35);
  font-weight: 600;
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
.foot-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 8px #34d399;
  animation: pulse 2s infinite;
}
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
.header-title {
  font-size: 13px;
  color: #8b94a8;
}
.header-badge {
  border: 1px solid rgba(59, 130, 246, 0.4);
}
.main {
  position: relative;
  z-index: 1;
  padding: 20px 22px;
}
</style>
