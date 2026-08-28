<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const list = ref<any[]>([])
const dialog = ref(false)
const cur = ref<any>(null)
const review = reactive({ status: 'approved', severity: '', reviewer_note: '' })

async function load() {
  list.value = await api.listVulns()
}
function open(v: any) {
  cur.value = v
  review.severity = v.severity
  review.status = 'approved'
  dialog.value = true
}
async function doReview() {
  if (!cur.value) return
  await api.reviewVuln(cur.value.id, review)
  ElMessage.success('已裁决')
  dialog.value = false
  await load()
}
async function del(id: string) {
  await api.deleteVuln(id)
  ElMessage.success('已删除')
  await load()
}
function sevType(s: string) {
  return { info: 'info', low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }[s] || 'info'
}
function fmt(t: string) {
  return t ? new Date(t).toLocaleString() : ''
}
onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center">
      <h2 class="page-title" style="margin: 0">漏洞复审</h2>
      <el-button @click="load">刷新</el-button>
    </div>
    <el-table :data="list" border style="margin-top: 16px" size="small">
      <el-table-column prop="vuln_type" label="类型" width="150" />
      <el-table-column label="级别" width="90">
        <template #default="{ row }">
          <el-tag :type="sevType(row.severity)">{{ row.severity }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="target_url" label="目标" width="240" />
      <el-table-column label="置信度" width="90">
        <template #default="{ row }">{{ (row.confidence * 100).toFixed(0) }}%</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column label="创建" width="160">
        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="170">
        <template #default="{ row }">
          <el-button size="small" @click="open(row)">复审</el-button>
          <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" title="漏洞详情 · 人工复审" width="660px">
      <el-descriptions :column="1" border v-if="cur">
        <el-descriptions-item label="类型">{{ cur.vuln_type }}</el-descriptions-item>
        <el-descriptions-item label="级别">{{ cur.severity }}</el-descriptions-item>
        <el-descriptions-item label="标题">{{ cur.title }}</el-descriptions-item>
        <el-descriptions-item label="目标">{{ cur.target_url }}</el-descriptions-item>
        <el-descriptions-item label="详情">{{ cur.detail }}</el-descriptions-item>
        <el-descriptions-item label="Payload"><pre>{{ cur.payload }}</pre></el-descriptions-item>
        <el-descriptions-item label="证据"><pre>{{ cur.evidence }}</pre></el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-select v-model="review.status" style="width: 130px; margin-right: 8px">
          <el-option label="通过" value="approved" />
          <el-option label="打回" value="rejected" />
          <el-option label="已提交" value="submitted" />
        </el-select>
        <el-input v-model="review.severity" placeholder="级别" style="width: 110px; margin-right: 8px" />
        <el-button type="primary" @click="doReview">提交裁决</el-button>
      </template>
    </el-dialog>
  </div>
</template>
