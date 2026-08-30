<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh, Search, Delete, View, Lightning, DataAnalysis,
} from '@element-plus/icons-vue'
import { api } from '@/api'
import {
  zh, CVE_SOURCE, CVE_SCAN_STATUS, CVE_SCAN_STATUS_TAG,
  CVE_SEVERITY, CVE_SEVERITY_TAG, CVE_PIPELINE, PLATFORM,
} from '@/i18n/cn'

// ============================================================
// 统计卡片
// ============================================================
const stats = ref<any>({
  total: 0, recent_7d: 0, pending_asset_hits: 0,
  by_severity: {}, by_source: {},
})

async function loadStats() {
  try {
    const r: any = await api.cveStats()
    if (r?.success) stats.value = r.data || stats.value
  } catch { /* 静默 */ }
}

// ============================================================
// Tab 1: CVE 列表
// ============================================================
const activeTab = ref('cves')
const cveLoading = ref(false)
const cveItems = ref<any[]>([])
const cveTotal = ref(0)
const cveFilters = reactive({
  keyword: '',
  severity: '',
  source: '',
  page: 1,
  page_size: 20,
})

const SEVERITY_OPTIONS = [
  { label: '全部', value: '' },
  { label: '严重', value: 'CRITICAL' },
  { label: '高危', value: 'HIGH' },
  { label: '中危', value: 'MEDIUM' },
  { label: '低危', value: 'LOW' },
]
const SOURCE_OPTIONS = [
  { label: '全部', value: '' },
  { label: 'NVD', value: 'nvd' },
  { label: 'OSV.dev', value: 'osv' },
]

async function loadCves() {
  cveLoading.value = true
  try {
    const r: any = await api.listCves({
      keyword: cveFilters.keyword.trim(),
      severity: cveFilters.severity,
      source: cveFilters.source,
      page: cveFilters.page,
      page_size: cveFilters.page_size,
    })
    if (r?.success && r.data) {
      cveItems.value = r.data.items || []
      cveTotal.value = Number(r.data.total) || 0
    } else {
      cveItems.value = []
      cveTotal.value = 0
      ElMessage.warning(r?.message || 'CVE 列表加载失败')
    }
  } catch (e: any) {
    cveItems.value = []
    cveTotal.value = 0
    ElMessage.error(e?.friendlyMsg || ('CVE 列表加载失败: ' + (e.message || e)))
  } finally {
    cveLoading.value = false
  }
}

function onTabChange(tab: string) {
  activeTab.value = tab
  if (tab === 'cves' && cveItems.value.length === 0) loadCves()
  if (tab === 'hits' && hitItems.value.length === 0) loadHits()
}

function severityTag(s: string) {
  return (CVE_SEVERITY_TAG as any)[s] || 'info'
}
function severityCn(s: string) {
  return (CVE_SEVERITY as any)[s] || s || '未评级'
}
function sourceCn(s: string) {
  return (CVE_SOURCE as any)[s] || s || '—'
}

function fmtDate(s: string | null) {
  return s ? String(s).replace('T', ' ').slice(0, 19) : '—'
}

// ============================================================
// CVE 详情对话框
// ============================================================
const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref<any>(null)

async function openDetail(cveId: string) {
  detailVisible.value = true
  detailLoading.value = true
  detail.value = null
  try {
    const r: any = await api.getCve(cveId)
    if (r?.success) detail.value = r.data
    else ElMessage.warning(r?.message || '详情加载失败')
  } catch (e: any) {
    ElMessage.error(e?.friendlyMsg || '详情加载失败')
  } finally {
    detailLoading.value = false
  }
}

// ============================================================
// 刷新 CVE 库对话框
// ============================================================
const refreshVisible = ref(false)
const refreshLoading = ref(false)
const refreshForm = reactive({
  days: 7,
  source: 'all',
})
const SOURCE_REFRESH_OPTIONS = [
  { label: '全部（NVD + OSV.dev，推荐）', value: 'all' },
  { label: 'NVD（美国国家漏洞库）', value: 'nvd' },
  { label: 'OSV.dev（开源漏洞库）', value: 'osv' },
]

async function doRefresh() {
  refreshLoading.value = true
  try {
    const r: any = await api.refreshCves({
      days: refreshForm.days,
      source: refreshForm.source,
    })
    ElMessage.success(r?.message || 'CVE 库刷新完成')
    refreshVisible.value = false
    await Promise.all([loadCves(), loadStats()])
  } catch (e: any) {
    ElMessage.error(e?.friendlyMsg || '刷新失败: ' + (e.message || e))
  } finally {
    refreshLoading.value = false
  }
}

