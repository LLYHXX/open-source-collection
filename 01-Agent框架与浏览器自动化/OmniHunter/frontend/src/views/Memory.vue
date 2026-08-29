<template>
  <div class="memory-page">
    <!-- ===== 顶部统计卡 ===== -->
    <section class="stats-panel">
      <div class="metric-cards">
        <div class="metric-card total">
          <div class="m-label">记忆条目</div>
          <div class="m-value">{{ stats.total || 0 }}</div>
          <div class="m-sub">活跃 {{ stats.active }} · 命中 {{ stats.total_hits }} 次</div>
        </div>
        <div class="metric-card lifecycle">
          <div class="m-label">生命周期</div>
          <ul class="lc-list">
            <li v-for="l in stats.by_lifecycle || []" :key="l.status" class="lc-item">
              <span class="lc-dot" :class="l.status"></span>
              <span class="lc-name">{{ lifecycleLabel(l.status) }}</span>
              <span class="lc-num">{{ l.count }}</span>
            </li>
          </ul>
        </div>
        <div class="metric-card bykind">
          <div class="m-label">类型分布（Top 6）</div>
          <div class="bar-chart">
            <div v-for="k in topKinds" :key="k.kind" class="bar-row">
              <div class="bar-name" :title="k.kind">{{ k.kind }}</div>
              <div class="bar-track"><div class="bar-fill" :style="{ width: k.pct + '%' }"></div></div>
              <div class="bar-count">{{ k.count }}</div>
            </div>
            <div v-if="!stats.by_kind?.length" class="empty">暂无数据</div>
          </div>
        </div>
        <div class="metric-card daily">
          <div class="m-label">近 7 日增量</div>
          <div class="daily-chart">
            <div v-for="(d, i) in stats.daily_7d || []" :key="i" class="daily-col">
              <div class="daily-bar" :style="{ height: dailyMax ? (d.count / dailyMax * 80 + 4) + 'px' : '4px' }">
                <span class="daily-count" v-if="d.count">{{ d.count }}</span>
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
          <el-select v-model="filters.kind" placeholder="全部" clearable @change="reload">
            <el-option v-for="k in kindOptions" :key="k" :label="k" :value="k" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.lifecycle" placeholder="全部" clearable @change="reload">
            <el-option label="活跃 active" value="active" />
            <el-option label="陈旧 stale" value="stale" />
            <el-option label="退役 retired" value="retired" />
          </el-select>
        </el-form-item>
        <el-form-item label="置信度">
          <el-slider
            v-model="confRange" range :min="0" :max="1" :step="0.05"
            show-stops :format-tooltip="(v) => (v*100).toFixed(0) + '%'"
            @change="reload" style="width: 180px" />
        </el-form-item>
        <el-form-item>
          <el-button @click="reload"><el-icon><Search /></el-icon> 查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
        <el-form-item class="spacer" />
        <el-form-item>
          <el-button type="primary" @click="openCreate">
            <el-icon><Plus /></el-icon> 新增记忆
          </el-button>
          <el-upload
            class="inline-up" :auto-upload="false" :show-file-list="false"
            accept=".json,.csv" :on-change="doImport"
          >
            <el-button><el-icon><Upload /></el-icon> 导入</el-button>
          </el-upload>
          <el-dropdown @command="doExport">
            <el-button><el-icon><Download /></el-icon> 导出<i class="el-icon-arrow-down el-icon--right"/></el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="json">导出 JSON（当前筛选）</el-dropdown-item>
                <el-dropdown-item command="csv">导出 CSV（当前筛选）</el-dropdown-item>
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
          <el-tag :type="lifecycleTag(it.lifecycle)" size="small">{{ lifecycleLabel(it.lifecycle) }}</el-tag>
          <span class="mem-kind">{{ it.kind }}</span>
          <span class="mem-time">{{ it.updated_at }}</span>
        </header>
        <div class="mem-key" title="检索键">{{ it.key || '（空键）' }}</div>
        <div class="mem-value" :class="{ 'is-json': looksJson(it.value) }">
          {{ it.value.length > 400 ? it.value.slice(0, 400) + '…' : it.value || '（空值）' }}
        </div>
        <footer class="mem-foot">
          <div class="foot-left">
            <el-tag size="small" type="info" class="conf-tag" :title="'置信度 ' + it.confidence">
              置信度 {{ (it.confidence * 100).toFixed(0) }}%
            </el-tag>
            <span class="hits" v-if="it.hits > 0">命中 {{ it.hits }} 次</span>
            <span class="src" v-if="it.source" :title="'来源 ' + it.source">源 · {{ short(it.source, 24) }}</span>
          </div>
          <div class="foot-right">
            <el-button size="small" link @click="openEdit(it)">编辑</el-button>
            <el-button size="small" link type="danger" @click="doRetire(it)">退役</el-button>
            <el-button size="small" link type="danger" @click="doHardDelete(it)">删除</el-button>
          </div>
        </footer>
      </div>
      <div v-if="!loading && !items.length" class="empty-block">
        <el-empty description="还没有记忆条目，点右上角“新增记忆”或导入 .json/.csv 开始沉淀。" />
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
    <el-dialog v-model="dialog.show" :title="dialog.id ? '编辑记忆' : '新增记忆'" width="640px">
      <el-form :model="dialog.form" label-width="92px">
        <el-form-item label="类型 kind" required>
          <el-select v-model="dialog.form.kind" filterable allow-create default-first-option>
            <el-option v-for="k in kindOptions" :key="k" :label="k" :value="k" />
          </el-select>
          <span class="hint-text">例如 credential / fingerprint / attack_experience 等</span>
        </el-form-item>
        <el-form-item label="检索键 key">
          <el-input v-model="dialog.form.key" placeholder="用于检索的键，如 host/指纹名/站点标识" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item label="内容 value">
          <el-input v-model="dialog.form.value" type="textarea" :rows="8" placeholder="记忆内容，凭证、指纹、经验 JSON 均可" />
        </el-form-item>
        <el-form-item label="置信度">
          <el-slider v-model="dialog.form.confidence" :min="0" :max="1" :step="0.05" show-stops
            :format-tooltip="(v) => (v*100).toFixed(0) + '%'" style="width: 100%" />
        </el-form-item>
        <el-form-item label="来源 source">
          <el-input v-model="dialog.form.source" placeholder="例如 target-xxx 或 upload，便于溯源" maxlength="200" />
        </el-form-item>
        <el-form-item label="生命周期">
          <el-radio-group v-model="dialog.form.lifecycle">
            <el-radio-button value="active">active 活跃</el-radio-button>
            <el-radio-button value="stale">stale 陈旧</el-radio-button>
            <el-radio-button value="retired">retired 退役</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.show = false">取消</el-button>
        <el-button type="primary" @click="submitDialog">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Upload, Download } from '@element-plus/icons-vue'
