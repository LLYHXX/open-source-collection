<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Close, Check, Lightning } from '@element-plus/icons-vue'
import { api } from '@/api'
import { zh, MINER_STATUS_TAG, MINER_KIND } from '@/i18n/cn'

// ============================================================
// Tab 1: POC 扩展分析（保留 + 全中文文案）
// ============================================================
const targetUrl = ref('')
const pocText = ref('')
const matchRegex = ref('')
const taskId = ref('')
const tasks = ref<any[]>([])
const running = ref(false)
const result = ref<any>(null)

// ============================================================
// Tab 3: 单站协作（权限发现专项）
// ============================================================
const collab = reactive({
  taskId: '',
  url: '',
  adminCookie: '',
  userCookie: '',
  user2Cookie: '',
  anonProbe: true,
  enableAttacker: true,
})
const collabRunning = ref(false)

async function startCollab() {
  if (!collab.taskId) { ElMessage.warning('请选择关联任务'); return }
  if (!collab.url.trim()) { ElMessage.warning('请输入目标 URL'); return }
  if (!collab.userCookie && !collab.adminCookie) {
    ElMessage.warning('至少需要填写一个身份会话 Cookie（user 或 admin）才能跑权限矩阵')
    return
  }
  try {
    await ElMessageBox.confirm(
      '将启动单站协作流水线：\n' +
      ' SiteProfiler 资产收集 → Modeler 业务建模\n' +
      ' → PermissionAgent 权限发现专项（5 类权限 + 权限矩阵）\n' +
      (collab.enableAttacker ? ' → Attacker 变异攻击\n' : '') +
      ' → Verifier 独立复现 → Reviewer 入库\n\n' +
      '是否继续？',
      '启动单站协作',
      { type: 'warning', confirmButtonText: '确认启动', cancelButtonText: '取消' },
    )
  } catch { return /* 用户取消 */ }

  collabRunning.value = true
  try {
    const r: any = await api.startCollab(collab.taskId, collab.url.trim(), {
      admin_cookie: collab.adminCookie.trim() || undefined,
      user_cookie: collab.userCookie.trim() || undefined,
      user2_cookie: collab.user2Cookie.trim() || undefined,
      anon_probe: collab.anonProbe,
      enable_attacker: collab.enableAttacker,
    })
    ElMessage.success(r?.message || '已启动单站协作，可在「任务详情」查看进度')
    // 跳转到任务详情
    setTimeout(() => {
      window.location.hash = `#/tasks/${collab.taskId}`
    }, 800)
  } catch (e: any) {
    ElMessage.error(e?.friendlyMsg || '启动失败: ' + (e.message || e))
  } finally {
    collabRunning.value = false
  }
}

onMounted(async () => {
  try {
    tasks.value = await api.listTasks()
  } catch { /* 不阻塞页面 */ }
  // 切换到 Miner 候选池时自动刷一次
})

async function runPoc() {
  if (!targetUrl.value.trim()) { ElMessage.warning('请输入目标 URL'); return }
  if (!pocText.value.trim()) { ElMessage.warning('请输入 POC 描述（URL 或 curl 命令）'); return }
  running.value = true
  result.value = null
  try {
    const res: any = await api.pocExpand({
      target_url: targetUrl.value.trim(),
      poc_text: pocText.value,
      match_regex: matchRegex.value,
      task_id: taskId.value,
    })
    result.value = res.data
    ElMessage.success(res.message || '扩展分析完成')
  } catch (e: any) {
    ElMessage.error(e?.friendlyMsg || ('扩展分析失败: ' + (e.response?.data?.detail || e.message || e)))
  } finally {
    running.value = false
  }
}

function sevType(hit: boolean) {
  return hit ? 'danger' : 'info'
}

// ============================================================
// Tab 2: Miner 候选池（新增）
// ============================================================
const activeTab = ref('poc')
const candLoading = ref(false)
const candItems = ref<any[]>([])
const candTotal = ref(0)
const candSelected = ref<any[]>([])
const candFilters = reactive({
  status: 'pending',
  page: 1,
  page_size: 20,
  keyword: '',
})
const STATUS_OPTIONS = [
  { label: '待审核', value: 'pending' },
  { label: '已批准入库', value: 'approved' },
  { label: '已拒绝', value: 'rejected' },
  { label: '已跳过（越权）', value: 'skipped' },
]

