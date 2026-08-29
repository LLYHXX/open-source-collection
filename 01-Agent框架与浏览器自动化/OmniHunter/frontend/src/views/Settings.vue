<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const list = ref<any[]>([])
const newKey = ref('')
const newVal = ref('')
const tokenInput = ref(localStorage.getItem('aififteen_hunter_token') || '')

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
onMounted(() => {
  load()
  loadVersion()
})
</script>

<template>
  <div>
    <h2 class="page-title">设置</h2>
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