import { api } from '@/api'

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

const dialog = reactive({
  show: false,
  id: '' as string,
  form: { kind: '', key: '', value: '', confidence: 0.6, source: '', lifecycle: 'active' as 'active' | 'stale' | 'retired' },
})

const topKinds = computed(() => {
  const list = stats.by_kind || []
  const max = Math.max(1, ...list.slice(0, 6).map(k => k.count))
  return list.slice(0, 6).map(k => ({ ...k, pct: +(k.count / max * 100).toFixed(1) }))
})
const dailyMax = computed(() => Math.max(0, ...(stats.daily_7d || []).map(d => d.count)))

// ---- helpers ----
function lifecycleLabel(s: string) {
  return { active: '活跃', stale: '陈旧', retired: '退役' }[s] || s
}
function lifecycleTag(s: string) {
  return { active: 'success', stale: 'warning', retired: 'info' }[s] || ''
}
function short(s: string, n: number) { return s.length > n ? s.slice(0, n) + '…' : s }
function looksJson(v: string) {
  const t = v.trim()
  return (t.startsWith('{') && t.endsWith('}')) || (t.startsWith('[') && t.endsWith(']'))
}

// ---- 筛选重置 ----
function resetFilters() {
  filters.q = ''; filters.kind = ''; filters.lifecycle = ''; filters.source = ''
  filters.page = 1; confRange.value = [0, 1]
  reload()
}

