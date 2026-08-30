<script setup lang="ts">
import { computed, inject, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import { zh, TASK_SOURCE, COLLECT_METHOD } from '@/i18n/cn'

function sourceCn(s: string) {
  return (TASK_SOURCE as any)[s] || zh(s) || s
}
function collCn(m: string) {
  return (COLLECT_METHOD as any)[m] || zh(m) || m
}

const labels: any = inject('uiLabels', {
  isCyber: { value: false },
  status: {
    pending_approval: { cyber: 'PENDING APPR', full: '待审批' },
    rejected:         { cyber: 'REJECTED',     full: '已拒绝' },
    pending:          { cyber: 'QUEUED',       full: '待执行' },
    collecting:       { cyber: 'COLLECTING',   full: '收集中' },
    running:          { cyber: 'RUN',          full: '执行中' },
    review:           { cyber: 'REV',          full: '待复审' },
    done:             { cyber: 'DONE',         full: '完成' },
    failed:           { cyber: 'FAIL',         full: '失败' },
  },
  actions: {
    approve: { cyber: 'APPR', full: '批准' },
    reject:  { cyber: 'REJECT', full: '拒绝' },
  },
})
const isCyber = computed(() => labels?.isCyber?.value)
function L(obj: any) { return isCyber.value ? obj?.cyber : obj?.full }

const router = useRouter()
const tasks = ref<any[]>([])
const dialog = ref(false)
const form = ref({
  name: '',
  mode: 'engine',
  vuln_types:
    'sql_injection,rce,unauthorized_access,idor,file_upload,captcha_bypass,backdoor_compromised',
  source: 'manual',
  collect_method: 'auto',
  collect_query: '',
  manual_targets: '',
})

async function load() {
  try {
    const r = await api.listTasks()
    // 容错：如果后端返回对象而非数组（异常兜底 StandardResponse）
    tasks.value = Array.isArray(r) ? r : (r?.items || r?.data || [])
  } catch (e: any) {
    tasks.value = tasks.value || []
    ElMessage.error(
      (isCyber ? 'TASK_LOAD_FAIL: ' : '任务列表加载失败: ')
      + (e?.friendlyMsg || e?.response?.data?.message || e?.message || e),
    )
  }
}
async function create() {
  if (!form.value.name) {
    ElMessage.warning(isCyber ? 'NAME_REQ' : '请填任务名')
    return
  }
  try {
    const r: any = await api.createTask(form.value)
    if (r && r.success === false) {
      ElMessage.error(r?.message || (isCyber ? 'CREATE_FAIL' : '创建失败'))
      return
    }
    ElMessage.success(isCyber ? 'CREATED' : '已创建')
    dialog.value = false
    // 清空表单，避免重复提交残留值
    form.value.name = ''
    form.value.collect_query = ''
    form.value.manual_targets = ''
  } catch (e: any) {
    ElMessage.error(
      (isCyber ? 'CREATE_FAIL: ' : '创建失败: ')
      + (e?.friendlyMsg || e?.response?.data?.message || e?.message || e),
    )
    return
  }
  await load()
}
async function start(id: string) {
  try {
    const r: any = await api.startTask(id)
    if (r && r.success === false) {
      ElMessage.error(r?.message || (isCyber ? 'START_FAIL' : '启动失败'))
      await load()
      return
    }
    ElMessage.success(isCyber ? 'STARTED' : '已启动')
    await load()
  } catch (e: any) {
    ElMessage.error(
      (isCyber ? 'START_FAIL: ' : '启动失败: ')
      + (e?.friendlyMsg || e?.response?.data?.message || e?.message || e),
    )
    await load()
  }
}
async function approve(id: string) {
  try {
    await ElMessageBox.confirm(
      isCyber ? `REJECT TASK id=${id.slice(0,8)} ?` : '确认拒绝该 Miner 生成的任务？拒绝后将标记 rejected 不再可启动。',
      L(labels.actions.reject) + ' × 1',
      { type: 'warning', confirmButtonText: isCyber ? 'REJECT' : '确认拒绝' },
    )
    await api.approveTask(id)
    ElMessage.success(isCyber ? 'APPR · STARTED' : '已批准并启动')
    await load()
  } catch (e: any) {
    if (e === 'cancel' || e === 'close') return
    ElMessage.error(
      (isCyber ? 'APPR_FAIL: ' : '批准失败: ')
      + (e?.friendlyMsg || e?.response?.data?.message || e?.message || e),
    )
    await load()
  }
}
async function reject(id: string) {
  try {
    await ElMessageBox.confirm(
      isCyber ? `REJECT TASK id=${id.slice(0,8)} ?` : '确认拒绝该 Miner 生成的任务？拒绝后将标记 rejected 不再可启动。',
      L(labels.actions.reject) + ' × 1',
      { type: 'warning', confirmButtonText: isCyber ? 'REJECT' : '确认拒绝' },
    )
  } catch { return }
  try {
    await api.rejectTask(id)
    ElMessage.success(isCyber ? 'REJECTED' : '已拒绝')
    await load()
  } catch (e: any) {
    ElMessage.error(
      (isCyber ? 'REJECT_FAIL: ' : '拒绝失败: ')
      + (e?.friendlyMsg || e?.response?.data?.message || e?.message || e),
    )
  }
}
async function del(id: string) {
  try {
    await ElMessageBox.confirm(
      isCyber ? `PURGE TASK id=${id.slice(0,8)} ?` : '确认删除该任务?',
      isCyber ? 'PURGE' : '提示',
      { type: 'warning', confirmButtonText: isCyber ? 'PURGE' : '删除', cancelButtonText: isCyber ? 'CANCEL' : '取消' },
    )
  } catch { return }
  try {
    await api.deleteTask(id)
    ElMessage.success(isCyber ? 'PURGED' : '已删除')
    await load()
  } catch (e: any) {
    ElMessage.error(
      (isCyber ? 'PURGE_FAIL: ' : '删除失败: ')
      + (e?.friendlyMsg || e?.response?.data?.message || e?.message || e),
    )
  }
}
function goDetail(row: any) {
  router.push(`/tasks/${row.id}`)
}
function statusType(s: string) {
  return (
    {
      pending: 'info',
      collecting: 'warning',
      running: 'warning',
      review: 'primary',
      done: 'success',
      failed: 'danger',
      pending_approval: 'warning',
      rejected: 'danger',
    }[s] || 'info'
  )
}
function statusLabel(s: string) {
  const m = labels.status?.[s]
  if (m) return L(m)
  return s
}
onMounted(load)
</script>

<style scoped>
.mode-tip {
  width: 100%;
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.7;
  color: #8b94a8;
  padding: 8px 12px;
  border-radius: var(--radius-card, 8px);
  background: rgba(59, 130, 246, 0.07);
  border: 1px solid rgba(59, 130, 246, 0.18);
}
:global([data-theme='cyber']) .mode-tip,
:global([data-theme='mono']) .mode-tip {
  border-radius: 0;
  background: var(--bg-1, #0a0c10);
  border: 1px solid var(--border-1, #1a1d24);
  color: var(--text-2, #9fb0c7);
  font-family: var(--font-mono, Consolas, monospace);
}
</style>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center">
      <h2 class="page-title" style="margin: 0">{{ isCyber ? 'TASKS · QUEUE' : '挖掘任务' }}</h2>
      <el-button type="primary" @click="dialog = true">{{ isCyber ? 'NEW · TASK' : '新建任务' }}</el-button>
    </div>
    <el-table :data="tasks" border style="margin-top: 16px" @row-click="goDetail" stripe empty-text="暂无任务">
      <el-table-column prop="name" :label="isCyber ? 'NAME' : '任务名称'" show-overflow-tooltip />
      <el-table-column :label="isCyber ? 'MODE' : '任务模式'" width="120">
        <template #default="{ row }">
          <el-tag :type="row.mode === 'engine' ? 'success' : 'info'" effect="dark" size="small">
            {{ isCyber ? (row.mode === 'engine' ? 'ENGINE' : row.mode) : (row.mode === 'engine' ? '自研引擎' : zh(row.mode) || row.mode) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="isCyber ? 'SRC' : '目标来源'" width="130">
        <template #default="{ row }">
          <span v-if="isCyber">{{ row.source }}</span>
          <span v-else>{{ sourceCn(row.source) }}</span>
        </template>
      </el-table-column>
      <el-table-column :label="isCyber ? 'COLL' : '搜集方式'" width="130">
        <template #default="{ row }">
          <span v-if="isCyber">{{ row.collect_method }}</span>
          <span v-else>{{ collCn(row.collect_method) }}</span>
        </template>
      </el-table-column>
      <el-table-column :label="isCyber ? 'STAT' : '状态'" width="140">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" :label="isCyber ? 'CREATED_AT' : '创建时间'" />
      <el-table-column :label="isCyber ? 'ACTIONS' : '操作'" width="320">
        <template #default="{ row }">
          <template v-if="row.status === 'pending_approval'">
            <el-button size="small" type="success" @click.stop="approve(row.id)">{{ L(labels.actions.approve) }}</el-button>
            <el-button size="small" type="warning" plain @click.stop="reject(row.id)">{{ L(labels.actions.reject) }}</el-button>
          </template>
          <template v-else-if="row.status === 'rejected'">
            <el-button size="small" disabled>{{ isCyber ? 'REJECTED' : '已拒绝' }}</el-button>
          </template>
          <template v-else>
            <el-button size="small" type="success" @click.stop="start(row.id)">{{ isCyber ? 'START' : '启动' }}</el-button>
          </template>
          <el-button size="small" @click.stop="goDetail(row)">{{ isCyber ? 'DETAIL' : '详情' }}</el-button>
          <el-button size="small" type="danger" @click.stop="del(row.id)">{{ isCyber ? 'PURGE' : '删除' }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" title="新建挖掘任务" width="660px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="任务名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="任务模式">
          <el-radio-group v-model="form.mode">
            <el-radio-button value="engine">自研引擎</el-radio-button>
            <el-radio-button value="EduSRC">EduSRC</el-radio-button>
            <el-radio-button value="企业SRC">企业SRC</el-radio-button>
          </el-radio-group>
          <div v-if="form.mode === 'engine'" class="mode-tip">
            全自动流水线：FOFA/清单收集 → 引擎确定性检测 → 独立复现 → CVSS 定级，
            全程不依赖大模型质量，最低配 LLM 即可运行。
          </div>
          <div v-else class="mode-tip">
            多 Agent 流水线：Collector → Recon → Worker → Verifier → Reviewer，LLM 参与 ReAct 决策。
          </div>
        </el-form-item>
        <el-form-item label="漏洞类型">
          <el-input v-model="form.vuln_types" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="目标来源">
          <el-select v-model="form.source">
            <el-option label="手动清单" value="manual" />
            <el-option label="FOFA自动搜" value="fofa" />
            <el-option label="360 Quake" value="quake" />
            <el-option label="Hunter鹰图" value="hunter" />
            <el-option label="ZoomEye" value="zoomeye" />
            <el-option label="Shodan" value="shodan" />
            <el-option label="Censys" value="censys" />
            <el-option label="全平台并发" value="all" />
            <el-option label="手动+FOFA" value="both" />
            <el-option label="单站协作" value="single" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜集方式">
          <el-select v-model="form.collect_method">
            <el-option label="自动判断" value="auto" />
            <el-option label="平台语法" value="fofa_syntax" />
            <el-option label="自然语言意图" value="nl_intent" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.source !== 'manual'" label="语法/意图">
          <el-input
            v-model="form.collect_query"
            type="textarea"
            :rows="2"
            placeholder='平台语法如 title="后台管理"，或自然语言如 "找高校统一身份认证系统"'
          />
        </el-form-item>
        <el-form-item v-if="['manual', 'single', 'both'].includes(form.source)" label="手动清单">
          <el-input v-model="form.manual_targets" type="textarea" :rows="4" placeholder="每行一个 URL" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="create">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>
