/** 全局中文 · 枚举字典（aififteen Hunter 汉化包）
 *  - 所有「英文 raw 值 → 中文」映射集中在此，避免散落在各 Vue 文件
 *  - 提供 zh( raw ) 总入口，所有 Views 统一使用 zh(xxx) 查表渲染
 *  - Cyber 模式时调用 en( raw ) 返回英文/等宽风格短词
 */

export type DictFn = (raw: string | null | undefined) => string

// ---------- 一级枚举 ----------
export const TASK_STATUS: Record<string, string> = {
  pending_approval: '待审批', rejected: '已拒绝', pending: '待执行',
  collecting: '收集中', running: '执行中', review: '待复审',
  ai_reviewed: 'AI 已复审', done: '已完成', success: '已完成', failed: '执行失败',
  queued: '排队中', new: '待处理', skipped: '已跳过', approved: '已批准',
}
export const TASK_STATUS_EN: Record<string, string> = {
  pending_approval: 'PEND_APPR', rejected: 'REJECTED', pending: 'QUEUED',
  collecting: 'COLL', running: 'RUN', review: 'REV',
  ai_reviewed: 'AI_REV', done: 'DONE', success: 'DONE', failed: 'FAIL',
  queued: 'QUEUED', new: 'NEW', skipped: 'SKIP', approved: 'APPR',
}
export const VULN_STATUS: Record<string, string> = {
  pending: '待处理', ai_reviewed: 'AI 已复审', approved: '已通过',
  submitted: '已提交', rejected: '已打回',
}
export const VULN_STATUS_EN: Record<string, string> = {
  pending: 'NEW', ai_reviewed: 'AI_REV', approved: 'APPR', submitted: 'SUBMIT', rejected: 'REJ',
}
export const SEVERITY: Record<string, string> = {
  critical: '严重', high: '高危', medium: '中危', low: '低危', info: '信息',
}
export const SEVERITY_EN: Record<string, string> = {
  critical: 'CRIT', high: 'HIGH', medium: 'MED', low: 'LOW', info: 'INFO',
}
export const SEVERITY_TYPE: Record<string, string> = {
  critical: 'danger', high: 'danger', medium: 'warning', low: 'info', info: 'info',
}
export const LIFECYCLE: Record<string, string> = {
  active: '活跃', stale: '陈旧', retired: '退役',
}
export const LIFECYCLE_EN: Record<string, string> = {
  active: 'L.ACT', stale: 'L.STL', retired: 'L.RET',
}
export const LIFECYCLE_TAG: Record<string, string> = {
  active: 'success', stale: 'warning', retired: 'info',
}
export const INTEL_KIND: Record<string, string> = {
  credential: '凭据', endpoint: '端点', fingerprint: '指纹',
  techstack: '技术栈', leak: '泄露', db_schema: '数据库模型',
  pb_audit: 'PowerBuilder 审计', cve: 'CVE 漏洞',
  os_fingerprint: '操作系统指纹', passive_dns: '被动 DNS',
  attack_experience: '攻击经验', unknown: '未分类',
}
export const INTEL_KIND_EN: Record<string, string> = {
  credential: 'CRED', endpoint: 'EP', fingerprint: 'FP',
  techstack: 'STACK', leak: 'LEAK', db_schema: 'SCHEMA',
  pb_audit: 'PB_AUD', cve: 'CVE', os_fingerprint: 'OS_FP',
  passive_dns: 'DNS', attack_experience: 'EXP', unknown: 'UNK',
}
export const MINER_STATUS: Record<string, string> = {
  pending: '待审核', approved: '已批准入库', rejected: '已拒绝', skipped: '已跳过（越权）',
}
export const MINER_STATUS_EN: Record<string, string> = {
  pending: 'PEND', approved: 'INTEL_WR', rejected: 'REJ', skipped: 'SKIP',
}
export const MINER_STATUS_TAG: Record<string, string> = {
  pending: 'warning', approved: 'success', rejected: 'danger', skipped: 'info',
}
export const MINER_KIND: Record<string, string> = {
  credential: '凭据', endpoint: '端点/URL', fingerprint: '指纹',
  techstack: '技术栈', os_fingerprint: '操作系统',
  passive_dns: '被动 DNS', cve: 'CVE', leak: '泄露',
  unknown: '未分类', pb_audit: 'PB 审计', db_schema: 'DB 模型',
}
export const MINER_KIND_EN: Record<string, string> = {
  credential: 'CRED', endpoint: 'EP', fingerprint: 'FP',
  techstack: 'STACK', os_fingerprint: 'OS',
  passive_dns: 'DNS', cve: 'CVE', leak: 'LEAK',
  unknown: 'UNK', pb_audit: 'PB', db_schema: 'DB',
}
export const TASK_MODE: Record<string, string> = {
  engine: '自研引擎', EduSRC: '高校 SRC', 企业SRC: '企业 SRC',
}
export const TASK_SOURCE: Record<string, string> = {
  manual: '手动清单', fofa: 'FOFA', quake: '360 Quake',
  hunter: 'Hunter 鹰图', zoomeye: 'ZoomEye', shodan: 'Shodan',
  censys: 'Censys', all: '六家并发', both: '手动+FOFA', single: '单站协作',
}
export const COLLECT_METHOD: Record<string, string> = {
  auto: '自动判断', fofa_syntax: '平台语法', nl_intent: '自然语言意图',
}
export const MINER_POLICY: Record<string, string> = {
  reverify_only: '仅复检自动（推荐，安全）',
  all_scope: '授权范围内全部自动（无人值守）',
  off: '全手动审批',
  reverify: '仅复检自动（推荐，安全）', /* 兼容旧值 */
  all: '授权范围内全部自动（无人值守）', /* 兼容旧值 */
}
export const MINER_POLICY_EN: Record<string, string> = {
  reverify_only: 'SAFE · REV', all_scope: 'UNATTEND · ALL', off: 'MANUAL',
  reverify: 'SAFE · REV', all: 'UNATTEND · ALL',
}
export const THEME: Record<string, string> = {
  default: 'Default（深色 · 蓝牌）',
  cyber: 'Cyber（赛博终端 · 扫描线）',
  mono: 'Mono Noir（纯黑白灰 · 无彩色）',
}
export const PLATFORM: Record<string, string> = {
  fofa: 'FOFA', quake: '360 Quake', hunter: 'Hunter 鹰图',
  zoomeye: 'ZoomEye', shodan: 'Shodan', censys: 'Censys',
}

