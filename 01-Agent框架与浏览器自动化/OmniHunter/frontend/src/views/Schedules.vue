<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const list = ref<any[]>([])
const dialog = ref(false)
const form = ref({
  name: '',
  cron_expr: '', // 如 "0 2 * * *" 每天2点；留空用间隔
  interval_minutes: 1440,
  deadline_days: 30,
  task_template: {
    mode: 'EduSRC',
    vuln_types:
      'sql_injection,rce,unauthorized_access,idor,file_upload,captcha_bypass,backdoor_compromised',
    source: 'manual',
    collect_method: 'auto',
    collect_query: '',
    manual_targets: '',
    max_pages: 3,
  },
})

async function load() {
  list.value = await api.listSchedules()
}
async function create() {
  if (!form.value.name) {
    ElMessage.warning('请填任务名')
    return
  }
  if (!form.value.cron_expr && !form.value.interval_minutes) {
    ElMessage.warning('cron 或间隔分钟至少填一项')
    return
  }
  await api.createSchedule(form.value)
  ElMessage.success('定时任务已创建，期限默认1月')
  dialog.value = false
  await load()
}
async function toggle(row: any) {
  await api.toggleSchedule(row.id)
  ElMessage.success(row.enabled ? '已停用' : '已启用')
  await load()
}
async function extend(row: any) {
  try {
    const { value } = await ElMessageBox.prompt('延期天数（延长到当前期限之后）', '延长期限', {
      inputType: 'number',
      inputValue: '30',
      inputValidator: (v: string) => Number(v) > 0 || '请输入正整数',
    })
    await api.extendSchedule(row.id, Number(value))
    ElMessage.success(`已延长 ${value} 天`)
    await load()
  } catch {
    /* 取消 */
  }
}
async function runNow(row: any) {
  await api.runScheduleNow(row.id)
  ElMessage.success('已触发一次执行')
}
async function del(row: any) {
  await ElMessageBox.confirm('确认删除该定时任务?', '提示', { type: 'warning' })
  await api.deleteSchedule(row.id)
  ElMessage.success('已删除')
  await load()
}
function fmt(d: string | null) {
  return d ? d.replace('T', ' ').slice(0, 19) : '-'
}
onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center">
      <h2 class="page-title" style="margin: 0">定时任务</h2>
      <el-button type="primary" @click="dialog = true">新建定时任务</el-button>
    </div>
    <p class="muted" style="margin-top: 8px">
      周期性启动→执行→关闭循环，期限默认1个月，到期自动停用；可延期或手动启停。
    </p>
    <el-table :data="list" border style="margin-top: 12px">
      <el-table-column prop="name" label="名称" min-width="160" />
      <el-table-column label="调度" width="160">
        <template #default="{ row }">
          {{ row.cron_expr ? 'cron: ' + row.cron_expr : '每 ' + row.interval_minutes + ' 分钟' }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.enabled ? 'success' : 'info'">
            {{ row.enabled ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="期限" width="170">
        <template #default="{ row }">{{ fmt(row.deadline) }}</template>
      </el-table-column>
      <el-table-column label="下次执行" width="170">
        <template #default="{ row }">{{ fmt(row.next_run) }}</template>
      </el-table-column>
      <el-table-column label="上次执行" width="170">
        <template #default="{ row }">{{ fmt(row.last_run) }}</template>
      </el-table-column>
      <el-table-column prop="run_count" label="次数" width="80" />
      <el-table-column label="操作" width="300">
        <template #default="{ row }">
          <el-button size="small" :type="row.enabled ? 'warning' : 'success'" @click="toggle(row)">
            {{ row.enabled ? '停用' : '启用' }}
          </el-button>
          <el-button size="small" @click="extend(row)">延期</el-button>
          <el-button size="small" type="primary" @click="runNow(row)">立即执行</el-button>
          <el-button size="small" type="danger" @click="del(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" title="新建定时任务" width="680px">
      <el-form :model="form" label-width="110px">
        <el-divider content-position="left">调度配置</el-divider>
        <el-form-item label="任务名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="Cron 表达式">
          <el-input v-model="form.cron_expr" placeholder='如 "0 2 * * *" 每天2点；留空用间隔' />
        </el-form-item>
        <el-form-item label="间隔(分钟)">
          <el-input-number v-model="form.interval_minutes" :min="1" />
          <span class="muted" style="margin-left: 8px">cron 留空时生效，默认1440(每日)</span>
        </el-form-item>
        <el-form-item label="期限(天)">
          <el-input-number v-model="form.deadline_days" :min="1" />
          <span class="muted" style="margin-left: 8px">默认30天，到期自动停用，可延期</span>
        </el-form-item>
        <el-divider content-position="left">任务模板（每次触发按此生成挖掘任务）</el-divider>
        <el-form-item label="任务模式">
          <el-select v-model="form.task_template.mode">
            <el-option label="EduSRC" value="EduSRC" />
            <el-option label="企业SRC" value="企业SRC" />
          </el-select>
        </el-form-item>
        <el-form-item label="漏洞类型">
          <el-input v-model="form.task_template.vuln_types" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="目标来源">
          <el-select v-model="form.task_template.source">
            <el-option label="手动清单" value="manual" />
            <el-option label="FOFA自动搜" value="fofa" />
            <el-option label="两者" value="both" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.task_template.source !== 'manual'" label="语法/意图">
          <el-input v-model="form.task_template.collect_query" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item v-if="form.task_template.source !== 'fofa'" label="手动清单">
          <el-input v-model="form.task_template.manual_targets" type="textarea" :rows="4" placeholder="每行一个 URL" />
        </el-form-item>
        <el-form-item label="最大页数">
          <el-input-number v-model="form.task_template.max_pages" :min="1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="create">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>
