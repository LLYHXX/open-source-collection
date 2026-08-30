<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { zh, SEVERITY, VULN_STATUS, SEVERITY_TYPE } from '@/i18n/cn'

const list = ref<any[]>([])
const dialog = ref(false)
const cur = ref<any>(null)
const review = reactive({ status: 'approved', severity: '', reviewer_note: '' })

function sevText(s: string) { return (SEVERITY as any)[s] || zh(s) }
function statusText(s: string) { return (VULN_STATUS as any)[s] || zh(s) }
const SEVERITY_OPTIONS = [
  { label: '严重', value: 'critical' },
  { label: '高危', value: 'high' },
  { label: '中危', value: 'medium' },
  { label: '低危', value: 'low' },
  { label: '信息', value: 'info' },
]

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
function statusType(s: string) {
  return (
    {
      pending: 'info',
      ai_reviewed: 'primary',
      approved: 'success',
      submitted: 'success',
      rejected: 'danger',
    }[s] || 'info'
  )
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
    <el-table :data="list" border style="margin-top: 16px" size="small" stripe empty-text="暂无漏洞">
      <el-table-column label="严重级别" width="100" align="center">
        <template #default="{ row }">
          <span :class="`sev-tag sev-${row.severity || 'info'}`">{{ sevText(row.severity) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="vuln_type" label="漏洞类型" width="160" />
      <el-table-column prop="title" label="漏洞标题" show-overflow-tooltip />
      <el-table-column prop="target_url" label="目标地址" width="240" show-overflow-tooltip />
      <el-table-column label="置信度" width="110">
        <template #default="{ row }">
          <el-progress
            :percentage="Math.round((row.confidence || 0) * 100)"
            :stroke-width="8"
            :color="row.confidence >= 0.8 ? '#34d399' : row.confidence >= 0.6 ? '#fbbf24' : '#64748b'"
            style="width: 90px"
          />
        </template>
      </el-table-column>
      <el-table-column label="复审状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small" effect="dark">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
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

    <el-dialog v-model="dialog" title="漏洞详情 · 人工复审" width="700px">
      <el-descriptions :column="1" border v-if="cur" size="default">
        <el-descriptions-item label="漏洞类型">{{ cur.vuln_type }}</el-descriptions-item>
        <el-descriptions-item label="严重级别">
          <span :class="`sev-tag sev-${cur.severity || 'info'}`">{{ sevText(cur.severity) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="漏洞标题">{{ cur.title }}</el-descriptions-item>
        <el-descriptions-item label="目标地址">{{ cur.target_url }}</el-descriptions-item>
        <el-descriptions-item label="漏洞详情">{{ cur.detail }}</el-descriptions-item>
        <el-descriptions-item label="验证 Payload"><pre class="payload-block">{{ cur.payload }}</pre></el-descriptions-item>
        <el-descriptions-item label="复现证据"><pre class="payload-block">{{ cur.evidence }}</pre></el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-select v-model="review.status" style="width: 140px; margin-right: 8px">
          <el-option label="通过（入库）" value="approved" />
          <el-option label="打回修改" value="rejected" />
          <el-option label="已提交报告" value="submitted" />
        </el-select>
        <el-select v-model="review.severity" placeholder="级别（可选调整）" clearable style="width: 140px; margin-right: 8px">
          <el-option v-for="op in SEVERITY_OPTIONS" :key="op.value" :label="op.label" :value="op.value" />
        </el-select>
        <el-button type="primary" @click="doReview">提交裁决</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.payload-block {
  font-family: 'JetBrains Mono', Consolas, Monaco, monospace;
  background: rgba(255, 255, 255, 0.04);
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  color: #cbd5e1;
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.6;
  max-height: 220px;
  overflow: auto;
  margin: 0;
}
</style>
