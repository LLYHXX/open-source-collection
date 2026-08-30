<template>
  <div class="memory-page">
    <!-- ===== 顶部统计卡 ===== -->
    <section class="stats-panel">
      <div class="metric-cards">
        <div class="metric-card total">
          <div class="m-label">{{ L(labels.memoryRubric.total) }}</div>
          <div class="m-value">
            <el-tooltip v-if="isCyber" :content="'DEC: ' + (stats.total || 0)" placement="top">
              <span class="hex-val">{{ hexLabel(stats.total || 0) }}</span>
            </el-tooltip>
            <span v-else>{{ stats.total || 0 }}</span>
          </div>
          <div class="m-sub">
            {{ L(labels.memoryRubric.active) }}
            <el-tooltip v-if="isCyber" :content="'DEC: ' + (stats.active || 0)"><span class="hex-val">{{ hexLabel(stats.active || 0) }}</span></el-tooltip>
            <span v-else>{{ stats.active || 0 }}</span>
            ·
            {{ L(labels.memoryRubric.total_hits) }}
            <el-tooltip v-if="isCyber" :content="'DEC: ' + (stats.total_hits || 0)"><span class="hex-val">{{ hexLabel(stats.total_hits || 0) }}</span></el-tooltip>
            <span v-else>{{ stats.total_hits || 0 }}</span>
          </div>
        </div>
        <div class="metric-card lifecycle">
          <div class="m-label">{{ L(labels.memoryRubric.lifecycle) }}</div>
          <ul class="lc-list">
            <li v-for="l in stats.by_lifecycle || []" :key="l.status" class="lc-item">
              <span class="lc-dot" :class="l.status"></span>
              <span class="lc-name">{{ L(labels.lifecycle[l.status] || {cyber:l.status, full:l.status}) }}</span>
              <el-tooltip v-if="isCyber" :content="'DEC: ' + l.count"><span class="lc-num hex-val">{{ hexLabel(l.count) }}</span></el-tooltip>
              <span v-else class="lc-num">{{ l.count }}</span>
            </li>
          </ul>
        </div>
        <div class="metric-card bykind">
          <div class="m-label">{{ L(labels.memoryRubric.kind) }}</div>
          <div class="bar-chart">
            <div v-for="k in topKinds" :key="k.kind" class="bar-row">
              <div class="bar-name" :title="k.kind">
                <code v-if="isCyber" class="mem-kind-inline">&lt;{{ k.kind }}&gt;</code>
                <span v-else>{{ kindCn(k.kind) }}</span>
              </div>
              <div class="bar-track"><div class="bar-fill" :style="{ width: k.pct + '%' }"></div></div>
              <el-tooltip v-if="isCyber" :content="'DEC: ' + k.count"><span class="bar-count hex-val">{{ hexLabel(k.count) }}</span></el-tooltip>
              <span v-else class="bar-count">{{ k.count }}</span>
            </div>
            <div v-if="!stats.by_kind?.length" class="empty">暂无类型分布数据</div>
          </div>
        </div>
        <div class="metric-card daily">
          <div class="m-label">{{ L(labels.memoryRubric.daily) }}</div>
          <div class="daily-chart">
            <div v-for="(d, i) in stats.daily_7d || []" :key="i" class="daily-col">
              <div class="daily-bar" :style="{ height: dailyMax ? (d.count / dailyMax * 80 + 4) + 'px' : '4px' }">
                <el-tooltip v-if="isCyber && d.count" :content="'DEC: ' + d.count">
                  <span class="daily-count hex-val">{{ hexLabel(d.count) }}</span>
                </el-tooltip>
                <span v-else-if="d.count" class="daily-count">{{ d.count }}</span>
              </div>
              <div class="daily-date">{{ d.date.slice(5) }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== 筛选条 ===== -->
    <section class="filter-bar card">
      <el-form :inline="true" class="filter-form" size="default">
        <el-form-item label="关键词">
          <el-input v-model="filters.q" placeholder="key / value / 来源" clearable @keyup.enter="reload" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.kind" :placeholder="isCyber ? '*' : '全部'" clearable @change="reload">
            <el-option v-for="k in kindOptions" :key="k" :label="k" :value="k" />
          </el-select>
        </el-form-item>
        <el-form-item :label="isCyber ? 'LIFE' : '状态'">
          <el-select v-model="filters.lifecycle" :placeholder="isCyber ? '*' : '全部'" clearable @change="reload">
            <el-option :label="L(labels.lifecycle.active)" value="active" />
            <el-option :label="L(labels.lifecycle.stale)" value="stale" />
            <el-option :label="L(labels.lifecycle.retired)" value="retired" />
          </el-select>
        </el-form-item>
        <el-form-item :label="isCyber ? 'CONF' : '置信度'">
          <el-slider
            v-model="confRange" range :min="0" :max="1" :step="0.05"
            show-stops :format-tooltip="(v: number) => (v*100).toFixed(0) + '%'"
            @change="reload" style="width: 180px" />
        </el-form-item>
        <el-form-item>
          <el-button @click="reload"><el-icon><Search /></el-icon> {{ L(labels.actions.search) }}</el-button>
          <el-button @click="resetFilters">{{ L(labels.actions.reset) }}</el-button>
        </el-form-item>
        <el-form-item class="spacer" />
        <el-form-item>
          <el-badge v-if="candidatesWaiting > 0" :value="candidatesWaiting" :max="99" class="cand-badge">
            <el-button type="warning" size="default" @click="openCandDialog" plain>
              <el-icon><Connection /></el-icon> [CAND]
            </el-button>
          </el-badge>
          <el-tooltip v-else content="暂无待审批候选" placement="top">
            <el-button size="default" @click="openCandDialog" disabled>[CAND]</el-button>
          </el-tooltip>
          <el-button type="primary" @click="openCreate" style="margin-left:8px">
            <el-icon><Plus /></el-icon> {{ L(labels.actions.new) }}
          </el-button>
          <el-upload
            class="inline-up" :auto-upload="false" :show-file-list="false"
            accept=".json,.csv" :on-change="doImport"
          >
            <el-button>[{{ L(labels.actions.in) }}]</el-button>
          </el-upload>
          <el-dropdown @command="doExport">
            <el-button>[{{ L(labels.actions.out) }}]<i class="el-icon-arrow-down el-icon--right"/></el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="json">{{ isCyber ? 'JSON · FILTERED' : '导出 JSON（当前筛选）' }}</el-dropdown-item>
                <el-dropdown-item command="csv">{{ isCyber ? 'CSV · FILTERED' : '导出 CSV（当前筛选）' }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </el-form-item>
      </el-form>
    </section>

    <!-- ===== 卡片浏览 ===== -->
    <section class="card-grid">
      <div v-for="it in items" :key="it.id" class="mem-card">
        <header class="mem-head">
          <el-tag :type="lifecycleTag(it.lifecycle)" size="small">{{ L(labels.lifecycle[it.lifecycle] || {cyber:it.lifecycle, full:it.lifecycle}) }}</el-tag>
          <code class="mem-kind" v-if="isCyber">&lt;{{ it.kind }}&gt;</code>
          <span class="mem-kind" v-else>{{ kindCn(it.kind) }}</span>
          <span class="mem-time">{{ it.updated_at }}</span>
        </header>
        <div v-if="Array.isArray(it.tags) && it.tags.length" class="mem-tags">
          <el-tag v-for="tg in it.tags.slice(0, 6)" :key="tg" size="small" effect="plain" :type="tagType(tg)">{{ tg }}</el-tag>
        </div>
        <div class="mem-key" title="检索键">{{ it.key || '（空键）' }}</div>
        <div class="mem-value-wrap">
          <div v-if="it.masked && !expanded[it.id]" class="mem-value masked-value">
            [▒▒▒ MASKED · CREDENTIAL PATTERN ▒▒▒]
          </div>
          <div v-else class="mem-value" :class="{ 'is-json': looksJson(it.value) }">
            {{ it.value.length > 400 ? it.value.slice(0, 400) + '…' : it.value || '（空值）' }}
          </div>
          <div v-if="it.masked" class="mem-mask-toggle" @click="toggleMasked(it.id)">
            <el-button size="small" link type="primary">[{{ expanded[it.id] ? (isCyber ? 'HIDE' : '隐藏') : (isCyber ? 'SHOW' : '显示') }}]</el-button>
          </div>
        </div>
        <footer class="mem-foot">
          <div class="foot-left">
            <el-tag size="small" type="info" class="conf-tag" :title="'置信度 ' + it.confidence">
              <span v-if="isCyber" class="hex-val">{{ hexLabel(Math.round(it.confidence*100)) }}%</span>
              <span v-else>置信度 {{ (it.confidence * 100).toFixed(0) }}%</span>
            </el-tag>
            <span v-if="it.hits > 0" class="hits">
              {{ isCyber ? 'HITS:' : '命中 ' }}
              <el-tooltip v-if="isCyber" :content="'DEC: ' + it.hits"><span class="hex-val">{{ hexLabel(it.hits) }}</span></el-tooltip>
              <span v-else>{{ it.hits }}</span>{{ isCyber ? '' : ' 次' }}
            </span>
            <span v-if="it.source" class="src" :title="'来源 ' + it.source">{{ isCyber ? 'SRC:' : '源 · ' }}{{ short(it.source, 24) }}</span>
          </div>
          <div class="foot-right">
            <el-button size="small" link @click="openEdit(it)">{{ L(labels.actions.edit) }}</el-button>
            <el-button size="small" link type="warning" @click="doRetire(it)">{{ L(labels.actions.retire) }}</el-button>
            <el-button size="small" link type="danger" @click="doHardDelete(it)">{{ L(labels.actions.purge) }}</el-button>
          </div>
        </footer>
      </div>
      <div v-if="!loading && !items.length" class="empty-block">
        <el-empty description="暂无记忆条目" :image-size="40" />
      </div>
    </section>

    <!-- ===== 分页 ===== -->
    <div class="pagination-wrap" v-if="total > filters.page_size">
      <el-pagination
        v-model:current-page="filters.page"
        v-model:page-size="filters.page_size"
        layout="total, prev, pager, next, sizes"
        :page-sizes="[20, 50, 100, 200]"
        :total="total"
        background
        @current-change="reload"
        @size-change="reload"
      />
    </div>

    <!-- ===== 新增 / 编辑弹窗 ===== -->
    <el-dialog v-model="dialog.show" :title="dialog.id ? (isCyber ? L(labels.actions.edit) + ' · MEM_OBJ' : '编辑记忆') : (isCyber ? L(labels.actions.new) + ' · MEM_OBJ' : '新增记忆')" width="640px">
      <el-form :model="dialog.form" label-width="92px">
        <el-form-item :label="isCyber ? 'KIND (req)' : '类型 kind'" required>
          <el-select v-model="dialog.form.kind" filterable allow-create default-first-option>
            <el-option v-for="k in kindOptions" :key="k" :label="k" :value="k" />
          </el-select>
          <span class="hint-text" v-if="!isCyber">例如 credential / fingerprint / attack_experience 等</span>
        </el-form-item>
        <el-form-item :label="isCyber ? 'KEY' : '检索键 key'">
          <el-input v-model="dialog.form.key" :placeholder="isCyber ? 'retrieval key' : '用于检索的键，如 host/指纹名/站点标识'" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item :label="isCyber ? 'VALUE' : '内容 value'">
          <el-input v-model="dialog.form.value" type="textarea" :rows="8" :placeholder="isCyber ? 'payload' : '记忆内容，凭证、指纹、经验 JSON 均可'" />
        </el-form-item>
        <el-form-item :label="isCyber ? 'CONF %' : '置信度'">
          <el-slider v-model="dialog.form.confidence" :min="0" :max="1" :step="0.05" show-stops
            :format-tooltip="(v: number) => (v*100).toFixed(0) + '%'" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="isCyber ? 'SRC' : '来源 source'">
          <el-input v-model="dialog.form.source" :placeholder="isCyber ? 'source tag' : '例如 target-xxx 或 upload，便于溯源'" maxlength="200" />
        </el-form-item>
        <el-form-item :label="isCyber ? 'TAGS · []' : '标签 tags'">
          <el-select
            v-model="dialog.form.tags"
            multiple filterable allow-create default-first-option
            :placeholder="isCyber ? 'STALE_CANDIDATE / custom...' : '自定义标签，回车新增；内置：STALE_CANDIDATE'"
            style="width: 100%"
          >
            <el-option label="STALE_CANDIDATE" value="STALE_CANDIDATE" />
          </el-select>
        </el-form-item>
        <el-form-item :label="isCyber ? 'LIFECYCLE' : '生命周期'">
          <el-radio-group v-model="dialog.form.lifecycle">
            <el-radio-button value="active">{{ L(labels.lifecycle.active) }}</el-radio-button>
            <el-radio-button value="stale">{{ L(labels.lifecycle.stale) }}</el-radio-button>
            <el-radio-button value="retired">{{ L(labels.lifecycle.retired) }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.show = false">{{ L(labels.actions.cancel) }}</el-button>
        <el-button type="primary" @click="submitDialog">{{ L(labels.actions.save) }}</el-button>
      </template>
    </el-dialog>

    <!-- ===== Miner Candidate 审批弹窗 ===== -->
    <el-dialog v-model="candDialog.show" :title="isCyber ? 'CAND · PENDING APPR' : '[CAND] 候选情报审批（Link-Extend Hook 生成）'" width="860px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 12px">
        <template #title>{{ isCyber ? 'BATCH_APPROVE · WRITE INTEL' : '批量批准会直接把 (kind, key, value, extracted_key) 写入情报库；批量拒绝则标记 status=rejected 不再提示。' }}</template>
        <span v-if="isCyber">OUT_OF_SCOPE 项 status=skipped 且永不自动起任务。</span>
        <span v-else>越权项会被系统自动标为 skipped，不会出现在此列表中。</span>
      </el-alert>
      <el-table :data="candDialog.items" size="small" border empty-text="暂无待审批候选" @selection-change="(s: any[])=>candDialog.selected=s" style="max-height: 400px; overflow:auto;">
        <el-table-column type="selection" width="46" />
        <el-table-column prop="id" label="#" width="54" />
        <el-table-column prop="extracted_kind" :label="isCyber ? 'KIND' : '类型'" width="120">
          <template #default="{row}"><code class="mem-kind-inline">&lt;{{ row.extracted_kind }}&gt;</code></template>
        </el-table-column>
        <el-table-column prop="extracted_key" :label="isCyber ? 'EXTRACTED_KEY' : '抽取值'" min-width="180" />
        <el-table-column prop="src_intel_id" :label="isCyber ? 'SRC_INTEL' : '来源 Intel ID'" width="170">
          <template #default="{row}"><span class="hex-val" v-if="row.src_intel_id">{{ row.src_intel_id }}</span></template>
        </el-table-column>
        <el-table-column prop="status" :label="isCyber ? 'STAT' : '状态'" width="100" />
        <el-table-column prop="note" :label="isCyber ? 'NOTE' : '备注'" min-width="160">
          <template #default="{row}"><span class="muted">{{ row.note || '—' }}</span></template>
        </el-table-column>
        <el-table-column prop="created_at" :label="isCyber ? 'CREATED_AT' : '生成时间'" width="170" />
      </el-table>
      <template #footer>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span class="muted">{{ isCyber ? 'SEL: ' + candDialog.selected.length + ' / TOTAL: ' + candDialog.total : '已选 ' + candDialog.selected.length + ' 项 / 合计 ' + candDialog.total }}</span>
          <div>
            <el-button @click="loadCandidates">{{ isCyber ? 'REFRESH' : '刷新' }}</el-button>
            <el-button type="warning" plain :disabled="!candDialog.selected.length" @click="rejectSelected">{{ L(labels.actions.reject) }}</el-button>
            <el-button type="primary" :disabled="!candDialog.selected.length" @click="approveSelected">{{ L(labels.actions.approve) }}</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Upload, Download, Connection } from '@element-plus/icons-vue'
import { api } from '@/api'
import { zh, INTEL_KIND } from '@/i18n/cn'

function kindCn(k: string) {
  return (INTEL_KIND as any)[k] || zh(k) || k
}

const labels: any = inject('uiLabels', {
  isCyber: { value: false },
  actions: {}, memoryRubric: {}, lifecycle: {}, status: {},
})
const isCyber = computed(() => labels?.isCyber?.value)
function L(obj: any) { return isCyber.value ? obj?.cyber : obj?.full }
function hexLabel(n: number) {
  try { const v = Number(n) || 0; return '0x' + v.toString(16).padStart(2, '0').toUpperCase() }
  catch { return String(n) }
}
function tagType(t: string) {
  const s = String(t).toUpperCase()
  if (s.includes('STALE')) return 'warning'
  if (s.includes('CANDIDATE')) return 'info'
  if (s.includes('HIGH') || s.includes('CRITICAL')) return 'danger'
  return 'success'
}

const loading = ref(false)
const items = ref<any[]>([])
const total = ref(0)
const kindOptions = ref<string[]>([])
const stats = reactive<any>({
  total: 0, active: 0, retired: 0, stale: 0, total_hits: 0,
  by_kind: [], by_lifecycle: [], daily_7d: [], top_hits: [],
})
const filters = reactive({
  q: '', kind: '' as string, lifecycle: '' as string, source: '',
  page: 1, page_size: 20,
})
const confRange = ref<[number, number]>([0, 1])
const expanded = reactive<Record<string, boolean>>({})

const candidatesWaiting = ref(0)
const candDialog = reactive({
  show: false,
  items: [] as any[],
  selected: [] as any[],
  total: 0,
})

const dialog = reactive({
  show: false,
  id: '' as string,
  form: {
    kind: '', key: '', value: '', confidence: 0.6, source: '', lifecycle: 'active' as 'active' | 'stale' | 'retired',
    tags: [] as string[],
  },
})

const topKinds = computed(() => {
  const list = stats.by_kind || []
  const max = Math.max(1, ...list.slice(0, 6).map((k: any) => k.count))
  return list.slice(0, 6).map((k: any) => ({ ...k, pct: +(k.count / max * 100).toFixed(1) }))
})
const dailyMax = computed(() => Math.max(0, ...(stats.daily_7d || []).map((d: any) => d.count)))

// ---- helpers ----
function lifecycleLabel(s: string) { return L(labels.lifecycle[s] || {cyber:s, full:s}) }
function lifecycleTag(s: string) { return { active: 'success', stale: 'warning', retired: 'info' }[s] || '' }
function short(s: string, n: number) { return s.length > n ? s.slice(0, n) + '…' : s }
function looksJson(v: string) {
  const t = (v || '').trim()
  return (t.startsWith('{') && t.endsWith('}')) || (t.startsWith('[') && t.endsWith(']'))
}
function toggleMasked(id: string) { expanded[id] = !expanded[id] }

// ---- 筛选重置 ----
function resetFilters() {
  filters.q = ''; filters.kind = ''; filters.lifecycle = ''; filters.source = ''
  filters.page = 1; confRange.value = [0, 1]
  reload()
}

// ---- 加载列表 + 统计 + CAND 数 ----
async function reload() {
  loading.value = true
  try {
    const params: any = {
      ...filters, conf_min: confRange.value[0], conf_max: confRange.value[1],
    }
    const [r, s, cand] = await Promise.all([
      api.queryIntel(params), api.intelStats(),
      api.listMinerCandidates('pending', 1, 1).catch(() => ({ success: false, data: { total: 0, items: [] } })),
    ])
    if (r.success && r.data) {
      items.value = r.data.items || []
      total.value = r.data.total || 0
      if (r.data.kind_options?.length) kindOptions.value = r.data.kind_options
    }
    if (s.success && s.data) Object.assign(stats, s.data)
    candidatesWaiting.value = Number(cand?.data?.total) || 0
  } catch (e: any) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// ---- CAND dialog ----
async function openCandDialog() {
  candDialog.show = true
  await loadCandidates()
}
async function loadCandidates() {
  try {
    const r: any = await api.listMinerCandidates('pending', 1, 200)
    if (r?.success && r.data) {
      candDialog.items = r.data.items || []
      candDialog.total = r.data.total || 0
    }
  } catch (e: any) {
    candDialog.items = []
    candDialog.total = 0
  } finally {
    candidatesWaiting.value = candDialog.total
  }
}
async function approveSelected() {
  const ids = candDialog.selected.map((x: any) => String(x.id)).filter(Boolean)
  if (!ids.length) return
  try {
    await ElMessageBox.confirm(
      isCyber ? `WRITE INTEL × ${ids.length} ?` : `批准并入库 ${ids.length} 条候选情报？写入后可在情报库 / 记忆管理中检索。`,
      L(labels.actions.approve) + ' × ' + ids.length,
      { type: 'success', confirmButtonText: L(labels.actions.confirm) },
    )
    const r: any = await api.approveMinerCandidates(ids)
    ElMessage.success(r?.message || `已写入 ${ids.length} 条`)
    candDialog.selected = []
    await loadCandidates()
    reload()
  } catch {}
}
async function rejectSelected() {
  const ids = candDialog.selected.map((x: any) => String(x.id)).filter(Boolean)
  if (!ids.length) return
  try {
    await ElMessageBox.confirm(
      isCyber ? `REJECT × ${ids.length} ? (irreversible)` : `拒绝 ${ids.length} 条候选？被拒条目不再出现在候选列表中。`,
      L(labels.actions.reject) + ' × ' + ids.length,
      { type: 'warning', confirmButtonText: L(labels.actions.confirm) },
    )
    const r: any = await api.rejectMinerCandidates(ids)
    ElMessage.success(r?.message || `已拒绝 ${ids.length} 条`)
    candDialog.selected = []
    await loadCandidates()
  } catch {}
}

// ---- 增删改 ----
function openCreate() {
  dialog.id = ''
  dialog.form = { kind: '', key: '', value: '', confidence: 0.6, source: '', lifecycle: 'active', tags: [] }
  dialog.show = true
}
function openEdit(it: any) {
  dialog.id = it.id
  dialog.form = {
    kind: it.kind, key: it.key, value: it.value,
    confidence: it.confidence, source: it.source, lifecycle: it.lifecycle,
    tags: Array.isArray(it.tags) ? [...it.tags] : [],
  }
  dialog.show = true
}
async function submitDialog() {
  if (!dialog.form.kind.trim()) { ElMessage.warning(isCyber ? 'KIND_REQ' : '类型 kind 必填'); return }
  try {
    const payload = { ...dialog.form, tags: Array.isArray(dialog.form.tags) ? dialog.form.tags : [] }
    if (dialog.id) await api.updateIntel(dialog.id, payload)
    else await api.createIntel(payload)
    ElMessage.success(isCyber ? 'WRITTEN' : '保存成功')
    dialog.show = false
    reload()
  } catch (e: any) {
    ElMessage.error(e?.message || '保存失败')
  }
}
async function doRetire(it: any) {
  try {
    await ElMessageBox.confirm(
      isCyber ? `MARK L.RET · id=${short(it.id,8)} ?` : `确定把条目 "${short(it.key || it.kind, 24)}" 标记为退役？`,
      L(labels.actions.retire), { type: 'warning' }
    )
    await api.retireIntel(it.id, false)
    ElMessage.success(isCyber ? 'L.RET · OK' : '已退役')
    reload()
  } catch {}
}
async function doHardDelete(it: any) {
  try {
    await ElMessageBox.confirm(
      isCyber ? `PURGE · id=${short(it.id,8)} ? IRREVERSIBLE.`
              : `确定物理删除 "${short(it.key || it.kind, 24)}"？该操作不可恢复。`,
      L(labels.actions.purge), { type: 'error', confirmButtonText: isCyber ? 'PURGE' : '永久删除', cancelButtonText: L(labels.actions.cancel) }
    )
    await api.retireIntel(it.id, true)
    ElMessage.success(isCyber ? 'PURGED' : '已删除')
    reload()
  } catch {}
}

// ---- 导入 / 导出 ----
async function doImport(file: any) {
  try {
    const opt = await ElMessageBox.prompt(
      isCyber
        ? `IMPORT_MODE · merge / replace_kind / replace_all`
        : `选择导入模式：合并 merge（按 id 覆盖）/ replace_kind（按 kind 替换）/ replace_all（清空全库导入）`,
      `${isCyber ? 'INBOUND:' : '即将导入'} ${file.name}`,
      { inputPlaceholder: 'merge', inputValue: 'merge', confirmButtonText: isCyber ? 'START INBOUND' : '开始导入' },
    ) as any
    const mode = (opt.value || 'merge').trim() || 'merge'
    const r = await api.intelImport(file.raw, mode)
    ElMessage.success(r.message || (isCyber ? 'INBOUND OK' : '导入成功'))
    reload()
  } catch {}
}
function doExport(t: string) {
  const p = {
    kind: filters.kind, lifecycle: filters.lifecycle, q: filters.q, source: filters.source,
    conf_min: confRange.value[0], conf_max: confRange.value[1],
  }
  if (t === 'json') api.intelExportJson(p)
  else api.intelExportCsv(p)
}

let _candPoll: any = null
onMounted(() => {
  reload()
  // 每 30 秒轻量轮询一次 CAND 计数（即便后端没接也 catch 空值）
  try {
    _candPoll = setInterval(async () => {
      try {
        const r: any = await api.listMinerCandidates('pending', 1, 1)
        candidatesWaiting.value = Number(r?.data?.total) || 0
      } catch { /* ignore */ }
    }, 30000)
  } catch {}
})
onBeforeUnmount(() => { if (_candPoll) { clearInterval(_candPoll); _candPoll = null } })
</script>

<style scoped>
.memory-page { padding: 16px 20px 32px; }

.cand-badge :deep(.el-badge__content) {
  border: 1px solid var(--border-1, #1a1d24);
}

/* ---- 统计卡 ---- */
.metric-cards {
  display: grid;
  grid-template-columns: 1fr 1fr 1.4fr 1.3fr;
  gap: 14px;
  margin-bottom: 18px;
}
.metric-card {
  background: linear-gradient(180deg, var(--card-bg, #1a1d27), var(--card-bg-2, #13161f));
  border: 1px solid var(--card-border, #2a2f3e);
  border-radius: var(--radius-card, 10px);
  padding: 14px 16px;
  color: var(--text-1, #e5e7eb);
}
.metric-card .m-label { font-size: 12px; color: var(--text-2, #9ca3af); margin-bottom: 8px; letter-spacing: .03em; }
:global([data-theme='cyber']) .metric-card .m-label { font-family: var(--font-mono, Consolas, monospace); }
.metric-card .m-value { font-size: 28px; font-weight: 700; color: var(--brand, #6aa6ff); }
.metric-card .m-sub   { font-size: 12px; color: var(--text-2, #9ca3af); margin-top: 4px; }

.lc-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.lc-item { display: flex; align-items: center; gap: 8px; }
.lc-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
:global([data-theme='cyber']) .lc-dot,
:global([data-theme='mono']) .lc-dot { border-radius: 0; }
.lc-dot.active  { background: #10b981; }
.lc-dot.stale   { background: #f59e0b; }
.lc-dot.retired { background: #64748b; }
.lc-name { flex: 1; color: var(--text-2, #cbd5e1); }
:global([data-theme='cyber']) .lc-name { font-family: var(--font-mono, Consolas, monospace); letter-spacing: .02em; }
.lc-num  { font-weight: 600; color: var(--text-1, #e5e7eb); }

.bar-chart { display: flex; flex-direction: column; gap: 6px; }
.bar-row { display: grid; grid-template-columns: 88px 1fr 36px; align-items: center; gap: 8px; font-size: 12px; }
.bar-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-2, #cbd5e1); }
.mem-kind-inline { display: inline-block; padding: 0 3px; background: var(--bg-1, #0a0c10); border: 1px solid var(--border-1, #1a1d24);
  font-family: var(--font-mono, Consolas, monospace); color: var(--accent, #6aa6ff); border-radius: 2px; font-size: 11px; }
:global([data-theme='cyber']) .mem-kind-inline,
:global([data-theme='mono']) .mem-kind-inline { border-radius: 0; color: var(--accent, #00e5ff); }
.bar-track { background: #242836; border-radius: 4px; height: 8px; overflow: hidden; }
:global([data-theme='cyber']) .bar-track,
:global([data-theme='mono']) .bar-track { border-radius: 0; background: var(--bg-1, #0a0c10); border: 1px solid var(--border-1, #1a1d24); }
.bar-fill  { background: linear-gradient(90deg, #6aa6ff, #a78bfa); height: 100%; border-radius: 4px; }
:global([data-theme='cyber']) .bar-fill { background: var(--accent, #00e5ff); border-radius: 0; }
:global([data-theme='mono']) .bar-fill { background: #9ca3af; border-radius: 0; }
.bar-count { text-align: right; color: var(--text-1, #e5e7eb); font-variant-numeric: tabular-nums; }
.bar-chart .empty { text-align: center; color: var(--text-3, #6b7280); padding: 14px 0; }

.daily-chart { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; align-items: end; height: 110px; }
.daily-col { display: flex; flex-direction: column; align-items: center; justify-content: end; height: 100%; }
.daily-bar { background: linear-gradient(180deg, #6aa6ff, #4f46e5); border-radius: 4px 4px 0 0; min-height: 4px; width: 70%;
  display: flex; justify-content: center; position: relative; }
:global([data-theme='cyber']) .daily-bar { background: var(--accent, #00e5ff); border-radius: 0; box-shadow: 0 0 6px rgba(0,229,255,0.3); }
:global([data-theme='mono']) .daily-bar { background: #9ca3af; border-radius: 0; }
.daily-count { font-size: 10px; color: #fff; position: absolute; top: -15px; }
:global([data-theme='cyber']) .daily-count { color: var(--accent, #00e5ff); }
.daily-date  { font-size: 11px; color: var(--text-2, #9ca3af); margin-top: 4px; }

/* ---- 筛选条 ---- */
.filter-bar { margin-bottom: 16px; }
.filter-form { display: flex; flex-wrap: wrap; align-items: center; row-gap: 4px; }
.filter-form .spacer { flex: 1; }
.inline-up .el-upload__action { display: inline-block; }
.hint-text { display: block; font-size: 12px; color: var(--text-2, #9ca3af); margin-top: 4px; }

/* ---- 卡片 ---- */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 14px;
}
.mem-card {
  background: var(--card-bg, #1a1d27);
  border: 1px solid var(--card-border, #2a2f3e);
  border-radius: var(--radius-card, 10px);
  padding: 12px 14px;
  display: flex; flex-direction: column; gap: 8px;
  transition: transform .15s ease, border-color .15s ease;
}
.mem-card:hover { transform: translateY(-1px); border-color: var(--brand, #6aa6ff); }
:global([data-theme='cyber']) .mem-card:hover,
:global([data-theme='mono']) .mem-card:hover {
  transform: none;
  border-color: var(--accent, #00e5ff);
  box-shadow: 0 0 14px rgba(0,229,255,0.10);
}
.mem-head { display: flex; align-items: center; gap: 8px; }
.mem-kind { flex: 1; font-size: 12px; padding: 2px 6px; border-radius: 4px; background: #242836;
  color: var(--brand, #9cc2ff); display: inline-block; }
:global([data-theme='cyber']) .mem-kind,
:global([data-theme='mono']) .mem-kind {
  border-radius: 0; background: transparent; border: 1px solid var(--border-1, #1a1d24); color: var(--accent, #00e5ff);
  font-family: var(--font-mono, Consolas, monospace); letter-spacing: .01em;
}
.mem-time { font-size: 12px; color: var(--text-3, #6b7280); }
:global([data-theme='cyber']) .mem-time { font-family: var(--font-mono, Consolas, monospace); color: var(--text-3, #7f8ea3); }
.mem-tags { display: flex; gap: 4px; flex-wrap: wrap; }
.mem-key  { font-weight: 600; color: var(--text-1, #fff); word-break: break-all; }
.mem-value-wrap { position: relative; }
.mem-value { font-size: 13px; color: var(--text-2, #cbd5e1); white-space: pre-wrap; word-break: break-all;
  background: #0f1218; border-radius: 6px; padding: 8px 10px; line-height: 1.5; max-height: 160px; overflow: auto; }
:global([data-theme='cyber']) .mem-value,
:global([data-theme='mono']) .mem-value { border-radius: 0; background: var(--bg-1, #0a0c10); border: 1px solid var(--border-1, #1a1d24); font-family: var(--font-mono, Consolas, monospace); font-size: 12px; }
.mem-value.is-json { font-family: Consolas, monospace; font-size: 12px; }
.mem-value.masked-value { font-family: var(--font-mono, Consolas, monospace); color: #f59e0b; letter-spacing: .03em; text-align: center; user-select: none; }
.mem-mask-toggle { margin-top: 4px; text-align: right; }
.mem-foot { display: flex; justify-content: space-between; align-items: center; margin-top: auto; }
.foot-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.conf-tag { background: #0f1218 !important; color: var(--brand, #6aa6ff) !important; border-color: #2a2f3e !important; border-radius: 3px; }
:global([data-theme='cyber']) .conf-tag,
:global([data-theme='mono']) .conf-tag { border-radius: 0; background: transparent !important; border: 1px solid var(--accent, #00e5ff) !important; color: var(--accent, #00e5ff) !important; }
.hits, .src { font-size: 12px; color: var(--text-2, #9ca3af); }
:global([data-theme='cyber']) .hits,
:global([data-theme='cyber']) .src { font-family: var(--font-mono, Consolas, monospace); color: var(--text-2, #9fb0c7); }

.empty-block { grid-column: 1/-1; }
.pagination-wrap { display: flex; justify-content: center; margin-top: 18px; }

@media (max-width: 1200px) {
  .metric-cards { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .metric-cards { grid-template-columns: 1fr; }
  .filter-form .el-form-item { display: block; width: 100%; }
}
</style>
