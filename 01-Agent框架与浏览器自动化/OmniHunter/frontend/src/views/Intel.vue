<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const list = ref<any[]>([])
const filter = ref('')

async function load() {
  list.value = await api.listIntel(filter.value || undefined)
}
async function retire(id: string) {
  await api.retireIntel(id)
  ElMessage.success('已退役')
  await load()
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
    <div style="margin: 12px 0">
      <el-select v-model="filter" placeholder="按类型筛选" clearable style="width: 200px" @change="load">
        <el-option label="凭证" value="credential" />
        <el-option label="端点" value="endpoint" />
        <el-option label="指纹" value="fingerprint" />
        <el-option label="技术栈" value="techstack" />
        <el-option label="泄露" value="leak" />
      </el-select>
      <el-button @click="load" style="margin-left: 8px">刷新</el-button>
    </div>
    <el-table :data="list" border size="small">
      <el-table-column prop="kind" label="类型" width="110" />
      <el-table-column prop="key" label="键" width="200" />
      <el-table-column prop="value" label="值" show-overflow-tooltip />
      <el-table-column label="置信度" width="90">
        <template #default="{ row }">{{ (row.confidence * 100).toFixed(0) }}%</template>
      </el-table-column>
      <el-table-column prop="hits" label="命中" width="80" />
      <el-table-column prop="lifecycle" label="生命周期" width="100" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click="retire(row.id)">退役</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
