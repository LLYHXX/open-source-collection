<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

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
  tasks.value = await api.listTasks()
}
async function create() {
  if (!form.value.name) {
    ElMessage.warning('请填任务名')
    return
  }
  await api.createTask(form.value)
  ElMessage.success('已创建')
  dialog.value = false
  await load()
}
async function start(id: string) {
  await api.startTask(id)
  ElMessage.success('已启动')
  await load()
}
async function del(id: string) {
  await ElMessageBox.confirm('确认删除该任务?', '提示', { type: 'warning' })
  await api.deleteTask(id)
  ElMessage.success('已删除')
  await load()
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
    }[s] || 'info'
  )
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
  border-radius: 8px;
  background: rgba(59, 130, 246, 0.07);
  border: 1px solid rgba(59, 130, 246, 0.18);
}
</style>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center">
      <h2 class="page-title" style="margin: 0">挖掘任务</h2>
      <el-button type="primary" @click="dialog = true">新建任务</el-button>
    </div>
    <el-table :data="tasks" border style="margin-top: 16px" @row-click="goDetail">
      <el-table-column prop="name" label="任务名" />
      <el-table-column label="模式" width="110">
        <template #default="{ row }">
          <el-tag :type="row.mode === 'engine' ? 'success' : 'info'" effect="dark" size="small">
            {{ row.mode === 'engine' ? '自研引擎' : row.mode }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="source" label="来源" width="110" />
      <el-table-column prop="collect_method" label="搜集方式" width="120" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" />
      <el-table-column label="操作" width="230">
        <template #default="{ row }">
          <el-button size="small" type="success" @click.stop="start(row.id)">启动</el-button>
          <el-button size="small" @click.stop="goDetail(row)">详情</el-button>
          <el-button size="small" type="danger" @click.stop="del(row.id)">删除</el-button>
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
            <el-option label="两者" value="both" />
            <el-option label="单站协作" value="single" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜集方式">
          <el-select v-model="form.collect_method">
            <el-option label="自动判断" value="auto" />
            <el-option label="FOFA语法" value="fofa_syntax" />
            <el-option label="自然语言意图" value="nl_intent" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.source !== 'manual'" label="语法/意图">
          <el-input
            v-model="form.collect_query"
            type="textarea"
            :rows="2"
            placeholder='如 body="管理" && org="China Education..." 或 "找高校统一身份认证系统"'
          />
        </el-form-item>
        <el-form-item v-if="form.source !== 'fofa'" label="手动清单">
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
