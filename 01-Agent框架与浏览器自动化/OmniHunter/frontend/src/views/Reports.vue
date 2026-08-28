<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const templates = ref<any[]>([])
const tasks = ref<any[]>([])
const dialog = ref(false)
const editing = ref<any>(null)
const form = ref({ name: '', content: '', is_default: false })

// 生成报告
const genTaskId = ref('')
const genTemplateId = ref('')
const reportText = ref('')
const reportVisible = ref(false)

async function load() {
  templates.value = await api.listTemplates()
  tasks.value = await api.listTasks()
}
function openCreate() {
  editing.value = null
  form.value = { name: '', content: '', is_default: false }
  dialog.value = true
}
function openEdit(row: any) {
  editing.value = row.id
  form.value = { name: row.name, content: row.content, is_default: row.is_default }
  dialog.value = true
}
async function save() {
  if (!form.value.name) {
    ElMessage.warning('请填模板名')
    return
  }
  if (editing.value) {
    await api.updateTemplate(editing.value, form.value)
    ElMessage.success('已更新')
  } else {
    await api.createTemplate(form.value)
    ElMessage.success('已创建')
  }
  dialog.value = false
  await load()
}
async function del(id: string) {
  await ElMessageBox.confirm('确认删除该模板?', '提示', { type: 'warning' })
  await api.deleteTemplate(id)
  ElMessage.success('已删除')
  await load()
}
async function generate() {
  if (!genTaskId.value) {
    ElMessage.warning('请选择任务')
    return
  }
  const res = await api.generateReport(genTaskId.value, genTemplateId.value || undefined)
  reportText.value = res.data.report
  reportVisible.value = true
  ElMessage.success(res.message)
}
function copyReport() {
  navigator.clipboard.writeText(reportText.value)
  ElMessage.success('已复制到剪贴板')
}
onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center">
      <h2 class="page-title" style="margin: 0">漏洞报告</h2>
      <el-button type="primary" @click="openCreate">新建模板</el-button>
    </div>

    <el-card style="margin-top: 16px">
      <template #header>报告模板（支持自定义 markdown/jinja2）</template>
      <el-table :data="templates" border size="small">
        <el-table-column prop="name" label="模板名" min-width="160" />
        <el-table-column label="默认" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success">默认</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>生成报告</template>
      <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap">
        <el-select v-model="genTaskId" placeholder="选择任务" style="width: 280px">
          <el-option v-for="t in tasks" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-select v-model="genTemplateId" placeholder="模板（留空用默认）" clearable style="width: 220px">
          <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button type="primary" @click="generate">生成报告</el-button>
      </div>
    </el-card>

    <el-dialog v-model="dialog" :title="editing ? '编辑模板' : '新建模板'" width="720px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="模板名"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="form.is_default" />
        </el-form-item>
        <el-form-item label="模板内容">
          <el-input v-model="form.content" type="textarea" :rows="14"
            placeholder='jinja2/markdown。可用变量：task_name, generated_at, vuln_count, severity_summary, vulns(循环 v.title/v.severity/v.target_url/v.detail/v.payload/v.evidence...)' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reportVisible" title="生成的报告" width="800px">
      <el-input v-model="reportText" type="textarea" :rows="22" readonly />
      <template #footer>
        <el-button @click="copyReport">复制</el-button>
        <el-button type="primary" @click="reportVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>
