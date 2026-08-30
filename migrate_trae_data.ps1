# ============================================================
# TRAE 数据迁移脚本
# 从 TRAE SOLO CN 迁移到 TRAE IDE (TraeCode)
# ============================================================
# 使用方法：
#   1. 先关闭 TRAE SOLO CN（必须！）
#   2. 右键点击此脚本，选择 "使用 PowerShell 运行"
#   3. 按照提示操作
# ============================================================

$ErrorActionPreference = "Stop"

# 颜色输出函数
function Write-ColorOutput($ForegroundColor, $Message) {
    Write-Host $Message -ForegroundColor $ForegroundColor
}

function Write-Success($Message) { Write-ColorOutput Green "✅ $Message" }
function Write-Warning($Message) { Write-ColorOutput Yellow "⚠️  $Message" }
function Write-Error($Message) { Write-ColorOutput Red "❌ $Message" }
function Write-Info($Message) { Write-ColorOutput Cyan "ℹ️  $Message" }
function Write-Step($Message) { Write-ColorOutput Magenta "`n📌 $Message" }

# ============================================================
# 配置路径
# ============================================================
$sourceName = "TRAE SOLO CN"
$targetName = "TRAE IDE"

$sourceAppData = "$env:APPDATA\TRAE SOLO CN"
$targetAppData = "$env:APPDATA\Trae CN"

$sourceDbRel = "ModularData\ai-agent\database.db"
$targetDbRel = "ModularData\ai-agent\database.db"

# 需要迁移的文件/目录列表（相对路径）
$itemsToMigrate = @(
    @{ Path = "ModularData\ai-agent\database.db"; Type = "File"; Name = "对话历史数据库" },
    @{ Path = "ModularData\ai-agent\database.db-wal"; Type = "File"; Name = "对话历史 WAL" },
    @{ Path = "ModularData\ai-agent\database.db-shm"; Type = "File"; Name = "对话历史 SHM" },
    @{ Path = "Preferences"; Type = "File"; Name = "偏好设置" },
    @{ Path = "Local State"; Type = "File"; Name = "本地状态" },
    @{ Path = "Local Storage\config.db"; Type = "File"; Name = "本地存储配置" },
    @{ Path = "User\History"; Type = "Directory"; Name = "历史记录" },
    @{ Path = "User\workspaceStorage"; Type = "Directory"; Name = "工作区存储" },
    @{ Path = "User\snippets"; Type = "Directory"; Name = "代码片段" }
)

# ============================================================
# 检查是否以管理员身份运行
# ============================================================
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warning "建议以管理员身份运行此脚本（右键 -> 以管理员身份运行）"
    $confirm = Read-Host "是否继续？(y/n)"
    if ($confirm -ne "y") {
        Write-Host "脚本已取消"
        exit
    }
}

# ============================================================
# 开场信息
# ============================================================
Clear-Host
Write-ColorOutput Cyan @"
╔══════════════════════════════════════════════════════════╗
║           TRAE 数据迁移工具                                ║
║  从 $sourceName  →  $targetName                            ║
╚══════════════════════════════════════════════════════════╝
"@

Write-Host ""
Write-Info "源目录: $sourceAppData"
Write-Info "目标目录: $targetAppData"
Write-Host ""

# ============================================================
# 检查源目录和目标目录是否存在
# ============================================================
Write-Step "检查目录..."

if (-not (Test-Path $sourceAppData)) {
    Write-Error "源目录不存在: $sourceAppData"
    Read-Host "按回车键退出"
    exit
}
Write-Success "源目录存在"

if (-not (Test-Path $targetAppData)) {
    Write-Error "目标目录不存在: $targetAppData"
    Write-Info "请先安装并启动一次 TRAE IDE"
    Read-Host "按回车键退出"
    exit
}
Write-Success "目标目录存在"

# ============================================================
# 检查源软件是否在运行
# ============================================================
Write-Step "检查 $sourceName 是否在运行..."

$processes = Get-Process | Where-Object { 
    $_.ProcessName -like "*TRAE*" -or 
    $_.ProcessName -like "*SOLO*" -or
    $_.MainWindowTitle -like "*TRAE SOLO*"
}

