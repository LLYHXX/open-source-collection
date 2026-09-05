<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { zh, SEVERITY } from '@/i18n/cn'

const router = useRouter()
const stats = ref({ tasks: 0, vulns: 0, pending: 0, intel: 0 })
const recent = ref<any[]>([])
const recentVulns = ref<any[]>([])
const health = ref('unknown')
const detectors = ref<any[]>([])

function sevText(s: string) {
  return (SEVERITY as any)[s] || zh(s)
}
function healthText(s: string) {
  if (s === 'ok') return '正常'
  if (s === 'err') return '异常'
  return s === 'unknown' ? '未知' : s
}
function modeText(m: string) {
  return zh(m) || m
}
function statusText(s: string) {
  return zh(s) || s
}

const cards = computed(() => [
  { label: '任务总数', value: stats.value.tasks, color: '#60a5fa', icon: 'List' },
  { label: '已确认漏洞', value: stats.value.vulns, color: '#f87171', icon: 'Warning' },
  { label: '待人工复审', value: stats.value.pending, color: '#fbbf24', icon: 'View' },
  { label: '情报条目', value: stats.value.intel, color: '#34d399', icon: 'Coin' },
])

const heroBadges = [
  { icon: 'Cpu', text: '10 类确定性检测插件' },
  { icon: 'CircleCheck', text: '检测命中必独立复现' },
  { icon: 'Histogram', text: 'CVSS 3.1 自动定级' },
  { icon: 'Coin', text: '最低配模型即可跑通全流程' },
]

function sevClass(s: string) {
  return `sev-tag sev-${s || 'info'}`
}

