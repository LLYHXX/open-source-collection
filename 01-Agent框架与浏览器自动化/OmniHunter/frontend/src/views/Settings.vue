<script setup lang="ts">
import { computed, inject, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const uiLabels: any = inject('uiLabels', { isCyber: { value: false } })
const isCyber = computed(() => uiLabels?.isCyber?.value)

function L(obj: any) { return isCyber.value ? obj?.cyber : obj?.full }

const list = ref<any[]>([])
const newKey = ref('')
const newVal = ref('')
const tokenInput = ref(localStorage.getItem('aififteen_hunter_token') || '')

// ===== UI & Appearance =====
const THEME_OPTIONS = [
  { value: 'default', label: 'Default（默认深色渐变）' },
  { value: 'cyber',   label: 'Cyber / Terminal（纯黑 + 等宽 + 扫描线）' },
  { value: 'mono',    label: 'Mono Noir（纯黑白灰 · 无彩色）' },
]
const themeSel = ref<string>('default')
const savingTheme = ref(false)

function readThemeFromList() {
  const row = (list.value || []).find((s: any) => s.key && s.key.toLowerCase() === 'ui.theme')
  if (row?.value) themeSel.value = row.value
  else {
    try { themeSel.value = localStorage.getItem('ui.theme') || 'default' } catch {}
  }
}

function applyThemeToDom(t: string) {
  try {
    document.documentElement.setAttribute('data-theme', t)
    if (t === 'cyber' || t === 'mono') document.body.setAttribute('data-theme', t)
    else document.body.removeAttribute('data-theme')
    localStorage.setItem('ui.theme', t)
    // 通知 App.vue（已监听）
    window.dispatchEvent(new CustomEvent('aif-theme-change', { detail: { theme: t } }))
  } catch { /* ignore */ }
}

async function saveTheme() {
  savingTheme.value = true
  try {
    await api.saveSetting({ key: 'ui.theme', value: themeSel.value })
    applyThemeToDom(themeSel.value)
    ElMessage.success('主题已切换并保存（动态配置优先于本地）')
    await load()
  } catch (e: any) {
    // 即便后端存失败，前端仍然切（本地生效）
    applyThemeToDom(themeSel.value)
    ElMessage.warning('后端配置未写入，本次仅本地生效：' + (e?.message || e))
  } finally {
    savingTheme.value = false
  }
}

// ===== Autonomous Miner =====
const miner = reactive({
  enabled: false,
  scope_asset_ids: [] as string[],
  daily_budget_max_jobs: 20,
  max_runtime_min: 120,
  auto_approve: 'reverify_only' as 'reverify_only' | 'all_scope' | 'off',
  cron_expr: '0 2 * * *',
})
const scopeInput = ref('')
const savingMiner = ref(false)
const triggering = ref(false)
const minerRuns = ref<any[]>([])

function parseMinerConfig(raw: any) {
  if (!raw || !raw.success || !raw.data) return
  const d = raw.data as any
  miner.enabled = !!d.enabled
  miner.scope_asset_ids = Array.isArray(d.scope_asset_ids) ? d.scope_asset_ids : []
  miner.daily_budget_max_jobs = Number(d.daily_budget_max_jobs) || 20
  miner.max_runtime_min = Number(d.max_runtime_min) || 120
  miner.auto_approve = ['reverify_only', 'all_scope', 'off'].includes(d.auto_approve) ? d.auto_approve : 'reverify_only'
  miner.cron_expr = d.cron_expr || '0 2 * * *'
}

async function loadMinerConfig() {
  try {
    const r = await api.getMinerConfig()
    parseMinerConfig(r)
  } catch { /* ignore，路由 lazy load 未就绪时不打扰 */ }
  await reloadMinerRuns()
}

async function saveMiner() {
  // 预算范围
  const budget = Number(miner.daily_budget_max_jobs)
  if (!budget || budget < 1 || budget > 200) {
    ElMessage.warning('日预算 daily_budget_max_jobs 必须为 1~200 的整数')
    return
  }
  const runtime = Number(miner.max_runtime_min)
  if (!runtime || runtime < 5 || runtime > 1440) {
    ElMessage.warning('最大运行时长 max_runtime_min 必须为 5~1440 分钟')
    return
  }
  const scope = (miner.scope_asset_ids || []).map((s) => String(s).trim()).filter(Boolean)
  if (miner.enabled && scope.length === 0) {
    ElMessage.warning('启用 Miner 前 scope_asset_ids（授权资产域）不能为空')
    return
  }
  // all_scope 二次确认
  if (miner.enabled && miner.auto_approve === 'all_scope') {
    try {
      await ElMessageBox.confirm(
        'auto_approve=all_scope 将对 coverage_gap / reverify / link 全部三条流水线的候选项直接起任务，不再人工审批。确认开启？',
        '全量自动批准（高风险）',
        { type: 'warning', confirmButtonText: '确认全量批准', cancelButtonText: '改为仅复检自动' },
      )
    } catch { miner.auto_approve = 'reverify_only' }
  }
  savingMiner.value = true
  try {
    const payload = {
      enabled: miner.enabled,
      scope_asset_ids: scope,
      daily_budget_max_jobs: budget,
      max_runtime_min: runtime,
      auto_approve: miner.auto_approve,
      cron_expr: (miner.cron_expr || '').trim() || '0 2 * * *',
    }
    const r: any = await api.saveMinerConfig(payload)
    parseMinerConfig({ success: true, data: r.data })
    ElMessage.success(r.message || 'Miner 配置已保存（需要重启后端才刷新 cron trigger，或点击触发一次立即运行）')
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.message || e))
  } finally {
    savingMiner.value = false
    reloadMinerRuns()
  }
}