if ($processes.Count -gt 0) {
    Write-Warning "检测到可能相关的进程正在运行："
    $processes | ForEach-Object { Write-Host "  - $($_.ProcessName) (PID: $($_.Id))" }
    Write-Host ""
    Write-Warning "为了安全迁移对话历史数据库，请先关闭 $sourceName"
    $confirm = Read-Host "是否仍然继续？(数据库文件可能复制失败) (y/n)"
    if ($confirm -ne "y") {
        Write-Host "请先关闭 $sourceName，然后重新运行此脚本"
        Read-Host "按回车键退出"
        exit
    }
} else {
    Write-Success "未检测到 $sourceName 进程"
}

# ============================================================
# 选择迁移内容
# ============================================================
Write-Step "选择迁移内容"
Write-Host ""
Write-Host "请选择要迁移的内容："
Write-Host "  1. 全部迁移（对话历史 + 设置配置）"
Write-Host "  2. 仅迁移对话历史"
Write-Host "  3. 仅迁移设置配置"
Write-Host ""

$choice = Read-Host "请输入选项 (1/2/3，默认 1)"
if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "1" }

$migrateDb = $false
$migrateSettings = $false

switch ($choice) {
    "1" { $migrateDb = $true; $migrateSettings = $true }
    "2" { $migrateDb = $true }
    "3" { $migrateSettings = $true }
    default { 
        Write-Error "无效选项"
        Read-Host "按回车键退出"
        exit
    }
}

# ============================================================
# 备份目标数据
# ============================================================
Write-Step "备份目标数据..."

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "$env:USERPROFILE\trae_backup_$timestamp"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

Write-Info "备份目录: $backupDir"

# 备份目标数据库
$targetDb = Join-Path $targetAppData $targetDbRel
if (Test-Path $targetDb) {
    $targetDbBackup = Join-Path $backupDir "database.db"
    Copy-Item $targetDb $targetDbBackup -Force
    Write-Success "已备份目标数据库"
}

# 备份目标配置文件
$settingsFiles = @("Preferences", "Local State")
foreach ($file in $settingsFiles) {
    $src = Join-Path $targetAppData $file
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $backupDir $file) -Force
    }
}
Write-Success "已备份目标配置文件"

# ============================================================
# 开始迁移
# ============================================================
Write-Step "开始迁移..."

$successCount = 0
$skipCount = 0
$failCount = 0
$failedItems = @()

foreach ($item in $itemsToMigrate) {
    $itemPath = $item.Path
    $itemType = $item.Type
    $itemName = $item.Name
    
    # 根据选择跳过某些项
    $isDbItem = $itemPath -like "*database.db*"
    $isSettingItem = -not $isDbItem
    
    if ($isDbItem -and -not $migrateDb) { continue }
    if ($isSettingItem -and -not $migrateSettings) { continue }
    
    $srcPath = Join-Path $sourceAppData $itemPath
    $dstPath = Join-Path $targetAppData $itemPath
    
    if (-not (Test-Path $srcPath)) {
        Write-Warning "源文件不存在，跳过: $itemName"
        $skipCount++
        continue
    }
    
    # 确保目标目录存在
    $dstDir = Split-Path $dstPath -Parent
    if (-not (Test-Path $dstDir)) {
        New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    }
    
    try {
        if ($itemType -eq "File") {
            Copy-Item $srcPath $dstPath -Force
        } else {
            Copy-Item $srcPath $dstPath -Recurse -Force
        }
        Write-Success "已迁移: $itemName"
        $successCount++
    } catch {
        Write-Error "迁移失败: $itemName - $($_.Exception.Message)"
        $failCount++
        $failedItems += $itemName
    }
}

# ============================================================
# 迁移 .trae-cn 下的扩展配置（如果有）
# ============================================================
# 注意：.trae-cn 目录是共享的，一般不需要迁移扩展
# 但这里检查一下是否有额外的 skill 配置需要同步

# ============================================================
# 总结
# ============================================================
Write-Step "迁移完成！"
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-ColorOutput Green "  成功: $successCount 项"
Write-ColorOutput Yellow "  跳过: $skipCount 项"
Write-ColorOutput Red "  失败: $failCount 项"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""

if ($failCount -gt 0) {
    Write-Warning "以下项目迁移失败："
    $failedItems | ForEach-Object { Write-Host "  - $_" }
    Write-Host ""
}

Write-Info "备份位置: $backupDir"
Write-Info "如果迁移后有问题，可以从备份目录恢复"
Write-Host ""
Write-ColorOutput Cyan "💡 提示：请启动 TRAE IDE 检查数据是否正常迁移"
Write-Host ""

Read-Host "按回车键退出"
