<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const targetUrl = ref('')
const pocText = ref('')
const matchRegex = ref('')
const taskId = ref('')
const tasks = ref<any[]>([])
const running = ref(false)
const result = ref<any>(null)

onMounted(async () => {
  try {
    tasks.value = await api.listTasks()
  } catch {
    /* 任务列表加载失败不阻塞页面 */
  }
})

async function run() {
  if (!targetUrl.value.trim()) return ElMessage.warning('请输入目标 URL')
  if (!pocText.value.trim()) return ElMessage.warning('请输入 POC 描述（URL 或 curl 命令）')
  running.value = true
  result.value = null
  try {
    const res: any = await api.pocExpand({
      target_url: targetUrl.value.trim(),
      poc_text: pocText.value,
      match_regex: matchRegex.value,
      task_id: taskId.value,
    })
    if (!res.success) {
      ElMessage.error(res.message)
      return
    }
    result.value = res.data
    ElMessage.success(res.message)
  } catch (e: any) {
    ElMessage.error('扩展分析失败: ' + (e.response?.data?.detail || e.message || e))
  } finally {
    running.value = false
  }
}

function sevType(hit: boolean) {
  return hit ? 'danger' : 'info'
}
</script>

<template>
  <div>
    <h2 class="page-title">持续挖掘（POC 扩展分析）</h2>
    <p class="muted">
      输入已知 POC（URL 或 curl 命令），自动生成关联变体（后缀 / 前缀 / 参数值 / 编码）并逐个确定性复验；
      命中响应继续提取子目标 URL 与凭据回灌情报库。引擎扫描发现信息泄露漏洞时同样自动触发递归深挖（深度与总量受限）。
    </p>

    <el-card style="margin-bottom: 16px">
      <template #header>POC 扩展分析</template>
      <el-form label-width="90px">
        <el-form-item label="目标 URL">
          <el-input v-model="targetUrl" placeholder="http://target.com（用于 SSRF 校验与子目标过滤）" />
        </el-form-item>
        <el-form-item label="关联任务">
          <el-select v-model="taskId" placeholder="可选：命中漏洞自动入库到该任务" clearable filterable style="width: 100%">
            <el-option v-for="t in tasks" :key="t.id" :label="t.name || t.id" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="POC 描述">
          <el-input
            v-model="pocText" type="textarea" :rows="4"
            placeholder="curl 'http://target.com/config.bak'  或直接粘贴含 http(s):// 的 URL"
          />
        </el-form-item>
        <el-form-item label="命中正则">
          <el-input v-model="matchRegex" placeholder="响应命中特征（如 root:|password\s*=），留空只报可达性" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="running" @click="run">
            {{ running ? '复验中…' : '开始扩展分析' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <template v-if="result">
      <el-card style="margin-bottom: 16px">
        <template #header>
          原始 POC 复验
          <el-tag :type="sevType(result.original_hit?.hit)" size="small" style="margin-left: 8px">
            {{ result.original_hit?.hit ? '命中' : result.original_hit?.reachable ? '可达未命中' : '不可达' }}
          </el-tag>
        </template>
        <p class="muted" style="margin: 0 0 8px">
          {{ result.original_hit?.method }} {{ result.original_hit?.url }}
          — HTTP {{ result.original_hit?.status }} · {{ result.original_hit?.elapsed_ms }}ms
        </p>
        <p v-if="result.original_hit?.snippet" class="muted snippet">{{ result.original_hit.snippet }}</p>
      </el-card>

      <el-card style="margin-bottom: 16px">
        <template #header>
          变体复验结果（共 {{ result.variants_total }} 个，确认命中 {{ result.confirmed?.length || 0 }} 个）
        </template>
        <el-table :data="result.variants" border size="small">
          <el-table-column label="命中" width="70">
            <template #default="{ row }">
              <el-tag :type="sevType(row.hit)" size="small">{{ row.hit ? '命中' : '—' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="HTTP" width="70" />
          <el-table-column prop="method" label="方法" width="70" />
          <el-table-column prop="url" label="变体 URL" show-overflow-tooltip min-width="260" />
          <el-table-column prop="note" label="变体说明" width="150" show-overflow-tooltip />
          <el-table-column prop="snippet" label="响应片段" show-overflow-tooltip min-width="200" />
        </el-table>
      </el-card>

      <el-card>
        <template #header>持续挖掘产出（已回灌情报库）</template>
        <template v-if="result.followups?.urls?.length || result.followups?.creds?.length || result.followups?.private_ips?.length">
          <div v-if="result.followups.urls?.length" style="margin-bottom: 12px">
            <b>子目标 URL（kind=leak）</b>
            <div v-for="u in result.followups.urls" :key="u" class="muted mono">{{ u }}</div>
          </div>
          <div v-if="result.followups.creds?.length" style="margin-bottom: 12px">
            <b>凭据（kind=credential，已脱敏）</b>
            <div v-for="(c, i) in result.followups.creds" :key="i" class="muted mono">
              {{ c.name }} = {{ c.masked }}
            </div>
          </div>
          <div v-if="result.followups.private_ips?.length">
            <b>内网 IP</b>
            <div v-for="(ip, i) in result.followups.private_ips" :key="i" class="muted mono">{{ ip }}</div>
          </div>
        </template>
        <p v-else class="muted" style="margin: 0">本次响应未提取到可跟进的子目标。</p>
      </el-card>
    </template>
  </div>
</template>

<style scoped>
.snippet {
  font-family: monospace;
  background: rgba(255, 255, 255, 0.04);
  padding: 8px;
  border-radius: 6px;
  word-break: break-all;
}
.mono {
  font-family: monospace;
  word-break: break-all;
}
</style>
