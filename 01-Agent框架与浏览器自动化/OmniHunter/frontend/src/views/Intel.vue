<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { zh, INTEL_KIND, LIFECYCLE } from '@/i18n/cn'

const list = ref<any[]>([])
const filter = ref('')
const hostInput = ref('')
const lastResult = ref('')

function kindCn(k: string) {
  return (INTEL_KIND as any)[k] || zh(k)
}
function lifecycleCn(l: string) {
  return (LIFECYCLE as any)[l] || zh(l)
}

async function load() {
  const res: any = await api.listIntel(filter.value || undefined)
  // listIntel 后端返回 StandardResponse {data:{items,total,...}}
  list.value = Array.isArray(res?.data?.items) ? res.data.items : []
}
async function retire(id: string) {
  await api.retireIntel(id)
  ElMessage.success('已退役')
  await load()
}
async function onFileChange(file: any) {
  try {
    const res: any = await api.externalUpload(file.raw, hostInput.value || '')
    lastResult.value = res.message
    res.success ? ElMessage.success(res.message) : ElMessage.error(res.message)
    await load()
  } catch (e: any) {
    ElMessage.error('上传失败: ' + (e.response?.data?.detail || e.message || e))
  }
}
function fmt(t: string) {
  return t ? new Date(t).toLocaleString() : ''
}
onMounted(load)
</script>

<template>
  <div>
    <h2 class="page-title">情报库（记忆沉淀）</h2>
    <p class="muted">
      验证过的凭证 / 端点 / 指纹 / 技术栈沉淀于此，带置信度与生命周期，后续 Worker 自动复用（借鉴 agentmemory）。
    </p>

    <el-card style="margin-bottom: 16px">
      <template #header>外接工具集成（PowerDesigner / PowerBuilder / SQL / 配置文件）</template>
      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 12px">
        <template #title>专业开发工具产物 → 情报 → 引擎消费</template>
        上传 <b>.pdm</b>（PowerDesigner 数据模型，解析库表/字段/敏感列）、<b>.srw/.srd/.srf 等</b>（PowerBuilder
        源码，审计拼接 SQL / 动态 SQL 注入 sink）、<b>.sql</b>（建表脚本）、<b>.env/.pem/.key</b>（凭据）。
        解析结果入情报库，SQL 注入利用 / IDOR 定位时按 host 自动关联。
      </el-alert>
      <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap">
        <el-input v-model="hostInput" placeholder="关联 host（如 target.com，留空用文件名）" style="width: 300px" />
        <el-upload :auto-upload="false" :on-change="onFileChange" :show-file-list="false"
          accept=".pdm,.sql,.srd,.srw,.srf,.srs,.sra,.srp,.sru,.srj,.env,.ini,.conf,.config,.pem,.key">
          <el-button type="primary">选择文件并解析</el-button>
        </el-upload>
      </div>
      <p v-if="lastResult" class="muted" style="margin-top: 10px">{{ lastResult }}</p>
    </el-card>

    <div style="margin: 12px 0">
      <el-select v-model="filter" placeholder="按类型筛选" clearable style="width: 200px" @change="load">
        <el-option label="凭证" value="credential" />
        <el-option label="端点" value="endpoint" />
        <el-option label="指纹" value="fingerprint" />
        <el-option label="技术栈" value="techstack" />
        <el-option label="泄露" value="leak" />
        <el-option label="数据库模型" value="db_schema" />
        <el-option label="PB审计" value="pb_audit" />
      </el-select>
      <el-button @click="load" style="margin-left: 8px">刷新</el-button>
    </div>
    <el-table :data="list" border size="small" stripe empty-text="暂无数据">
      <el-table-column label="类型" width="120">
        <template #default="{ row }">
          <el-tag size="small" type="info" effect="plain">{{ kindCn(row.kind) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="key" label="检索键" width="220" show-overflow-tooltip />
      <el-table-column prop="value" label="值（内容）" show-overflow-tooltip />
      <el-table-column label="置信度" width="100" align="center">
        <template #default="{ row }">{{ (row.confidence * 100).toFixed(0) }}%</template>
      </el-table-column>
      <el-table-column prop="hits" label="命中次数" width="100" align="center" />
      <el-table-column label="生命周期" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="row.lifecycle === 'active' ? 'success' : row.lifecycle === 'stale' ? 'warning' : 'info'" size="small" effect="dark">
            {{ lifecycleCn(row.lifecycle) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" align="center">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click="retire(row.id)">退役</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
