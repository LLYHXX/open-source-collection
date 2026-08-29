<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const list = ref<any[]>([])
const newKey = ref('')
const newVal = ref('')
const tokenInput = ref(localStorage.getItem('aififteen_hunter_token') || '')

// 系统更新
const version = ref<any>(null)
const updateLogs = ref('')
const updating = ref(false)

async function load() {
  list.value = await api.listSettings()
}
function setToken() {
  localStorage.setItem('aififteen_hunter_token', tokenInput.value)
  ElMessage.success('访问令牌已保存到本地')
}
async function save() {
  if (!newKey.value) return
  await api.saveSetting({ key: newKey.value, value: newVal.value })
  ElMessage.success('已保存')
  newKey.value = ''
  newVal.value = ''
  await load()
}
async function loadVersion() {
  try {
    version.value = await api.version()
  } catch {
    version.value = null
  }
}
async function doUpdate() {
  updating.value = true
  try {
    const res = await api.systemUpdate()
    updateLogs.value = res.data.logs
    ElMessage.success(res.message)
    await loadVersion()
  } catch (e: any) {
    ElMessage.error('更新失败: ' + (e.message || e))
  } finally {
    updating.value = false
  }
}
onMounted(() => {
  load()
  loadVersion()
})
</script>

<template>
  <div>
    <h2 class="page-title">设置</h2>
    <el-card style="margin-bottom: 16px">
      <template #header>访问令牌</template>
      <el-input v-model="tokenInput" placeholder="与后端 API_TOKEN 一致" style="width: 400px" show-password />
      <el-button type="primary" style="margin-left: 8px" @click="setToken">保存</el-button>
      <p class="muted">未设后端 API_TOKEN 时开放访问；生产环境务必设置。</p>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header>引擎与模型策略（工具为主 · Agent 为辅）</template>
      <el-alert type="success" :closable="false" show-icon>
        <template #title>检测、复现、定级全部由自研引擎确定性完成 —— 任意最低配 LLM 都能跑通全流程</template>
        引擎内置 10 类确定性检测插件（SQLi / XSS / RCE / 目录遍历 / SSRF / 信息泄露 / IDOR / 越权 / 弱口令 / 文件上传），
        每个检测结果都经独立 verify() 复现 + CVSS 3.1 自动定级，检出率不随模型质量波动。
        大模型只负责 Payload 变异与复杂场景兜底（Worker ReAct），换最便宜的模型即可。
      </el-alert>
      <div style="display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap">
        <el-tag effect="dark" type="success" size="small">LLM_MODEL=deepseek-chat 即可</el-tag>
        <el-tag effect="dark" type="primary" size="small">任务模式选「自研引擎」全程免 LLM 检测</el-tag>
        <el-tag effect="dark" type="info" size="small">副作用插件（弱口令/上传）默认关闭</el-tag>
      </div>
      <p class="muted" style="margin-top: 10px">
        引擎调优键：ENGINE_PLUGIN_TIMEOUT（单插件超时）、ENGINE_MAX_CONCURRENCY（并发）、
        ENGINE_WEAKPWD_ENABLED / ENGINE_UPLOAD_PROBE（副作用开关），可用下方动态配置覆盖 .env。
      </p>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header>系统更新（增量拉取，不重新下载）</template>
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px">
        <span class="muted">版本：{{ version?.data?.version || '-' }}</span>
        <span class="muted">提交：{{ version?.data?.commit || '-' }}</span>
        <el-button type="primary" :loading="updating" @click="doUpdate">一键更新</el-button>
      </div>
      <p class="muted">
        一键更新 = git pull 增量拉取最新代码 + pip install 同步依赖。
        后端用 --reload 启动会自动热重载，无需重新下载/重新部署。
      </p>
      <el-input v-if="updateLogs" v-model="updateLogs" type="textarea" :rows="10" readonly />
    </el-card>

    <el-card>
      <template #header>动态配置（存库，优先级高于 .env）</template>
      <el-table :data="list" border size="small">
        <el-table-column prop="key" label="键" width="240" />
        <el-table-column prop="value" label="值" />
      </el-table>
      <div style="margin-top: 16px; display: flex; gap: 8px">
        <el-input v-model="newKey" placeholder="键，如 LLM_MODEL" style="width: 240px" />
        <el-input v-model="newVal" placeholder="值" style="width: 320px" />
        <el-button type="primary" @click="save">新增/更新</el-button>
      </div>
    </el-card>
  </div>
</template>