async function load() {
  try {
    const [tasks, vulns, intel, h, det] = await Promise.all([
      api.listTasks(),
      api.listVulns(),
      api.listIntel(),
      api.health().catch(() => ({ status: 'err' })),
      api.engineDetectors().catch(() => ({ detectors: [] })),
    ])
    // tasks/vulns: listTasks/listVulns 后端直接返回数组
    // intel: listIntel 返回 StandardResponse 包装 {data:{items,total,...}}
    const intelData = (intel as any)?.data
    const intelCount = intelData?.total ?? intelData?.items?.length ?? 0
    stats.value = {
      tasks: Array.isArray(tasks) ? tasks.length : 0,
      vulns: Array.isArray(vulns) ? vulns.length : 0,
      pending: Array.isArray(vulns)
        ? vulns.filter((v: any) => v.status === 'ai_reviewed').length
        : 0,
      intel: intelCount,
    }
    recent.value = Array.isArray(tasks) ? tasks.slice(0, 6) : []
    recentVulns.value = Array.isArray(vulns) ? vulns.slice(0, 6) : []
    detectors.value = (det as any).detectors || []
  } catch {
    // 统计接口失败不改健康状态（健康已单独探测）
  }
}
onMounted(load)
// 30s 轮询健康状态，页面驻留期间状态实时
const healthTimer = window.setInterval(loadHealth, 30000)
onUnmounted(() => window.clearInterval(healthTimer))
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center">
      <h2 class="page-title">控制台</h2>
      <el-tag :type="health === 'ok' ? 'success' : 'danger'" effect="dark">
        后端: {{ healthText(health) }}
      </el-tag>
    </div>

    <!-- Hero：产品定位 -->
    <div class="hero">
      <div class="hero-left">
        <div class="hero-title">工具为主 · Agent 为辅</div>
        <div class="hero-desc">
          自研检测引擎以确定性规则完成 10 类高频漏洞检测 ——
          换任何最低端的大模型，检出率不打折：LLM 只负责 Payload 变异与复杂场景兜底，
          检测、复现、定级全部由引擎独立完成。
        </div>
        <div class="hero-badges">
          <span v-for="b in heroBadges" :key="b.text" class="hero-badge">
            <el-icon :size="13"><component :is="b.icon" /></el-icon>
            {{ b.text }}
          </span>
        </div>
      </div>
      <div class="hero-art mono">
        <div class="flow-line">指纹前置 → 插件匹配 → 确定性检测</div>
        <div class="flow-line">→ 误报过滤 → 独立复现 → CVSS 定级</div>
        <div class="flow-line flow-llm">LLM：仅兜底（payload 变异 / 复杂场景）</div>
      </div>
    </div>

    <!-- 统计卡 -->
    <el-row :gutter="14" style="margin-top: 16px">
      <el-col :span="6" v-for="c in cards" :key="c.label">
        <div class="stat-card" :style="{ color: c.color }">
          <div style="display: flex; justify-content: space-between; align-items: flex-start">
            <div>
              <div class="stat-num">{{ c.value }}</div>
              <div class="muted" style="margin-top: 2px">{{ c.label }}</div>
            </div>
            <el-icon :size="22" style="opacity: 0.85"><component :is="c.icon" /></el-icon>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 引擎插件 -->
    <el-card style="margin-top: 16px">
      <template #header>
        <div style="display: flex; align-items: center; gap: 8px">
          自研检测引擎 · 插件清单
          <el-tag size="small" type="success" effect="dark">
            {{ detectors.length }} 个已加载
          </el-tag>
          <span class="muted" style="margin-left: auto">
            每个插件：匹配条件 + 检测逻辑 + 独立验证（检测命中 ≠ 漏洞）
          </span>
        </div>
      </template>
      <div class="plugin-grid">
        <div v-for="d in detectors" :key="d.id" class="plugin-item">
          <div style="display: flex; align-items: center; gap: 8px">
            <span class="mono" style="color: #93c5fd; font-size: 12px">{{ d.id }}</span>
            <el-tag v-if="!d.side_effect_free" size="small" type="warning" effect="plain">
              副作用
            </el-tag>
            <el-tag v-else size="small" type="success" effect="plain">无副作用</el-tag>
          </div>
          <div style="font-weight: 600; margin: 6px 0 4px">{{ d.name }}</div>
          <div class="muted" style="font-size: 12px; line-height: 1.6">{{ d.description }}</div>
        </div>
        <div v-if="!detectors.length" class="muted txt-cyber" style="padding: 8px">
          LINK_DOWN · BE · WAIT
        </div>
      </div>
    </el-card>

    <el-row :gutter="14" style="margin-top: 16px">
      <!-- 最近漏洞 -->
      <el-col :span="14">
        <el-card style="height: 100%">
          <template #header>最近漏洞</template>
          <el-table :data="recentVulns" size="small" @row-click="(r: any) => router.push('/vulns')">
            <el-table-column label="严重级别" width="96">
              <template #default="{ row }">
                <span :class="sevClass(row.severity)">{{ sevText(row.severity) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" show-overflow-tooltip />
            <el-table-column prop="target_url" label="目标" width="170" show-overflow-tooltip />
            <el-table-column label="置信" width="60">
              <template #default="{ row }">{{ (row.confidence * 100).toFixed(0) }}%</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!recentVulns.length" description="暂无漏洞数据" :image-size="40" />
        </el-card>
      </el-col>
      <!-- 最近任务 -->
      <el-col :span="10">
        <el-card style="height: 100%">
          <template #header>最近任务</template>
          <el-table :data="recent" size="small" @row-click="(r: any) => router.push(`/tasks/${r.id}`)">
            <el-table-column prop="name" label="任务名" show-overflow-tooltip />
            <el-table-column label="模式" width="108">
              <template #default="{ row }">
                <el-tag size="small" :type="row.mode === 'engine' ? 'success' : 'info'" effect="dark">
                  {{ modeText(row.mode) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">{{ statusText(row.status) }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!recent.length" description="暂无任务数据" :image-size="40" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  margin-top: 14px;
  padding: 22px 24px;
  border-radius: 16px;
  border: 1px solid rgba(59, 130, 246, 0.3);
  background:
    radial-gradient(ellipse 600px 220px at 90% -30%, rgba(34, 211, 238, 0.22), transparent),
    linear-gradient(135deg, rgba(59, 130, 246, 0.14), rgba(17, 24, 50, 0.9));
}
.hero-title {
  font-size: 22px;
  font-weight: 800;
  background: linear-gradient(90deg, #22d3ee, #93c5fd);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.hero-desc {
  max-width: 560px;
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.9;
  color: #aeb7c9;
}
.hero-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  font-size: 12px;
  color: #bfdbfe;
  border: 1px solid rgba(59, 130, 246, 0.4);
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.1);
}
.hero-art {
  text-align: right;
  color: #64748b;
  font-size: 12px;
  line-height: 2.1;
  flex-shrink: 0;
}
.flow-line {
  padding: 3px 10px;
  border-right: 2px solid rgba(34, 211, 238, 0.55);
  color: #9aa5bd;
}
.flow-llm {
  color: #64748b;
  border-right-color: rgba(100, 116, 139, 0.5);
}
.el-table .el-table__row {
  cursor: pointer;
}
</style>