// ---- 加载列表 + 统计 ----
async function reload() {
  loading.value = true
  try {
    const params: any = {
      ...filters, conf_min: confRange.value[0], conf_max: confRange.value[1],
    }
    const [r, s] = await Promise.all([api.queryIntel(params), api.intelStats()])
    if (r.success && r.data) {
      items.value = r.data.items || []
      total.value = r.data.total || 0
      if (r.data.kind_options?.length) kindOptions.value = r.data.kind_options
    }
    if (s.success && s.data) {
      Object.assign(stats, s.data)
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// ---- 增删改 ----
function openCreate() {
  dialog.id = ''
  dialog.form = { kind: '', key: '', value: '', confidence: 0.6, source: '', lifecycle: 'active' }
  dialog.show = true
}
function openEdit(it: any) {
  dialog.id = it.id
  dialog.form = {
    kind: it.kind, key: it.key, value: it.value,
    confidence: it.confidence, source: it.source, lifecycle: it.lifecycle,
  }
  dialog.show = true
}
async function submitDialog() {
  if (!dialog.form.kind.trim()) { ElMessage.warning('类型 kind 必填'); return }
  try {
    if (dialog.id) await api.updateIntel(dialog.id, dialog.form)
    else await api.createIntel(dialog.form)
    ElMessage.success('保存成功')
    dialog.show = false
    reload()
  } catch (e: any) {
    ElMessage.error(e?.message || '保存失败')
  }
}
async function doRetire(it: any) {
  try {
    await ElMessageBox.confirm(`确定把条目 "${short(it.key || it.kind, 24)}" 标记为退役？`, '退役', { type: 'warning' })
    await api.retireIntel(it.id, false)
    ElMessage.success('已退役')
    reload()
  } catch {}
}
async function doHardDelete(it: any) {
  try {
    await ElMessageBox.confirm(
      `确定物理删除 "${short(it.key || it.kind, 24)}"？该操作不可恢复。`,
      '删除', { type: 'error', confirmButtonText: '永久删除', cancelButtonText: '取消' }
    )
    await api.retireIntel(it.id, true)
    ElMessage.success('已删除')
    reload()
  } catch {}
}

// ---- 导入 / 导出 ----
async function doImport(file: any) {
  try {
    const opt = await ElMessageBox.prompt(
      `选择导入模式：合并 merge（按 id 覆盖）/ replace_kind（按 kind 替换）/ replace_all（清空全库导入）`,
      `即将导入 ${file.name}`,
      { inputPlaceholder: 'merge', inputValue: 'merge', confirmButtonText: '开始导入' },
    ) as any
    const mode = (opt.value || 'merge').trim() || 'merge'
    const r = await api.intelImport(file.raw, mode)
    ElMessage.success(r.message || '导入成功')
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

onMounted(reload)
</script>

<style scoped>
.memory-page { padding: 16px 20px 32px; }

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
  border-radius: 10px;
  padding: 14px 16px;
  color: var(--text-1, #e5e7eb);
}
.metric-card .m-label { font-size: 12px; color: var(--text-2, #9ca3af); margin-bottom: 8px; letter-spacing: .03em; }
.metric-card .m-value { font-size: 28px; font-weight: 700; color: var(--brand, #6aa6ff); }
.metric-card .m-sub   { font-size: 12px; color: var(--text-2, #9ca3af); margin-top: 4px; }

.lc-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.lc-item { display: flex; align-items: center; gap: 8px; }
.lc-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.lc-dot.active  { background: #10b981; }
.lc-dot.stale   { background: #f59e0b; }
.lc-dot.retired { background: #64748b; }
.lc-name { flex: 1; color: var(--text-2, #cbd5e1); }
.lc-num  { font-weight: 600; color: var(--text-1, #e5e7eb); }

.bar-chart { display: flex; flex-direction: column; gap: 6px; }
.bar-row { display: grid; grid-template-columns: 88px 1fr 36px; align-items: center; gap: 8px; font-size: 12px; }
.bar-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-2, #cbd5e1); }
.bar-track { background: #242836; border-radius: 4px; height: 8px; overflow: hidden; }
.bar-fill  { background: linear-gradient(90deg, #6aa6ff, #a78bfa); height: 100%; border-radius: 4px; }
.bar-count { text-align: right; color: var(--text-1, #e5e7eb); font-variant-numeric: tabular-nums; }
.bar-chart .empty { text-align: center; color: var(--text-3, #6b7280); padding: 14px 0; }

.daily-chart { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; align-items: end; height: 110px; }
.daily-col { display: flex; flex-direction: column; align-items: center; justify-content: end; height: 100%; }
.daily-bar { background: linear-gradient(180deg, #6aa6ff, #4f46e5); border-radius: 4px 4px 0 0; min-height: 4px; width: 70%;
  display: flex; justify-content: center; position: relative; }
.daily-count { font-size: 10px; color: #fff; position: absolute; top: -15px; }
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
  border-radius: 10px;
  padding: 12px 14px;
  display: flex; flex-direction: column; gap: 8px;
  transition: transform .15s ease, border-color .15s ease;
}
.mem-card:hover { transform: translateY(-1px); border-color: var(--brand, #6aa6ff); }
.mem-head { display: flex; align-items: center; gap: 8px; }
.mem-kind { flex: 1; font-size: 12px; padding: 2px 6px; border-radius: 4px; background: #242836;
  color: var(--brand, #9cc2ff); display: inline-block; }
.mem-time { font-size: 12px; color: var(--text-3, #6b7280); }
.mem-key  { font-weight: 600; color: var(--text-1, #fff); word-break: break-all; }
.mem-value { font-size: 13px; color: var(--text-2, #cbd5e1); white-space: pre-wrap; word-break: break-all;
  background: #0f1218; border-radius: 6px; padding: 8px 10px; line-height: 1.5; max-height: 160px; overflow: auto; }
.mem-value.is-json { font-family: Consolas, monospace; font-size: 12px; }
.mem-foot { display: flex; justify-content: space-between; align-items: center; margin-top: auto; }
.foot-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.conf-tag { background: #0f1218 !important; color: var(--brand, #6aa6ff) !important; border-color: #2a2f3e !important; }
.hits, .src { font-size: 12px; color: var(--text-2, #9ca3af); }

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