// ============================================================
// 搜资产对话框
// ============================================================
const searchVisible = ref(false)
const searchLoading = ref(false)
const searchForm = reactive({
  cve_id: '',
  platforms: [] as string[],
  max_results: 100,
})
const PLATFORM_OPTIONS = Object.entries(PLATFORM).map(([v, l]) => ({ value: v, label: l }))

function openSearchAssets(cveId: string) {
  searchForm.cve_id = cveId
  searchForm.platforms = []
  searchForm.max_results = 100
  searchVisible.value = true
}

async function doSearchAssets() {
  if (!searchForm.cve_id) { ElMessage.warning('CVE-ID 缺失'); return }
  searchLoading.value = true
  try {
    const r: any = await api.searchCveAssets({
      cve_id: searchForm.cve_id,
      platforms: searchForm.platforms,
      max_results: searchForm.max_results,
    })
    ElMessage.success(r?.message || '资产搜索完成')
    searchVisible.value = false
    // 切到命中资产 Tab 并刷新
    activeTab.value = 'hits'
    hitFilters.cve_id = searchForm.cve_id
    hitFilters.page = 1
    await loadHits()
    await loadStats()
  } catch (e: any) {
    ElMessage.error(e?.friendlyMsg || '资产搜索失败: ' + (e.message || e))
  } finally {
    searchLoading.value = false
  }
}

// ============================================================
// 触发扫描对话框
// ============================================================
const scanVisible = ref(false)
const scanLoading = ref(false)
const scanForm = reactive({
  cve_id: '',
  pipeline: 'engine',
})
const PIPELINE_OPTIONS = Object.entries(CVE_PIPELINE).map(([v, l]) => ({ value: v, label: l }))

function openScan(cveId: string) {
  scanForm.cve_id = cveId
  scanForm.pipeline = 'engine'
  scanVisible.value = true
}

async function doScan() {
  if (!scanForm.cve_id) { ElMessage.warning('CVE-ID 缺失'); return }
  try {
    await ElMessageBox.confirm(
      `将对 CVE ${scanForm.cve_id} 的所有待扫描资产启动「${(CVE_PIPELINE as any)[scanForm.pipeline]}」流水线，是否继续？`,
      '触发 CVE 扫描',
      { type: 'warning', confirmButtonText: '确认启动', cancelButtonText: '取消' },
    )
  } catch { return /* 用户取消 */ }

  scanLoading.value = true
  try {
    const r: any = await api.cveScan({
      cve_id: scanForm.cve_id,
      pipeline: scanForm.pipeline,
    })
    ElMessage.success(r?.message || '已触发扫描')
    scanVisible.value = false
    await loadStats()
    if (activeTab.value === 'hits') await loadHits()
  } catch (e: any) {
    ElMessage.error(e?.friendlyMsg || '触发扫描失败: ' + (e.message || e))
  } finally {
    scanLoading.value = false
  }
}