async function loadCandidates() {
  candLoading.value = true
  try {
    const r: any = await api.listMinerCandidates(
      candFilters.status,
      candFilters.page,
      candFilters.page_size,
      candFilters.keyword.trim()
    )
    if (r?.success && r.data) {
      candItems.value = r.data.items || []
      candTotal.value = Number(r.data.total) || 0
    } else {
      candItems.value = []
      candTotal.value = 0
      ElMessage.warning(r?.message || '候选列表加载失败')
    }
  } catch (e: any) {
    candItems.value = []
    candTotal.value = 0
    ElMessage.error(e?.friendlyMsg || ('候选列表加载失败: ' + (e.message || e)))
  } finally {
    candLoading.value = false
  }
}

function onTabChange(tab: string) {
  activeTab.value = tab
  if (tab === 'miner' && candItems.value.length === 0) {
    loadCandidates()
  }
}

function onSelectionChange(rows: any[]) {
  candSelected.value = rows
}

function statusTagType(s: string) {
  return (MINER_STATUS_TAG as any)[s] || 'info'
}
function kindCn(k: string) {
  return (MINER_KIND as any)[k] || zh(k)
}
function statusCn(s: string) {
  return zh(s)
}

async function doApprove() {
  const ids = candSelected.value.map((x: any) => String(x.id)).filter(Boolean)
  if (!ids.length) { ElMessage.warning('请先勾选要批准的候选'); return }
  try {
    await ElMessageBox.confirm(
      `批准并入库 ${ids.length} 条候选？写入后可在「情报库 / 记忆管理」中检索与复用。`,
      '批量批准 × ' + ids.length,
      { type: 'success', confirmButtonText: '确认批准', cancelButtonText: '取消' }
    )
    const r: any = await api.approveMinerCandidates(ids)
    ElMessage.success(r?.message || `已写入 ${ids.length} 条`)
    candSelected.value = []
    await loadCandidates()
  } catch { /* 用户取消 */ }
}

async function doReject() {
  const ids = candSelected.value.map((x: any) => String(x.id)).filter(Boolean)
  if (!ids.length) { ElMessage.warning('请先勾选要拒绝的候选'); return }
  try {
    await ElMessageBox.confirm(
      `拒绝 ${ids.length} 条候选？被拒条目后续将不再出现在待审核列表。`,
      '批量拒绝 × ' + ids.length,
      { type: 'warning', confirmButtonText: '确认拒绝', cancelButtonText: '取消' }
    )
    const r: any = await api.rejectMinerCandidates(ids)
    ElMessage.success(r?.message || `已拒绝 ${ids.length} 条`)
    candSelected.value = []
    await loadCandidates()
  } catch { /* 用户取消 */ }
}

function selCountText() {
  const sel = candSelected.value.length
  const tot = candTotal.value
  return sel ? `已选 ${sel} 项 / 合计 ${tot} 项` : `合计 ${tot} 项`
}

