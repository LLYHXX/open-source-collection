<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '@/api'

const stats = ref({ tasks: 0, vulns: 0, pending: 0, intel: 0 })
const recent = ref<any[]>([])
const health = ref('unknown')

const cards = computed(() => [
  { label: '任务总数', value: stats.value.tasks, color: '#409eff' },
  { label: '漏洞总数', value: stats.value.vulns, color: '#f56c6c' },
  { label: '待人工复审', value: stats.value.pending, color: '#e6a23c' },
  { label: '情报条目', value: stats.value.intel, color: '#67c23a' },
])

async function load() {
  try {
    const [tasks, vulns, intel, h] = await Promise.all([
      api.listTasks(),
      api.listVulns(),
      api.listIntel(),
      api.health().catch(() => ({ status: 'err' })),
    ])
    stats.value = {
      tasks: tasks.length,
      vulns: vulns.length,
      pending: vulns.filter((v: any) => v.status === 'ai_reviewed').length,
      intel: intel.length,
    }
    recent.value = tasks.slice(0, 6)
    health.value = (h as any).status
  } catch {
    health.value = 'err'
  }
}
onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center">
      <h2 class="page-title" style="margin: 0">控制台</h2>
      <el-tag :type="health === 'ok' ? 'success' : 'danger'">
        后端: {{ health }}
      </el-tag>
    </div>
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="6" v-for="c in cards" :key="c.label">
        <el-card shadow="hover">
          <div class="stat-num" :style="{ color: c.color }">{{ c.value }}</div>
          <div class="muted">{{ c.label }}</div>
        </el-card>
      </el-col>
    </el-row>
    <el-card style="margin-top: 16px">
      <template #header>最近任务</template>
      <el-table :data="recent" size="small">
        <el-table-column prop="name" label="任务名" />
        <el-table-column prop="mode" label="模式" width="110" />
        <el-table-column prop="source" label="来源" width="110" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column prop="created_at" label="创建时间" />
      </el-table>
    </el-card>
    <el-card style="margin-top: 16px">
      <template #header>整合架构（取其精华）</template>
      <ul class="muted" style="line-height: 1.9">
        <li><b>多 Agent 编排</b>：Collector → Recon → Worker(scan/exploit/verify) → Verifier → Reviewer（借鉴 AutoHunter + PraisonAI）</li>
        <li><b>记忆沉淀</b>：confidence + lifecycle + hybrid recall（借鉴 agentmemory + TheLibrarian）</li>
        <li><b>关卡式规划</b>：recon→scan→exploit→verify→report，evidence 准入（借鉴 LoopX + Superpowers）</li>
        <li><b>浏览器自动化</b>：Playwright Planner/Navigator/Validator，覆盖登录后/越权/逻辑漏洞（借鉴 Nanobrowser）</li>
        <li><b>工具链</b>：nmap · nuclei · sqlmap · httpx · Firecrawl · AgentReach · bettercap · 密探mitan · Cutter + MCP 预留（取自 02爬虫/03安全/03逆向/04终端 开源武器）</li>
        <li><b>独立验证</b>：Verifier 不轻信 Worker，复现 payload（借鉴 Strix / Xalgorix）</li>
      </ul>
    </el-card>
  </div>
</template>

<style scoped>
.stat-num {
  font-size: 30px;
  font-weight: 700;
}
</style>