async function triggerMinerOnce() {
  triggering.value = true
  try {
    const r: any = await api.triggerMinerOnce()
    ElMessage.success(r.message || '已触发一次 Miner 轮次')
  } catch (e: any) {
    ElMessage.error('触发失败: ' + (e.message || e))
  } finally {
    triggering.value = false
    setTimeout(reloadMinerRuns, 1000)
  }
}

async function reloadMinerRuns() {
  try {
    const r: any = await api.listMinerRuns(30)
    minerRuns.value = r?.success && Array.isArray(r.data) ? r.data : []
  } catch { minerRuns.value = [] }
}

function addScopeItem() {
  const v = scopeInput.value.trim()
  if (!v) return
  if (!miner.scope_asset_ids.includes(v)) miner.scope_asset_ids.push(v)
  scopeInput.value = ''
}
function removeScopeItem(v: string) {
  miner.scope_asset_ids = miner.scope_asset_ids.filter((x) => x !== v)
}

// 系统更新
const version = ref<any>(null)
const updateLogs = ref('')
const updating = ref(false)

// ===== 模型接入 =====
const LLM_PRESETS = [
  { label: 'DeepSeek', base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat', protocol: 'openai' },
  { label: '通义千问 Qwen（阿里）', base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus', protocol: 'openai' },
  { label: 'Kimi（月之暗面）', base_url: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k', protocol: 'openai' },
  { label: '智谱 GLM', base_url: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-4-flash', protocol: 'openai' },
  { label: 'OpenRouter（聚合）', base_url: 'https://openrouter.ai/api/v1', model: '', protocol: 'openai' },
  { label: '硅基流动 SiliconFlow', base_url: 'https://api.siliconflow.cn/v1', model: 'Qwen/Qwen2.5-7B-Instruct', protocol: 'openai' },
  { label: 'Ollama 本地', base_url: 'http://127.0.0.1:11434/v1', model: 'qwen2.5:7b', protocol: 'openai' },
  { label: 'LM Studio 本地', base_url: 'http://127.0.0.1:1234/v1', model: '', protocol: 'openai' },
  { label: 'Google Gemini（OpenAI 兼容端点）', base_url: 'https://generativelanguage.googleapis.com/v1beta/openai', model: 'gemini-2.0-flash', protocol: 'openai' },
  { label: 'Claude 官方（Anthropic 协议）', base_url: 'https://api.anthropic.com', model: 'claude-sonnet-4-20250514', protocol: 'anthropic' },
]

const big = reactive({ base_url: '', model: '', api_key: '', protocol: 'openai' })
const small = reactive({ base_url: '', model: '', api_key: '', protocol: 'openai' })
const savingModel = ref(false)

// ===== 资产测绘平台 =====
const PLATFORMS = [
  { key: 'fofa', label: 'FOFA', hint: 'email:APIKEY 或纯 APIKEY' },
  { key: 'quake', label: '360 Quake', hint: 'API Token（个人中心生成）' },
  { key: 'hunter', label: 'Hunter鹰图', hint: 'API-Key（开放接口页生成）' },
  { key: 'zoomeye', label: 'ZoomEye', hint: 'API-KEY' },
  { key: 'shodan', label: 'Shodan', hint: 'API Key' },
  { key: 'censys', label: 'Censys', hint: 'API_ID:API_SECRET' },
]
const platformKeys = reactive<Record<string, string>>({})
const testing = reactive<Record<string, boolean>>({})
const testResults = reactive<Record<string, string>>({})
const savingPlatforms = ref(false)

function applyPreset(label: string) {
  const p = LLM_PRESETS.find((x) => x.label === label)
  if (!p) return
  big.base_url = p.base_url
  big.model = p.model
  big.protocol = p.protocol
}

async function load() {
  list.value = await api.listSettings()
  const kv: Record<string, string> = {}
  for (const s of list.value) kv[s.key.toLowerCase()] = s.value
  big.base_url = kv['llm_base_url'] || ''
  big.model = kv['llm_model'] || ''
  big.api_key = kv['llm_api_key'] || ''
  big.protocol = kv['llm_protocol'] || 'openai'
  small.base_url = kv['llm_small_base_url'] || ''
  small.model = kv['llm_small_model'] || ''
  small.api_key = kv['llm_small_api_key'] || ''
  small.protocol = kv['llm_small_protocol'] || 'openai'
  for (const p of PLATFORMS) {
    platformKeys[p.key] = kv[`${p.key}_key`] || ''
  }
}

async function saveModel() {
  if (!big.base_url.trim() || !big.model.trim()) {
    ElMessage.warning('大模型 Base URL 和模型名必填')
    return
  }
  savingModel.value = true
  try {
    // 空值跳过：避免误清空 .env 已配置项；如需清除请用下方动态配置表
    const items: Record<string, string> = {
      LLM_BASE_URL: big.base_url,
      LLM_MODEL: big.model,
      LLM_PROTOCOL: big.protocol,
    }
    if (big.api_key) items.LLM_API_KEY = big.api_key
    if (small.model.trim()) {
      items.LLM_SMALL_BASE_URL = small.base_url
      items.LLM_SMALL_MODEL = small.model
      items.LLM_SMALL_PROTOCOL = small.protocol
      if (small.api_key) items.LLM_SMALL_API_KEY = small.api_key
    }
    for (const [k, v] of Object.entries(items)) {
      await api.saveSetting({ key: k, value: v })
    }
    ElMessage.success('模型配置已保存并即时生效（动态配置优先于 .env）')
    await load()
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.message || e))
  } finally {
    savingModel.value = false
  }
}

// ===== 资产测绘平台（操作函数）=====
async function savePlatforms() {
  savingPlatforms.value = true
  try {
    // 空值跳过：避免误清空 .env 已配置的密钥
    const filled = PLATFORMS.filter((p) => (platformKeys[p.key] || '').trim())
    if (!filled.length) {
      ElMessage.warning('至少填写一个平台密钥')
      return
    }
    for (const p of filled) {
      await api.saveSetting({ key: `${p.key.toUpperCase()}_KEY`, value: platformKeys[p.key].trim() })
    }
    ElMessage.success(`已保存 ${filled.length} 个平台密钥并即时生效`)
    await load()
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.message || e))
  } finally {
    savingPlatforms.value = false
  }
}