// ---------- 通用工具查表函数 ----------
function lookup(tbl: Record<string, string>, raw: unknown, fallback?: string): string {
  if (raw === null || raw === undefined) return fallback ?? ''
  const k = String(raw)
  const hit = tbl[k]
  if (hit) return hit
  const lk = tbl[k.toLowerCase()]
  return lk ?? (fallback ?? k)
}

// 默认（非 Cyber）：返回中文；找不到返回原值
export function zh(raw: unknown, fallback?: string): string {
  const r = String(raw ?? '')
  return (
    lookup(TASK_STATUS, r) ||
    lookup(VULN_STATUS, r) ||
    lookup(SEVERITY, r) ||
    lookup(LIFECYCLE, r) ||
    lookup(INTEL_KIND, r) ||
    lookup(MINER_STATUS, r) ||
    lookup(MINER_KIND, r) ||
    lookup(TASK_MODE, r) ||
    lookup(TASK_SOURCE, r) ||
    lookup(COLLECT_METHOD, r) ||
    lookup(MINER_POLICY, r) ||
    lookup(THEME, r) ||
    lookup(PLATFORM, r) ||
    (fallback ?? r)
  )
}

// Cyber 模式：统一返回短英文/代码风格值；找不到返回原值
export function en(raw: unknown, fallback?: string): string {
  const r = String(raw ?? '')
  return (
    lookup(TASK_STATUS_EN, r) ||
    lookup(VULN_STATUS_EN, r) ||
    lookup(SEVERITY_EN, r) ||
    lookup(LIFECYCLE_EN, r) ||
    lookup(INTEL_KIND_EN, r) ||
    lookup(MINER_STATUS_EN, r) ||
    lookup(MINER_KIND_EN, r) ||
    lookup(MINER_POLICY_EN, r) ||
    (fallback ?? r)
  )
}

// 根据是否 Cyber 自动挑语言，isCyber=false 时全部中文
export function L(isCyber: boolean, raw: unknown, fallback?: string): string {
  return isCyber ? en(raw, fallback) : zh(raw, fallback)
}

// 友好错误文案（HTTP 拦截统一替换）
export const HTTP_ERR: Record<string, string> = {
  400: '请求参数错误',
  401: '未登录或令牌过期，请重新登录',
  403: '无权访问该资源',
  404: '请求的资源不存在',
  405: '接口方法不被允许',
  408: '请求超时，请稍后重试',
  409: '数据冲突，请刷新后重试',
  413: '上传文件过大',
  422: '表单校验失败，请检查字段',
  429: '请求过于频繁，请稍后再试',
  500: '服务器异常，请查看后端日志',
  502: '网关错误',
  503: '服务暂不可用',
  504: '网关超时',
}

export function httpErrMessage(code: number, detail?: string): string {
  const prefix = HTTP_ERR[String(code)] || `请求失败（HTTP ${code}）`
  if (!detail) return prefix
  const clean = String(detail).trim()
  // 后端返回 StandardResponse.message 已有中文时直接显示
  if (/[\u4e00-\u9fa5]/.test(clean) || clean.length > 4) return clean
  return `${prefix}：${clean}`
}

// 常见后端英文错误字段 → 中文映射（HTTP 拦截时二次替换）
export function detailToCn(txt: string): string {
  if (!txt) return txt
  return txt
    .replace(/status 非法，允许值:([^)]+)/g, '状态参数仅支持：$1')
    .replace(/ids 不能为空/g, '请至少勾选 1 条记录')
    .replace(/scope_asset_ids 不能为空[\s\S]{0,60}/g, '启用 Miner 前必须先设置「授权资产域」（限域合规要求）')
    .replace(/daily_budget_max_jobs 必须为[\s\S]{0,40}整数/g, '日预算 daily_budget_max_jobs 必须是 1~200 的整数')
    .replace(/max_runtime_min 必须为[\s\S]{0,40}整数/g, '最大运行时长 max_runtime_min 必须是 5~1440 分钟')
    .replace(/auto_approve 非法值/g, '自动审批策略非法')
    .replace(/访问需要登录[\s\S]{0,30}/g, '公网访问需要密码登录，请先通过 /access 登录')
    .replace(/无效或缺失访问令牌/g, '令牌无效，请在「设置 → 访问令牌」填写正确的 API Token')
}
