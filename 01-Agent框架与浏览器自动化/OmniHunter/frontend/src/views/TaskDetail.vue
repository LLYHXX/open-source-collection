<script setup lang="ts">
import { computed, inject, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const labels: any = inject('uiLabels', {
  isCyber: { value: false },
  status: {
    pending_approval: { cyber: 'PENDING APPR', full: '待审批' },
    rejected:         { cyber: 'REJECTED',     full: '已拒绝' },
  },
  actions: {
    approve: { cyber: 'APPR', full: '批准' },
    reject:  { cyber: 'REJECT', full: '拒绝' },
  },
})
const isCyber = computed(() => labels?.isCyber?.value)
function L(obj: any) { return isCyber.value ? obj?.cyber : obj?.full }
function statusLabel(s: string) {
  const m = labels.status?.[s]
  if (m) return L(m)
  return s
}
function statusType(s: string) {
  return {
    pending: 'info', collecting: 'warning', running: 'warning', review: 'primary',
    done: 'success', failed: 'danger',
    pending_approval: 'warning', rejected: 'danger',
  }[s] || 'info'
}

const route = useRoute()
const router = useRouter()
const id = route.params.id as string

const task = ref<any>(null)
const vulns = ref<any[]>([])
const messages = ref<any[]>([])
const singleUrl = ref('')
const vulnDialog = ref(false)
const cur = ref<any>(null)
const review = reactive({ status: 'approved', severity: '', reviewer_note: '' })
const refreshTimer = ref<ReturnType<typeof setTimeout> | null>(null)

async function load() {
  task.value = await api.getTask(id)
  vulns.value = await api.listVulns(id)
  const runs = await api.listRuns(id)
  if (runs.length) messages.value = await api.listMessages(runs[0].id)
}
async function start() {
  await api.startTask(id)
  ElMessage.success(isCyber ? 'STARTED' : '已启动')
  if (refreshTimer.value) clearTimeout(refreshTimer.value)
  refreshTimer.value = setTimeout(load, 1200)
}
async function approve() {
  await api.approveTask(id)
  ElMessage.success(isCyber ? 'APPR · STARTED' : '已批准并启动')
  if (refreshTimer.value) clearTimeout(refreshTimer.value)
  refreshTimer.value = setTimeout(load, 1200)
}
async function reject() {
  try {
    await ElMessageBox.confirm(
      isCyber ? `REJECT TASK id=${id.slice(0,8)} ?` : '确认拒绝该 Miner 生成的任务？拒绝后将标记 rejected 不再可启动。',
      L(labels.actions.reject) + ' × 1',
      { type: 'warning', confirmButtonText: isCyber ? 'REJECT' : '确认拒绝' },
    )
    await api.rejectTask(id)
    ElMessage.success(isCyber ? 'REJECTED' : '已拒绝')
    if (refreshTimer.value) clearTimeout(refreshTimer.value)
    refreshTimer.value = setTimeout(load, 1200)
  } catch {}
}
async function startSingle() {
  if (!singleUrl.value) return
  await api.startSingle(id, singleUrl.value)
  ElMessage.success(isCyber ? 'SINGLE · STARTED' : '已启动')
  if (refreshTimer.value) clearTimeout(refreshTimer.value)
  refreshTimer.value = setTimeout(load, 1200)
}
function openVuln(v: any) {
  cur.value = v
  review.severity = v.severity
  review.status = 'approved'
  vulnDialog.value = true
}
async function doReview() {
  if (!cur.value) return
  await api.reviewVuln(cur.value.id, review)
  ElMessage.success(isCyber ? 'VERDICT · WRITTEN' : '已裁决')
  vulnDialog.value = false
  await load()
}
function back() {
  router.back()
}
function sevType(s: string) {
  return { info: 'info', low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }[s] || 'info'
}
function fmt(t: string) {
  return t ? new Date(t).toLocaleTimeString() : ''
}
onMounted(load)
onUnmounted(() => {
  if (refreshTimer.value) clearTimeout(refreshTimer.value)
})
</script>

<template>
  <div v-if="task">
    <el-page-header @back="back" :content="task.task.name" />
    <el-descriptions :column="3" border style="margin-top: 16px">
      <el-descriptions-item :label="isCyber ? 'STAT' : '状态'">
        <el-tag :type="statusType(task.task.status)">{{ statusLabel(task.task.status) }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item :label="isCyber ? 'TARGETS' : '目标数'">{{ task.targets }}</el-descriptions-item>
      <el-descriptions-item :label="isCyber ? 'VULNS' : '漏洞数'">{{ task.vulns }}</el-descriptions-item>
      <el-descriptions-item :label="isCyber ? 'PENDING_REV' : '待复审'">{{ task.pending_vulns }}</el-descriptions-item>
      <el-descriptions-item :label="isCyber ? 'SRC' : '来源'">{{ task.task.source }}</el-descriptions-item>
      <el-descriptions-item :label="isCyber ? 'CREATED_AT' : '创建时间'">{{ task.task.created_at }}</el-descriptions-item>
    </el-descriptions>

    <div style="margin: 16px 0; display:flex; flex-wrap:wrap; gap:8px; align-items:center;">
      <template v-if="task.task.status === 'pending_approval'">
        <el-button type="success" @click="approve">{{ L(labels.actions.approve) }} · {{ isCyber ? 'START' : '并启动流水线' }}</el-button>
        <el-button type="warning" plain @click="reject">{{ L(labels.actions.reject) }}</el-button>
      </template>
      <template v-else-if="task.task.status === 'rejected'">
        <el-button disabled type="warning" plain>{{ isCyber ? 'REJECTED' : '已拒绝 · 无法启动' }}</el-button>
      </template>
      <template v-else>
        <el-button type="success" @click="start">{{ isCyber ? 'PIPELINE · START' : '启动流水线' }}</el-button>
      </template>
      <el-input v-model="singleUrl" :placeholder="isCyber ? 'SINGLE-SITE URL' : '单站协作 URL'" style="width: 320px; margin: 0 8px" />
      <el-button @click="startSingle">{{ isCyber ? 'SINGLE-SITE · BROWSER' : '浏览器单站协作' }}</el-button>
      <el-button @click="load">{{ isCyber ? 'REFRESH' : '刷新' }}</el-button>
    </div>

    <el-tabs>
      <el-tab-pane label="漏洞结果">
        <el-table :data="vulns" border size="small">
          <el-table-column prop="vuln_type" label="类型" width="150" />
          <el-table-column label="级别" width="90">
            <template #default="{ row }">
              <el-tag :type="sevType(row.severity)">{{ row.severity }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="标题" />
          <el-table-column label="置信度" width="90">
            <template #default="{ row }">{{ (row.confidence * 100).toFixed(0) }}%</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="120" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" @click="openVuln(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="Agent 事件流">
        <div
          class="mono"
          style="max-height: 540px; overflow: auto; background: #0d1117; color: #c9d1d9; padding: 12px; border-radius: 6px"
        >
          <div v-if="!messages.length" class="muted">NO_DATA · EMPTY_SET</div>
          <div v-for="m in messages" :key="m.id" style="margin-bottom: 8px">
            <span style="color: #8b949e">[{{ fmt(m.created_at) }}] {{ m.role }} / {{ m.level }}</span>
            <span v-if="m.tool" style="color: #79c0ff"> · {{ m.tool }}</span>
            <div style="margin-left: 12px">{{ m.content }}</div>
            <pre v-if="m.tool_result" style="color: #8b9499; white-space: pre-wrap; margin: 4px 0 0 12px">{{ m.tool_result }}</pre>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="vulnDialog" title="漏洞详情 · 人工复审" width="660px">
      <el-descriptions :column="1" border v-if="cur">
        <el-descriptions-item label="类型">{{ cur.vuln_type }}</el-descriptions-item>
        <el-descriptions-item label="级别">{{ cur.severity }}</el-descriptions-item>
        <el-descriptions-item label="标题">{{ cur.title }}</el-descriptions-item>
        <el-descriptions-item label="详情">{{ cur.detail }}</el-descriptions-item>
        <el-descriptions-item label="Payload"><pre>{{ cur.payload }}</pre></el-descriptions-item>
        <el-descriptions-item label="证据"><pre>{{ cur.evidence }}</pre></el-descriptions-item>
        <el-descriptions-item label="置信度">{{ cur.confidence }}</el-descriptions-item>
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