const emptyCandText = computed(() => {
  if (candLoading.value) return '加载中…'
  if (candFilters.keyword.trim()) return '没有匹配的候选（可调整关键词或状态筛选）'
  const lab = STATUS_OPTIONS.find((x) => x.value === candFilters.status)?.label || ''
  return lab ? `当前没有「${lab}」的候选` : '暂无数据'
})
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <h2 class="page-title">持续挖掘</h2>
        <p class="muted" style="margin: 4px 0 0 0; line-height: 1.8">
          左侧：POC 扩展分析（已知 POC → 变体复验 → 子目标回灌情报库）；
          右侧：Miner 候选池审批（三 Loop 产出的候选情报，人工审核一键入库）。
        </p>
      </div>
      <div class="actions" v-if="activeTab === 'miner'">
        <el-input
          v-model="candFilters.keyword"
          placeholder="按关键值 / 备注 / 类型搜索"
          clearable
          style="width: 260px"
          @keyup.enter="candFilters.page = 1; loadCandidates()"
          @clear="candFilters.page = 1; loadCandidates()"
        />
        <el-button @click="candFilters.page = 1; loadCandidates()">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
        <el-button
          type="warning" plain
          :disabled="!candSelected.length"
          @click="doReject"
        >
          <el-icon><Close /></el-icon> 批量拒绝（{{ candSelected.length }}）
        </el-button>
        <el-button
          type="success"
          :disabled="!candSelected.length"
          @click="doApprove"
        >
          <el-icon><Check /></el-icon> 批量批准入库（{{ candSelected.length }}）
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" type="card" @tab-change="onTabChange">
      <!-- ================= Tab 1: POC 扩展分析 ================= -->
      <el-tab-pane label="POC 扩展分析" name="poc">
        <el-card style="margin-bottom: 16px">
          <template #header>参数配置</template>
          <el-form label-width="100px">
            <el-form-item label="目标 URL">
              <el-input
                v-model="targetUrl"
                placeholder="如 http://target.com（用于 SSRF 校验与子目标归属过滤）"
              />
            </el-form-item>
            <el-form-item label="关联任务">
              <el-select
                v-model="taskId"
                placeholder="可选：命中后漏洞结果自动入库到该任务"
                clearable filterable style="width: 100%"
              >
                <el-option v-for="t in tasks" :key="t.id"
                  :label="(t.name || '') + '  ·  ' + (t.id || '').slice(0, 8)"
                  :value="t.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="POC 描述">
              <el-input
                v-model="pocText" type="textarea" :rows="4"
                placeholder="curl 'http://target.com/config.bak' 或直接粘贴含 http(s):// 的 URL 行"
              />
            </el-form-item>
            <el-form-item label="命中正则">
              <el-input
                v-model="matchRegex"
                placeholder="可选：响应命中特征（如 root:|password\s*=），留空仅报可达性"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="running" @click="runPoc">
                {{ running ? '扩展与复验中…' : '开始扩展分析' }}
              </el-button>
              <span class="muted" style="margin-left: 10px">
                最多 40 个变体，每个变体最多 10 秒超时；命中后自动抽取子 URL 与凭据回灌情报库。
              </span>
            </el-form-item>
          </el-form>
        </el-card>

        <template v-if="result">
          <el-card style="margin-bottom: 16px">
            <template #header>
              原始 POC 复验
              <el-tag :type="sevType(result.original_hit?.hit)" size="small" effect="dark" style="margin-left: 8px">
                {{ result.original_hit?.hit ? '命中' : (result.original_hit?.reachable ? '可达未命中' : '不可达') }}
              </el-tag>
            </template>
            <p class="muted" style="margin: 0 0 8px">
              <span class="mono">{{ result.original_hit?.method }}</span>
              &nbsp;{{ result.original_hit?.url }}
              &nbsp;— HTTP <b>{{ result.original_hit?.status }}</b>
              &nbsp;· 耗时 {{ result.original_hit?.elapsed_ms }}ms
            </p>
            <p v-if="result.original_hit?.snippet" class="muted snippet">{{ result.original_hit.snippet }}</p>
          </el-card>

          <el-card style="margin-bottom: 16px">
            <template #header>
              变体复验结果（共 {{ result.variants_total }} 个，确认命中 {{ result.confirmed?.length || 0 }} 个）
            </template>
            <el-table :data="result.variants" border size="small" stripe empty-text="暂无变体数据">
              <el-table-column label="命中" width="70" align="center">
                <template #default="{ row }">
                  <el-tag :type="sevType(row.hit)" size="small" effect="dark">
                    {{ row.hit ? '命中' : '—' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态码" width="70" align="center" />
              <el-table-column prop="method" label="方法" width="70" align="center" />
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
                <div v-for="u in result.followups.urls" :key="u" class="muted mono mono-block">{{ u }}</div>
              </div>
              <div v-if="result.followups.creds?.length" style="margin-bottom: 12px">
                <b>凭据（kind=credential，已脱敏显示）</b>
                <div v-for="(c, i) in result.followups.creds" :key="i" class="muted mono mono-block">
                  {{ c.name }} = {{ c.masked }}
                </div>
              </div>
              <div v-if="result.followups.private_ips?.length">
                <b>内网 IP（越权提示，不会自动发起探测）</b>
                <div v-for="(ip, i) in result.followups.private_ips" :key="i" class="muted mono mono-block">{{ ip }}</div>
              </div>
            </template>
            <p v-else class="muted" style="margin: 0">本次响应未提取到可跟进的子目标或凭据。</p>
          </el-card>
        </template>
      </el-tab-pane>

      <!-- ================= Tab 2: Miner 候选池 ================= -->
      <el-tab-pane label="Miner 候选池审批" name="miner">
        <!-- 顶部筛选条 -->
        <div class="filter-wrap-card" style="margin-bottom: 14px">
          <el-form :inline="true" size="default" class="filter-form-miner">
            <el-form-item label="状态">
              <el-radio-group v-model="candFilters.status" @change="candFilters.page = 1; loadCandidates()">
                <el-radio-button
                  v-for="opt in STATUS_OPTIONS"
                  :key="opt.value"
                  :value="opt.value"
                >{{ opt.label }}</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item>
              <span class="muted" style="font-size: 13px">{{ selCountText() }}</span>
            </el-form-item>
          </el-form>
        </div>

        <!-- 候选列表 -->
        <el-card>
          <el-table
            :data="candItems"
            v-loading="candLoading"
            border stripe size="small"
            @selection-change="onSelectionChange"
            empty-text="暂无数据"
            style="width: 100%"
          >
            <el-table-column type="selection" width="46" reserve-selection />
            <el-table-column label="序号" width="60" type="index"
              :index="(i: number) => (candFilters.page - 1) * candFilters.page_size + i + 1" />
            <el-table-column label="类型" width="130">
              <template #default="{ row }">
                <el-tag size="small" type="info" effect="plain">{{ kindCn(row.extracted_kind) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="extracted_key" label="抽取关键值" min-width="240" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="mono" style="word-break: break-all">{{ row.extracted_key }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="140">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.status)" effect="dark" size="small">
                  {{ statusCn(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="note" label="备注" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="muted">{{ row.note || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="src_intel_id" label="来源情报 ID" width="190" show-overflow-tooltip>
              <template #default="{ row }">
                <span v-if="row.src_intel_id" class="hex-val mono" style="font-size: 12px">
                  {{ row.src_intel_id }}
                </span>
                <span v-else class="muted">—</span>
              </template>
            </el-table-column>
            <el-table-column label="生成时间" width="170">
              <template #default="{ row }">
                {{ row.created_at ? row.created_at.replace('T', ' ').slice(0, 19) : '—' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.status === 'pending' || row.status === 'rejected'"
                  size="small" type="success" plain
                  @click="candSelected = [row]; doApprove()"
                >批准</el-button>
                <el-button
                  v-if="row.status === 'pending'"
                  size="small" type="warning" plain
                  @click="candSelected = [row]; doReject()"
                >拒绝</el-button>
                <el-tag v-else size="small" type="info" effect="plain">{{ statusCn(row.status) }}</el-tag>
              </template>
            </el-table-column>
          </el-table>

          <!-- 空状态（当 items 为空但 loading 结束时给出更友好的提示） -->
          <div v-if="!candLoading && candItems.length === 0"
               style="padding: 14px 0 4px; text-align: center">
            <span class="muted">{{ emptyCandText }}</span>
          </div>

          <!-- 分页器 -->
          <div v-if="candTotal > 0" style="display: flex; justify-content: flex-end; margin-top: 14px">
            <el-pagination
              v-model:current-page="candFilters.page"
              v-model:page-size="candFilters.page_size"
              layout="total, sizes, prev, pager, next, jumper"
              :total="candTotal"
              :page-sizes="[10, 20, 50, 100]"
              background
              small
              @current-change="loadCandidates"
              @size-change="candFilters.page = 1; loadCandidates()"
            />
          </div>
        </el-card>

        <!-- 底部操作区（移动端方便） -->
        <div style="margin-top: 14px; display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end">
          <el-button
            type="warning" plain
            :disabled="!candSelected.length"
            @click="doReject"
          >
            批量拒绝所选（{{ candSelected.length }}）
          </el-button>
          <el-button
            type="success"
            :disabled="!candSelected.length"
            @click="doApprove"
          >
            批量批准并入库所选（{{ candSelected.length }}）
          </el-button>
        </div>
      </el-tab-pane>

      <!-- ================= Tab 3: 单站协作 ================= -->
      <el-tab-pane label="单站协作" name="collab">
        <el-alert
          title="单站协作：给定一个站点，让 Agent 自动挖掘「这个站点都有什么权限」"
          type="info" :closable="false" show-icon
          style="margin-bottom: 16px"
        >
          <template #default>
            <div style="line-height: 1.8">
              流水线：<b>SiteProfiler</b> 单站资产收集 → <b>Modeler</b> 业务建模 →
              <b>PermissionAgent</b> 权限发现专项（未授权访问 / 水平越权 / 垂直越权 / IDOR / 权限矩阵）→
              <b>Attacker</b>（可选）变异攻击 → <b>Verifier</b> 独立复现 → <b>Reviewer</b> 入库。
              <br/>
              至少需要 <b>一个身份会话 Cookie</b>（user 或 admin）；<b>admin Cookie</b> 用于垂直越权检测；
              <b>user2 Cookie</b> 用于水平越权检测；<b>匿名探测</b>（anon_probe）测未授权访问。
            </div>
          </template>
        </el-alert>

        <el-card>
          <template #header>参数配置</template>
          <el-form label-width="120px">
            <el-form-item label="关联任务" required>
              <el-select
                v-model="collab.taskId"
                placeholder="必选：单站协作将作为该任务的后台流程执行，结果入库到该任务"
                clearable filterable style="width: 100%"
              >
                <el-option v-for="t in tasks" :key="t.id"
                  :label="(t.name || '') + '  ·  ' + (t.id || '').slice(0, 8)"
                  :value="t.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="目标 URL" required>
              <el-input
                v-model="collab.url"
                placeholder="如 http://target.com（用于 SSRF 校验与资产归属过滤）"
              />
            </el-form-item>
            <el-form-item label="Admin Cookie">
              <el-input
                v-model="collab.adminCookie" type="textarea" :rows="2"
                placeholder="管理员身份 Cookie，用于垂直越权检测（如 Authorization: Bearer xxx 或 SESSION=xxx）"
              />
            </el-form-item>
            <el-form-item label="User Cookie">
              <el-input
                v-model="collab.userCookie" type="textarea" :rows="2"
                placeholder="普通用户身份 Cookie，用于权限矩阵基线与水平越权检测"
              />
            </el-form-item>
            <el-form-item label="User2 Cookie">
              <el-input
                v-model="collab.user2Cookie" type="textarea" :rows="2"
                placeholder="另一普通用户 Cookie，用于水平越权（同权限换 ID 访问对比）"
              />
            </el-form-item>
            <el-form-item label="匿名探测">
              <el-switch v-model="collab.anonProbe" />
              <span class="muted" style="margin-left: 10px">
                开启后先以无 Cookie 匿名身份访问，检测未授权访问漏洞（推荐开启）
              </span>
            </el-form-item>
            <el-form-item label="启用 LLM 攻击">
              <el-switch v-model="collab.enableAttacker" />
              <span class="muted" style="margin-left: 10px">
                开启后基于权限矩阵生成变异攻击动作（关闭则只做权限发现，不进行 LLM 攻击）
              </span>
            </el-form-item>
            <el-form-item>
              <el-button
                type="warning" :loading="collabRunning"
                :icon="Lightning"
                @click="startCollab"
              >
                {{ collabRunning ? '启动中…' : '启动单站协作' }}
              </el-button>
              <span class="muted" style="margin-left: 10px">
                后台异步执行，启动后可前往「任务详情」查看进度，「漏洞」页查看产出。
              </span>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.snippet {
  font-family: 'JetBrains Mono', Consolas, Monaco, monospace;
  background: rgba(255, 255, 255, 0.04);
  padding: 10px 12px;
  border-radius: 8px;
  word-break: break-all;
  white-space: pre-wrap;
  color: #cbd5e1;
  line-height: 1.6;
  border: 1px solid rgba(148, 163, 184, 0.12);
}
.mono {
  font-family: 'JetBrains Mono', Consolas, Monaco, monospace;
}
.mono-block {
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.03);
  border-left: 2px solid rgba(59, 130, 246, 0.4);
  margin: 4px 0;
  line-height: 1.8;
}
.filter-form-miner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}
.filter-form-miner .el-form-item {
  margin-bottom: 0;
  margin-right: 0;
}
.el-table {
  --el-table-row-hover-bg-color: rgba(59, 130, 246, 0.10);
}
</style>
