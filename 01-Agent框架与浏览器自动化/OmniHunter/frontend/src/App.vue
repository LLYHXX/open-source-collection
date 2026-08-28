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
  { index: '/settings', title: '设置', icon: 'Setting' },
]

function go(index: string) {
  router.push(index)
}
</script>

<template>
  <router-view v-if="isAccessPage" />
  <el-container v-else style="height: 100vh">
    <el-aside width="210px" class="aside">
      <div class="logo">aififteen Hunter</div>
      <el-menu
        :default-active="route.path"
        background-color="#001529"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        @select="go"
      >
        <el-menu-item v-for="m in menuItems" :key="m.index" :index="m.index">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        多 Agent 协同漏洞挖掘平台 · 整合 记忆 / 规划 / 浏览器 / 工具调用
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.aside {
  background: #001529;
}
.logo {
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  padding: 18px 16px;
}
.header {
  background: #f5f7fa;
  line-height: 60px;
  font-size: 13px;
  color: #606266;
  border-bottom: 1px solid #e6e6e6;
}
</style>