// ============================================================
// 删除 CVE
// ============================================================
async function doDeleteCve(cveId: string) {
  try {
    await ElMessageBox.confirm(
      `确认删除 CVE ${cveId}？将级联删除其所有命中资产记录，不可恢复。`,
      '删除 CVE',
      { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' },
    )
  } catch { return }
  try {
    const r: any = await api.deleteCve(cveId)
    ElMessage.success(r?.message || '已删除')
    await Promise.all([loadCves(), loadStats()])
  } catch (e: any) {
    ElMessage.error(e?.friendlyMsg || '删除失败: ' + (e.message || e))
  }
}

// ============================================================
// Tab 2: 命中资产
// ============================================================
const hitLoading = ref(false)
const hitItems = ref<any[]>([])
const hitTotal = ref(0)
const hitSelected = ref<any[]>([])
const hitFilters = reactive({
  cve_id: '',
  scan_status: '',
  page: 1,
  page_size: 20,
})
const HIT_STATUS_OPTIONS = [
  { label: '全部', value: '' },
  { label: '待扫描', value: 'pending' },
  { label: '扫描中', value: 'scanning' },
  { label: '已完成', value: 'done' },
  { label: '失败', value: 'failed' },
  { label: '已跳过', value: 'skipped' },
]

async function loadHits() {
  hitLoading.value = true
  try {
    const r: any = await api.listCveAssetHits({
      cve_id: hitFilters.cve_id.trim(),
      scan_status: hitFilters.scan_status,
      page: hitFilters.page,
      page_size: hitFilters.page_size,
    })
    if (r?.success && r.data) {
      hitItems.value = r.data.items || []
      hitTotal.value = Number(r.data.total) || 0
    } else {
      hitItems.value = []
      hitTotal.value = 0
      ElMessage.warning(r?.message || '命中资产加载失败')
    }
  } catch (e: any) {
    hitItems.value = []
    hitTotal.value = 0
    ElMessage.error(e?.friendlyMsg || ('命中资产加载失败: ' + (e.message || e)))
  } finally {
    hitLoading.value = false
  }
}

function onHitSelectionChange(rows: any[]) {
  hitSelected.value = rows
}

function hitStatusTag(s: string) {
  return (CVE_SCAN_STATUS_TAG as any)[s] || 'info'
}
function hitStatusCn(s: string) {
  return (CVE_SCAN_STATUS as any)[s] || s || '—'
}

async function doDeleteHit(row: any) {
  if (row.scan_status === 'scanning') {
    ElMessage.warning('正在扫描中，无法删除')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认删除命中资产 ${row.url || row.host}？`,
      '删除命中资产',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch { return }
  try {
    const r: any = await api.deleteCveAssetHit(row.id)
    ElMessage.success(r?.message || '已删除')
    await loadHits()
    await loadStats()
  } catch (e: any) {
    ElMessage.error(e?.friendlyMsg || '删除失败: ' + (e.message || e))
  }
}

async function doBatchScan() {
  if (!hitSelected.value.length) {
    ElMessage.warning('请先勾选要扫描的命中资产')
    return
  }
  // 必须是同一个 CVE 才能批量扫描
  const cveIds = new Set(hitSelected.value.map((x) => x.cve_id))
  if (cveIds.size > 1) {
    ElMessage.warning('批量扫描仅支持同一 CVE，请按 CVE 筛选后再勾选')
    return
  }
  const cveId = hitSelected.value[0]?.cve_id
  if (!cveId) { ElMessage.warning('无法识别 CVE-ID'); return }
  const hitIds = hitSelected.value.map((x) => String(x.id)).filter(Boolean)
  // pending 才能扫
  const pendingHits = hitSelected.value.filter((x) => x.scan_status === 'pending')
  if (pendingHits.length === 0) {
    ElMessage.warning('所选条目中没有「待扫描」状态的资产')
    return
  }
  // 选择 pipeline
  try {
    const action = await ElMessageBox.confirm(
      `将对 ${pendingHits.length} 条「待扫描」资产启动扫描，请选择流水线：`,
      '批量触发扫描',
      {
        type: 'warning',
        confirmButtonText: '自研引擎',
        cancelButtonText: '取消',
        distinguishCancelAndClose: true,
      },
    ).then(() => 'engine').catch((err) => {
      if (err === 'close') return null
      // 二次询问是否单站协作
      return ElMessageBox.confirm(
        '是否改用「单站协作」流水线（权限发现专项）？',
        '选择流水线',
        { confirmButtonText: '单站协作', cancelButtonText: '取消' },
      ).then(() => 'collab').catch(() => null)
    })
    if (!action) return
    scanForm.pipeline = action
  } catch { return }

  scanLoading.value = true
  try {
    const r: any = await api.cveScan({
      cve_id: cveId,
      hit_ids: hitIds,
      pipeline: scanForm.pipeline,
    })
    ElMessage.success(r?.message || '已触发批量扫描')
    await loadHits()
    await loadStats()
  } catch (e: any) {
    ElMessage.error(e?.friendlyMsg || '批量扫描失败: ' + (e.message || e))
  } finally {
    scanLoading.value = false
  }
}

async function doDeleteHits() {
  const rows = hitSelected.value.filter((x) => x.scan_status !== 'scanning')
  if (!rows.length) {
    ElMessage.warning('请先勾选可删除的条目（扫描中不可删）')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认删除 ${rows.length} 条命中资产？不可恢复。`,
      '批量删除',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch { return }
  let ok = 0, fail = 0
  for (const row of rows) {
    try {
      await api.deleteCveAssetHit(row.id)
      ok++
    } catch { fail++ }
  }
  if (ok) ElMessage.success(`已删除 ${ok} 条${fail ? `，失败 ${fail} 条` : ''}`)
  else ElMessage.error(`全部删除失败（${fail} 条）`)
  hitSelected.value = []
  await loadHits()
  await loadStats()
}

// ============================================================
// 初始化
// ============================================================
const emptyCveText = computed(() => {
  if (cveLoading.value) return '加载中…'
  if (cveFilters.keyword.trim() || cveFilters.severity || cveFilters.source) {
    return '没有匹配的 CVE（可调整筛选条件或刷新 CVE 库）'
  }
  return 'CVE 库为空，点击右上角「刷新 CVE 库」开始拉取'
})

const emptyHitText = computed(() => {
  if (hitLoading.value) return '加载中…'
  if (hitFilters.cve_id.trim() || hitFilters.scan_status) {
    return '没有匹配的命中资产（可调整筛选条件）'
  }
  return '暂无命中资产，可在「CVE 库」Tab 中对单个 CVE 触发资产搜索'
})

const severityCards = computed(() => {
  const bs = stats.value.by_severity || {}
  return [
    { key: 'CRITICAL', label: '严重', cls: 'sev-critical' },
    { key: 'HIGH', label: '高危', cls: 'sev-high' },
    { key: 'MEDIUM', label: '中危', cls: 'sev-medium' },
    { key: 'LOW', label: '低危', cls: 'sev-low' },
  ].map((x) => ({ ...x, count: Number(bs[x.key] || 0) }))
})

const sourceCards = computed(() => {
  const bs = stats.value.by_source || {}
  return [
    { key: 'nvd', label: 'NVD' },
    { key: 'osv', label: 'OSV.dev' },
  ].map((x) => ({ ...x, count: Number(bs[x.key] || 0) }))
})

onMounted(async () => {
  await Promise.all([loadStats(), loadCves()])
})
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <h2 class="page-title">CVE 库</h2>
        <p class="muted" style="margin: 4px 0 0 0; line-height: 1.8">
          自动拉取 NVD + OSV.dev 双源 CVE；按 affected 字段在各资产平台搜未修复资产，再一键触发挖掘流水线。
        </p>
      </div>
      <div class="actions">
        <el-button type="primary" :icon="Refresh" @click="refreshVisible = true">
          刷新 CVE 库
        </el-button>
        <el-button :icon="DataAnalysis" @click="loadStats">刷新统计</el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="12" style="margin-bottom: 16px">
      <el-col :span="6">
        <div class="stat-card" style="color: #3b82f6">
          <div class="muted" style="font-size: 12px">CVE 总数</div>
          <div class="stat-num">{{ stats.total || 0 }}</div>
          <div class="muted" style="font-size: 12px">近 7 天新增 {{ stats.recent_7d || 0 }} 条</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card" style="color: #fbbf24">
          <div class="muted" style="font-size: 12px">待扫描资产</div>
          <div class="stat-num">{{ stats.pending_asset_hits || 0 }}</div>
          <div class="muted" style="font-size: 12px">CVE 命中后未触发扫描的资产</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card" style="color: #34d399">
          <div class="muted" style="font-size: 12px">按严重等级分布</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px">
            <el-tag v-for="s in severityCards" :key="s.key"
              :class="s.cls" class="sev-tag" size="small" effect="dark">
              {{ s.label }} {{ s.count }}
            </el-tag>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card" style="color: #a78bfa">
          <div class="muted" style="font-size: 12px">按来源分布</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px">
            <el-tag v-for="s in sourceCards" :key="s.key" size="small" type="info" effect="plain">
              {{ s.label }} {{ s.count }}
            </el-tag>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-tabs v-model="activeTab" type="card" @tab-change="onTabChange">
      <!-- ============= Tab 1: CVE 库 ============= -->
      <el-tab-pane label="CVE 库" name="cves">
        <div class="filter-wrap-card" style="margin-bottom: 14px">
          <el-form :inline="true" size="default">
            <el-form-item label="关键字">
              <el-input
                v-model="cveFilters.keyword"
                placeholder="CVE-ID / 标题 / 描述 / 产品"
                clearable
                style="width: 280px"
                @keyup.enter="cveFilters.page = 1; loadCves()"
                @clear="cveFilters.page = 1; loadCves()"
              />
            </el-form-item>
            <el-form-item label="严重等级">
              <el-select v-model="cveFilters.severity" style="width: 130px"
                @change="cveFilters.page = 1; loadCves()">
                <el-option v-for="o in SEVERITY_OPTIONS" :key="o.value"
                  :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="来源">
              <el-select v-model="cveFilters.source" style="width: 140px"
                @change="cveFilters.page = 1; loadCves()">
                <el-option v-for="o in SOURCE_OPTIONS" :key="o.value"
                  :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :icon="Search" @click="cveFilters.page = 1; loadCves()">
                查询
              </el-button>
              <el-button :icon="Refresh" @click="loadCves">刷新</el-button>
            </el-form-item>
          </el-form>
        </div>

        <el-card>
          <el-table
            :data="cveItems"
            v-loading="cveLoading"
            border stripe size="small"
            empty-text="暂无数据"
            style="width: 100%"
          >
            <el-table-column label="序号" width="60" type="index"
              :index="(i: number) => (cveFilters.page - 1) * cveFilters.page_size + i + 1" />
            <el-table-column prop="cve_id" label="CVE-ID" width="170" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="mono" style="color: #93c5fd">{{ row.cve_id }}</span>
              </template>
            </el-table-column>
            <el-table-column label="等级" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="severityTag(row.cvss_severity)" effect="dark" size="small">
                  {{ severityCn(row.cvss_severity) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="CVSS" width="70" align="center">
              <template #default="{ row }">
                <span v-if="row.cvss_score" class="mono">{{ row.cvss_score }}</span>
                <span v-else class="muted">—</span>
              </template>
            </el-table-column>
            <el-table-column label="来源" width="100">
              <template #default="{ row }">
                <el-tag size="small" type="info" effect="plain">{{ sourceCn(row.source) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" min-width="280" show-overflow-tooltip>
              <template #default="{ row }">
                <span>{{ row.title || row.description?.slice(0, 80) || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="发布时间" width="160">
              <template #default="{ row }">{{ fmtDate(row.published_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="280" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" plain :icon="View"
                  @click="openDetail(row.cve_id)">详情</el-button>
                <el-button size="small" type="success" plain :icon="Search"
                  @click="openSearchAssets(row.cve_id)">搜资产</el-button>
                <el-button size="small" type="warning" plain :icon="Lightning"
                  @click="openScan(row.cve_id)">扫描</el-button>
                <el-button size="small" type="danger" plain :icon="Delete"
                  @click="doDeleteCve(row.cve_id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div v-if="!cveLoading && cveItems.length === 0"
               style="padding: 14px 0 4px; text-align: center">
            <span class="muted">{{ emptyCveText }}</span>
          </div>

          <div v-if="cveTotal > 0" style="display: flex; justify-content: flex-end; margin-top: 14px">
            <el-pagination
              v-model:current-page="cveFilters.page"
              v-model:page-size="cveFilters.page_size"
              layout="total, sizes, prev, pager, next, jumper"
              :total="cveTotal"
              :page-sizes="[10, 20, 50, 100]"
              background small
              @current-change="loadCves"
              @size-change="cveFilters.page = 1; loadCves()"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <!-- ============= Tab 2: 命中资产 ============= -->
      <el-tab-pane label="命中资产" name="hits">
        <div class="filter-wrap-card" style="margin-bottom: 14px">
          <el-form :inline="true" size="default">
            <el-form-item label="CVE-ID">
              <el-input
                v-model="hitFilters.cve_id"
                placeholder="按 CVE-ID 过滤（如 CVE-2024-1234）"
                clearable
                style="width: 220px"
                @keyup.enter="hitFilters.page = 1; loadHits()"
                @clear="hitFilters.page = 1; loadHits()"
              />
            </el-form-item>
            <el-form-item label="扫描状态">
              <el-select v-model="hitFilters.scan_status" style="width: 140px"
                @change="hitFilters.page = 1; loadHits()">
                <el-option v-for="o in HIT_STATUS_OPTIONS" :key="o.value"
                  :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :icon="Search" @click="hitFilters.page = 1; loadHits()">
                查询
              </el-button>
              <el-button :icon="Refresh" @click="loadHits">刷新</el-button>
              <el-button type="warning" plain :icon="Lightning"
                :disabled="!hitSelected.length"
                @click="doBatchScan">批量扫描（{{ hitSelected.length }}）</el-button>
              <el-button type="danger" plain :icon="Delete"
                :disabled="!hitSelected.length"
                @click="doDeleteHits">批量删除（{{ hitSelected.length }}）</el-button>
            </el-form-item>
          </el-form>
        </div>

        <el-card>
          <el-table
            :data="hitItems"
            v-loading="hitLoading"
            border stripe size="small"
            @selection-change="onHitSelectionChange"
            empty-text="暂无数据"
            style="width: 100%"
          >
            <el-table-column type="selection" width="46" reserve-selection />
            <el-table-column label="序号" width="60" type="index"
              :index="(i: number) => (hitFilters.page - 1) * hitFilters.page_size + i + 1" />
            <el-table-column prop="cve_id" label="CVE-ID" width="160" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="mono" style="color: #93c5fd">{{ row.cve_id }}</span>
              </template>
            </el-table-column>
            <el-table-column label="资产 URL" min-width="280" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="mono" style="word-break: break-all">{{ row.url || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="host" label="主机" width="160" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="mono">{{ row.host }}{{ row.port ? ':' + row.port : '' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="muted">{{ row.title || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="平台" width="110">
              <template #default="{ row }">
                <el-tag size="small" type="info" effect="plain">{{ zh(row.platform) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="扫描状态" width="110" align="center">
              <template #default="{ row }">
                <el-tag :type="hitStatusTag(row.scan_status)" effect="dark" size="small">
                  {{ hitStatusCn(row.scan_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="命中时间" width="160">
              <template #default="{ row }">{{ fmtDate(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="danger" plain :icon="Delete"
                  @click="doDeleteHit(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div v-if="!hitLoading && hitItems.length === 0"
               style="padding: 14px 0 4px; text-align: center">
            <span class="muted">{{ emptyHitText }}</span>
          </div>

          <div v-if="hitTotal > 0" style="display: flex; justify-content: flex-end; margin-top: 14px">
            <el-pagination
              v-model:current-page="hitFilters.page"
              v-model:page-size="hitFilters.page_size"
              layout="total, sizes, prev, pager, next, jumper"
              :total="hitTotal"
              :page-sizes="[10, 20, 50, 100]"
              background small
              @current-change="loadHits"
              @size-change="hitFilters.page = 1; loadHits()"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- ============= CVE 详情对话框 ============= -->
    <el-dialog
      v-model="detailVisible"
      title="CVE 详情"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-loading="detailLoading">
        <template v-if="detail">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="CVE-ID">
              <span class="mono" style="color: #93c5fd">{{ detail.cve_id }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="来源">
              <el-tag size="small" type="info" effect="plain">{{ sourceCn(detail.source) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="严重等级">
              <el-tag :type="severityTag(detail.cvss_severity)" effect="dark" size="small">
                {{ severityCn(detail.cvss_severity) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="CVSS 分数">
              <span class="mono">{{ detail.cvss_score || '—' }}</span>
              <span v-if="detail.cvss_vector" class="muted mono"
                style="margin-left: 8px; font-size: 12px">{{ detail.cvss_vector }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="发布时间">{{ fmtDate(detail.published_at) }}</el-descriptions-item>
            <el-descriptions-item label="源更新时间">{{ fmtDate(detail.updated_at_src) }}</el-descriptions-item>
          </el-descriptions>

          <div style="margin-top: 14px">
            <div class="muted" style="margin-bottom: 6px; font-weight: 600">标题</div>
            <div>{{ detail.title || '—' }}</div>
          </div>

          <div style="margin-top: 14px">
            <div class="muted" style="margin-bottom: 6px; font-weight: 600">描述</div>
            <div class="desc-block">{{ detail.description || '—' }}</div>
          </div>

          <div v-if="detail.affected && Object.keys(detail.affected).length" style="margin-top: 14px">
            <div class="muted" style="margin-bottom: 6px; font-weight: 600">受影响产品</div>
            <pre class="json-block">{{ JSON.stringify(detail.affected, null, 2) }}</pre>
          </div>

          <div v-if="detail.references && detail.references.length" style="margin-top: 14px">
            <div class="muted" style="margin-bottom: 6px; font-weight: 600">参考链接</div>
            <div v-for="(r, i) in detail.references" :key="i" style="margin: 4px 0">
              <a :href="r.url || r" target="_blank" rel="noopener" class="ref-link">
                {{ r.url || r }}
              </a>
            </div>
          </div>
        </template>
        <el-empty v-else-if="!detailLoading" description="无详情数据" />
      </div>

      <template #footer>
        <el-button v-if="detail" type="success" plain :icon="Search"
          @click="openSearchAssets(detail.cve_id); detailVisible = false">搜资产</el-button>
        <el-button v-if="detail" type="warning" plain :icon="Lightning"
          @click="openScan(detail.cve_id); detailVisible = false">触发扫描</el-button>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ============= 刷新 CVE 库对话框 ============= -->
    <el-dialog
      v-model="refreshVisible"
      title="刷新 CVE 库"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="拉取天数">
          <el-input-number v-model="refreshForm.days" :min="1" :max="365" />
          <div class="muted" style="font-size: 12px; margin-top: 4px">
            拉取最近 N 天的 CVE（建议 7~30 天）
          </div>
        </el-form-item>
        <el-form-item label="数据源">
          <el-select v-model="refreshForm.source" style="width: 100%">
            <el-option v-for="o in SOURCE_REFRESH_OPTIONS" :key="o.value"
              :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <div class="muted" style="font-size: 12px; line-height: 1.8">
            NVD 需要 API_KEY（在「设置 → LLM 与外部服务」中配置），OSV.dev 免费免 Key。
            拉取耗时较长，请耐心等待。
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="refreshVisible = false">取消</el-button>
        <el-button type="primary" :loading="refreshLoading" @click="doRefresh">开始刷新</el-button>
      </template>
    </el-dialog>

    <!-- ============= 搜资产对话框 ============= -->
    <el-dialog
      v-model="searchVisible"
      title="按 CVE 搜未修复资产"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="CVE-ID">
          <span class="mono" style="color: #93c5fd">{{ searchForm.cve_id }}</span>
        </el-form-item>
        <el-form-item label="资产平台">
          <el-select v-model="searchForm.platforms" multiple style="width: 100%"
            placeholder="留空 = 使用已配置的全部平台">
            <el-option v-for="o in PLATFORM_OPTIONS" :key="o.value"
              :label="o.label" :value="o.value" />
          </el-select>
          <div class="muted" style="font-size: 12px; margin-top: 4px">
            在「设置 → 资产平台」中配置各平台的 API Key
          </div>
        </el-form-item>
        <el-form-item label="最大数量">
          <el-input-number v-model="searchForm.max_results" :min="10" :max="1000" :step="50" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="searchVisible = false">取消</el-button>
        <el-button type="primary" :loading="searchLoading" :icon="Search" @click="doSearchAssets">
          开始搜索
        </el-button>
      </template>
    </el-dialog>

    <!-- ============= 触发扫描对话框 ============= -->
    <el-dialog
      v-model="scanVisible"
      title="触发 CVE 扫描"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="CVE-ID">
          <span class="mono" style="color: #93c5fd">{{ scanForm.cve_id }}</span>
        </el-form-item>
        <el-form-item label="流水线">
          <el-select v-model="scanForm.pipeline" style="width: 100%">
            <el-option v-for="o in PIPELINE_OPTIONS" :key="o.value"
              :label="o.label" :value="o.value" />
          </el-select>
          <div class="muted" style="font-size: 12px; margin-top: 4px">
            engine：自研引擎扫描；collab：单站协作权限发现专项；traffic：流量挖掘
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scanVisible = false">取消</el-button>
        <el-button type="warning" :loading="scanLoading" :icon="Lightning" @click="doScan">
          启动扫描
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.mono {
  font-family: 'JetBrains Mono', Consolas, Monaco, monospace;
}
.desc-block {
  background: rgba(255, 255, 255, 0.04);
  padding: 10px 12px;
  border-radius: 8px;
  line-height: 1.7;
  border: 1px solid rgba(148, 163, 184, 0.12);
  max-height: 220px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
.json-block {
  background: rgba(255, 255, 255, 0.04);
  padding: 10px 12px;
  border-radius: 8px;
  font-family: 'JetBrains Mono', Consolas, Monaco, monospace;
  font-size: 12px;
  color: #cbd5e1;
  line-height: 1.6;
  border: 1px solid rgba(148, 163, 184, 0.12);
  max-height: 220px;
  overflow: auto;
  margin: 0;
}
.ref-link {
  color: #60a5fa;
  word-break: break-all;
  font-family: 'JetBrains Mono', Consolas, Monaco, monospace;
  font-size: 12px;
}
.ref-link:hover {
  color: #93c5fd;
  text-decoration: underline;
}
.el-table {
  --el-table-row-hover-bg-color: rgba(59, 130, 246, 0.10);
}
</style>