async function testPlatform(key: string) {
  testing[key] = true
  testResults[key] = ''
  try {
    const res: any = await api.testAssetPlatform(key)
    testResults[key] = res.message || (res.success ? '连通正常' : '测试失败')
    res.success ? ElMessage.success(`${key} 连通正常`) : ElMessage.error(res.message || '测试失败')
  } catch (e: any) {
    testResults[key] = '测试失败: ' + (e.message || e)
    ElMessage.error('测试失败: ' + (e.message || e))
  } finally {
    testing[key] = false
  }
}

function setToken() {
  localStorage.setItem('aififteen_hunter_token', tokenInput.value)
  ElMessage.success('访问令牌已保存到本地')
}
async function save() {
  if (!newKey.value) return
  await api.saveSetting({ key: newKey.value, value: newVal.value })
  ElMessage.success('已保存')
  newKey.value = ''
  newVal.value = ''
  await load()
}
async function loadVersion() {
  try {
    version.value = await api.version()
  } catch {
    version.value = null
  }
}
async function doUpdate() {
  updating.value = true
  try {
    const res = await api.systemUpdate()
    updateLogs.value = res.data.logs
    ElMessage.success(res.message)
    await loadVersion()
  } catch (e: any) {
    ElMessage.error('更新失败: ' + (e.message || e))
  } finally {
    updating.value = false
  }
}
onMounted(async () => {
  await load()
  readThemeFromList()
  loadVersion()
  await loadMinerConfig()
})
</script>

<template>
  <div>
    <h2 class="page-title">{{ isCyber ? 'CFG · CONTROL PANEL' : '设置' }}</h2>

    <!-- ===== UI & Appearance ===== -->
    <el-card style="margin-bottom: 16px">
      <template #header>{{ isCyber ? 'UI · APPEARANCE' : 'UI 与外观（零依赖 · 三种内建主题）' }}</template>
      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 12px">
        <template #title>{{ isCyber ? 'THEME_SWITCH · data-theme · ZERO_DEPS' : '切换主题后即时生效，选择同时持久化到「动态配置」ui.theme 字段，跨设备同步。' }}</template>
        <span v-if="isCyber">DEFAULT/CYBER/MONO · CSS VAR OVERLAY · NO FONT CDN</span>
        <span v-else>Cyber = 纯黑 #050608 底 + 等宽字体 + CRT 扫描线；Mono = 全黑白灰去彩色；Default = 原有渐变风格。</span>
      </el-alert>
      <div style="display:flex; align-items:center; gap:16px; flex-wrap:wrap;">
        <el-radio-group v-model="themeSel" size="default">
          <el-radio-button v-for="t in THEME_OPTIONS" :key="t.value" :value="t.value">{{ t.label }}</el-radio-button>
        </el-radio-group>
        <el-button type="primary" :loading="savingTheme" @click="saveTheme">{{ isCyber ? 'SAVE · WRITE ui.theme' : '保存并应用主题' }}</el-button>
      </div>
    </el-card>

    <!-- ===== Autonomous Miner ===== -->
    <el-card style="margin-bottom: 16px">
      <template #header>{{ isCyber ? 'AUTONOMOUS MINER · CTRL' : 'AI 主动深度挖掘（限域 · 默认关 · 三 Loop 审计）' }}</template>
      <el-alert type="warning" :closable="false" show-icon style="margin-bottom: 12px">
        <template #title>{{ isCyber ? 'SCOPE_REQUIRED · BUDGET_CAP · AUTO_APPR_REVERIFY_ONLY (default)' : '启用前必须先填 scope_asset_ids（授权资产域），空 scope 不允许启用，确保只在授权范围内自主挖掘。' }}</template>
        <span v-if="isCyber">LOOP1=COVERAGE · LOOP2=REVERIFY(30D DECAY) · LOOP3=LINK_EXTRACT</span>
        <span v-else>三 Loop：①覆盖缺口补采（Coverage Gap）②30 天未更新置信度衰减自动复检（Decay &amp; Re-Verify）③情报入库时从 value 正则抽取域名/IP/CVE 作为候选（Link-Extend，入库不发 HTTP）。</span>
      </el-alert>

      <el-form label-width="180px" size="small">
        <el-form-item :label="isCyber ? 'ENABLED' : '启用 Miner（cron 每日定点 + 支持手动触发）'">
          <el-switch v-model="miner.enabled" />
          <span class="muted" style="margin-left:10px">{{ isCyber ? '[__miner_internal__] CRON_TRIGGER = ' + (miner.cron_expr || '0 2 * * *') : '定时 job id = __miner_internal__，默认每日 02:00（CST）运行一次。' }}</span>
        </el-form-item>

        <el-form-item :label="isCyber ? 'SCOPE (asset hosts)' : '授权 scope · scope_asset_ids（域名/IP/CIDR，必填非空）'">
          <div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap; width: 640px">
            <el-tag v-for="(v,i) in miner.scope_asset_ids" :key="v+'_'+i" closable type="info" size="small" effect="dark" @close="removeScopeItem(v)">{{ v }}</el-tag>
            <el-input v-model="scopeInput" placeholder="如 example.com / 192.168.1.0/24 / 10.0.0.5" style="width: 360px" size="small" @keyup.enter="addScopeItem" />
            <el-button size="small" @click="addScopeItem">{{ isCyber ? 'ADD' : '添加到 scope' }}</el-button>
          </div>
        </el-form-item>

        <el-form-item :label="isCyber ? 'BUDGET · JOBS/DAY' : '日预算 · daily_budget_max_jobs（1~200，默认 20）'">
          <el-input-number v-model="miner.daily_budget_max_jobs" :min="1" :max="200" />
        </el-form-item>

        <el-form-item :label="isCyber ? 'MAX_RUNTIME (min)' : '单轮最大运行时长 · max_runtime_min（5~1440，默认 120）'">
          <el-input-number v-model="miner.max_runtime_min" :min="5" :max="1440" />
        </el-form-item>

        <el-form-item :label="isCyber ? 'AUTO_APPROVE_POLICY' : 'auto_approve 自动审批策略'">
          <el-radio-group v-model="miner.auto_approve">
            <el-radio value="reverify_only">{{ isCyber ? 'REVERIFY_ONLY (SAFE)' : '仅复检 loop 自动批准（默认，推荐）' }}</el-radio>
            <el-radio value="all_scope">{{ isCyber ? 'ALL_SCOPE (UNATTEND)' : 'scope 内全部自动批准（无人值守，需二次确认）' }}</el-radio>
            <el-radio value="off">{{ isCyber ? 'OFF · FULL_MANUAL' : '全手动审批（off）' }}</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item :label="isCyber ? 'CRON_EXPR' : 'Cron 表达式（默认 0 2 * * * = 每日 02:00 CST）'">
          <el-input v-model="miner.cron_expr" placeholder="0 2 * * *" style="width:280px" />
          <el-button style="margin-left:8px" :loading="triggering" @click="triggerMinerOnce">
            <el-icon><Promotion /></el-icon>
            {{ isCyber ? 'TRIGGER · ONCE' : '立即触发一次（不等 cron）' }}
          </el-button>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="savingMiner" @click="saveMiner">{{ isCyber ? 'SAVE · COMMIT miner.cfg' : '保存 Miner 配置' }}</el-button>
        </el-form-item>
      </el-form>

      <el-divider content-position="left">{{ isCyber ? 'MINER_AUDIT_LOG (last 30 runs)' : 'Miner 运行审计日志（最近 30 条）' }}</el-divider>
      <el-table :data="minerRuns" size="small" border empty-text="暂无运行记录" style="max-height: 340px; overflow:auto;">
        <el-table-column prop="id" label="#" width="54" />
        <el-table-column prop="trigger_at" :label="isCyber ? 'TRIGGER_AT' : '触发时间'" width="170" />
        <el-table-column prop="loop1_coverage_count" :label="isCyber ? 'L1·COV' : 'L1·覆盖数量'" width="90" align="right">
          <template #default="{row}"><span class="hex-val">{{ row.loop1_coverage_count ?? 0 }}</span></template>
        </el-table-column>
        <el-table-column prop="loop2_reverify_count" :label="isCyber ? 'L2·REV' : 'L2·复验数量'" width="90" align="right">
          <template #default="{row}"><span class="hex-val">{{ row.loop2_reverify_count ?? 0 }}</span></template>
        </el-table-column>
        <el-table-column prop="loop3_link_count" :label="isCyber ? 'L3·LINK' : 'L3·链接挖掘'" width="90" align="right">
          <template #default="{row}"><span class="hex-val">{{ row.loop3_link_count ?? 0 }}</span></template>
        </el-table-column>
        <el-table-column prop="budget_hit_limit" :label="isCyber ? 'BUDGET_LIMIT' : '预算触顶'" width="96" align="center">
          <template #default="{row}">
            <el-tag v-if="row.budget_hit_limit" size="small" type="warning">{{ isCyber ? 'HIT' : '是' }}</el-tag>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="finished_at" :label="isCyber ? 'FINISHED_AT' : '结束时间'" width="170" />
        <el-table-column prop="error_log" :label="isCyber ? 'ERR' : '错误日志'">
          <template #default="{row}">
            <span v-if="row.error_log" style="color:var(--danger,#ef4444); font-family:Consolas,monospace; white-space:pre-wrap;">{{ row.error_log }}</span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header>访问令牌</template>
      <el-input v-model="tokenInput" placeholder="与后端 API_TOKEN 一致" style="width: 400px" show-password />
      <el-button type="primary" style="margin-left: 8px" @click="setToken">保存</el-button>
      <p class="muted">未设后端 API_TOKEN 时开放访问；生产环境务必设置。</p>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header>模型接入（多模型多协议 · 保存即时生效）</template>
      <el-alert type="success" :closable="false" show-icon style="margin-bottom: 12px">
        <template #title>任意最低配 LLM 都能跑通全流程 —— 检测、复现、定级由自研引擎确定性完成</template>
        支持 OpenAI 兼容协议（DeepSeek / Qwen / Kimi / GLM / OpenRouter / 硅基流动 / Ollama / LM Studio / Gemini）与
        Anthropic 官方协议（Claude）。小模型层用于轻量分析省 Token，留空自动回退大模型。
      </el-alert>

      <el-form label-width="110px" size="small">
        <el-form-item label="快捷预设">
          <el-select placeholder="选择厂商自动填充（仅大模型）" style="width: 360px" @change="applyPreset">
            <el-option v-for="p in LLM_PRESETS" :key="p.label" :label="p.label" :value="p.label" />
          </el-select>
        </el-form-item>
      </el-form>

      <el-divider content-position="left">大模型（关键决策层）</el-divider>
      <el-form label-width="110px" size="small">
        <el-form-item label="协议">
          <el-radio-group v-model="big.protocol">
            <el-radio value="openai">OpenAI 兼容</el-radio>
            <el-radio value="anthropic">Anthropic (Claude)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="big.base_url" placeholder="https://api.deepseek.com/v1" style="width: 480px" />
        </el-form-item>
        <el-form-item label="模型">
          <el-input v-model="big.model" placeholder="deepseek-chat" style="width: 480px" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="big.api_key" show-password placeholder="sk-..." style="width: 480px" />
        </el-form-item>
      </el-form>

      <el-divider content-position="left">小模型（轻量分析层 · 留空回退大模型）</el-divider>
      <el-form label-width="110px" size="small">
        <el-form-item label="协议">
          <el-radio-group v-model="small.protocol">
            <el-radio value="openai">OpenAI 兼容</el-radio>
            <el-radio value="anthropic">Anthropic (Claude)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="small.base_url" placeholder="留空 = 使用大模型 Base URL，如 http://127.0.0.1:11434/v1" style="width: 480px" />
        </el-form-item>
        <el-form-item label="模型">
          <el-input v-model="small.model" placeholder="留空 = 不启用小模型层，如 qwen2.5:7b" style="width: 480px" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="small.api_key" show-password placeholder="本地服务可随意填" style="width: 480px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="savingModel" @click="saveModel">保存模型配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header>资产测绘平台（信息搜集 · 保存即时生效）</template>
      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 12px">
        配置密钥后，任务「目标来源」即可选对应平台自动搜集资产；选「全平台」时六家并发查询。
        支持自然语言意图自动翻译为平台语法（如「找高校统一身份认证系统」）。
      </el-alert>
      <el-table :data="PLATFORMS" border size="small">
        <el-table-column prop="label" label="平台" width="130" />
        <el-table-column label="密钥">
          <template #default="{ row }">
            <el-input v-model="platformKeys[row.key]" :placeholder="row.hint" show-password />
          </template>
        </el-table-column>
        <el-table-column label="连通测试" width="220">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 8px">
              <el-button size="small" :loading="testing[row.key]" @click="testPlatform(row.key)">测试</el-button>
              <span class="muted" style="font-size: 12px">{{ testResults[row.key] }}</span>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-button type="primary" style="margin-top: 12px" :loading="savingPlatforms" @click="savePlatforms">
        保存平台密钥
      </el-button>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header>引擎与模型策略（工具为主 · Agent 为辅）</template>
      <el-alert type="success" :closable="false" show-icon>
        <template #title>检测、复现、定级全部由自研引擎确定性完成 —— 任意最低配 LLM 都能跑通全流程</template>
        引擎内置 10 类确定性检测插件（SQLi / XSS / RCE / 目录遍历 / SSRF / 信息泄露 / IDOR / 越权 / 弱口令 / 文件上传），
        每个检测结果都经独立 verify() 复现 + CVSS 3.1 自动定级，检出率不随模型质量波动。
        大模型只负责 Payload 变异与复杂场景兜底（Worker ReAct），换最便宜的模型即可。
      </el-alert>
      <div style="display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap">
        <el-tag effect="dark" type="success" size="small">LLM_MODEL=deepseek-chat 即可</el-tag>
        <el-tag effect="dark" type="primary" size="small">任务模式选「自研引擎」全程免 LLM 检测</el-tag>
        <el-tag effect="dark" type="info" size="small">副作用插件（弱口令/上传）默认关闭</el-tag>
      </div>
      <p class="muted" style="margin-top: 10px">
        引擎调优键：ENGINE_PLUGIN_TIMEOUT（单插件超时）、ENGINE_MAX_CONCURRENCY（并发）、
        ENGINE_WEAKPWD_ENABLED / ENGINE_UPLOAD_PROBE（副作用开关），可用下方动态配置覆盖 .env。
      </p>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header>系统更新（增量拉取，不重新下载）</template>
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px">
        <span class="muted">版本：{{ version?.data?.version || '-' }}</span>
        <span class="muted">提交：{{ version?.data?.commit || '-' }}</span>
        <el-button type="primary" :loading="updating" @click="doUpdate">一键更新</el-button>
      </div>
      <p class="muted">
        一键更新 = git pull 增量拉取最新代码 + pip install 同步依赖。
        后端用 --reload 启动会自动热重载，无需重新下载/重新部署。
      </p>
      <el-input v-if="updateLogs" v-model="updateLogs" type="textarea" :rows="10" readonly />
    </el-card>

    <el-card>
      <template #header>动态配置（存库，优先级高于 .env）</template>
      <el-table :data="list" border size="small">
        <el-table-column prop="key" label="键" width="240" />
        <el-table-column prop="value" label="值" />
      </el-table>
      <div style="margin-top: 16px; display: flex; gap: 8px">
        <el-input v-model="newKey" placeholder="键，如 LLM_MODEL" style="width: 240px" />
        <el-input v-model="newVal" placeholder="值" style="width: 320px" />
        <el-button type="primary" @click="save">新增/更新</el-button>
      </div>
    </el-card>
  </div>
</template>
