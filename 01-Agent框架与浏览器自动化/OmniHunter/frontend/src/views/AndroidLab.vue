<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

// ===== 环境状态 =====
const env = ref<any>(null)
const bootstrapJobId = ref('')
const job = ref<any>(null)
let jobTimer: number | undefined

async function loadEnv() {
  try {
    const res = await api.androidStatus()
    env.value = res.data
  } catch (e: any) {
    ElMessage.error('环境检测失败: ' + (e.message || e))
  }
}

async function runBootstrap() {
  try {
    await ElMessageBox.confirm(
      '将自动下载并配置 JDK17 + Android SDK 命令行工具 + platform-tools + emulator（约 400MB，需网络）。',
      '一键引导 Android 环境',
      { confirmButtonText: '开始', cancelButtonText: '取消', type: 'info' },
    )
  } catch {
    return
  }
  const res = await api.androidBootstrap(true)
  bootstrapJobId.value = res.data.job_id
  ElMessage.success('引导任务已启动')
  startJobPolling()
}

function startJobPolling() {
  stopJobPolling()
  jobTimer = window.setInterval(async () => {
    if (!bootstrapJobId.value) return
    try {
      const res = await api.androidJob(bootstrapJobId.value)
      job.value = res.data
      if (res.data.status === 'done' || res.data.status === 'failed') {
        const { status } = res.data
        bootstrapJobId.value = ''
        stopJobPolling()
        await loadEnv()
        status === 'done'
          ? ElMessage.success('Android 环境引导完成')
          : ElMessage.error('引导失败，详见日志')
      }
    } catch {
      /* 轮询失败忽略 */
    }
  }, 2000)
}
function stopJobPolling() {
  if (jobTimer) {
    clearInterval(jobTimer)
    jobTimer = undefined
  }
}

// ===== 系统镜像 =====
const installingImage = ref('')
async function installImage(pkg: string) {
  installingImage.value = pkg
  try {
    await api.androidInstallImage(pkg)
    ElMessage.info('镜像安装已开始（约 1.3~1.8GB），完成后请刷新')
  } finally {
    installingImage.value = ''
  }
}
function isImageInstalled(pkg: string) {
  return env.value?.installed_images?.includes(pkg)
}

// ===== AVD 管理 =====
const form = reactive({
  name: '',
  image: 'system-images;android-30;google_apis;x86_64',
  memory_mb: 2048,
  cores: 2,
  width: 1080,
  height: 2340,
  density: 440,
})
const headless = ref(false)
const withProxy = ref(true)
const creating = ref(false)

async function loadAvds() {
  await loadEnv()
}

async function createAvd() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写 AVD 名称')
    return
  }
  creating.value = true
  try {
    await api.androidCreateAvd({ ...form, name: form.name.trim() })
    ElMessage.success(`AVD ${form.name} 创建成功`)
    form.name = ''
    await loadAvds()
  } catch (e: any) {
    ElMessage.error('创建失败: ' + (e.response?.data?.detail || e.message || e))
  } finally {
    creating.value = false
  }
}

async function startAvd(name: string) {
  try {
    const res = await api.androidStartAvd(name, {
      headless: headless.value,
      proxy: withProxy.value,
      proxy_port: 8082,
      install_cert: withProxy.value,
    })
    ElMessage.success(res.data.note || '启动中')
    await loadAvds()
  } catch (e: any) {
    ElMessage.error('启动失败: ' + (e.response?.data?.detail || e.message || e))
  }
}

async function stopAvd(name: string) {
  await api.androidStopAvd(name)
  ElMessage.success(`已停止 ${name}`)
  await loadAvds()
}

async function deleteAvd(name: string) {
  try {
    await ElMessageBox.confirm(`确认删除 AVD「${name}」？此操作不可恢复。`, '删除', {
      type: 'warning',
    })
  } catch {
    return
  }
  await api.androidDeleteAvd(name)
  ElMessage.success('已删除')
  await loadAvds()
}

// ===== 设备 / APP / 抓包 =====
const devices = ref<any[]>([])
const apkFile = ref<File | null>(null)
const installing = ref(false)
const packages = ref<string[]>([])
const trafficRunning = ref(false)
const trafficText = ref('')

async function refreshDevices() {
  try {
    const res = await api.androidDevices()
    devices.value = res.data.devices
  } catch {
    devices.value = []
  }
}

async function onApkChange(file: any) {
  apkFile.value = file.raw
}

async function installApk() {
  if (!apkFile.value) {
    ElMessage.warning('请选择 APK 文件')
    return
  }
  const d = devices.value.find((x) => x.state === 'device')
  if (!d) {
    ElMessage.warning('没有在线设备，请先启动 AVD')
    return
  }
  installing.value = true
  try {
    await api.androidInstallApk(d.serial, apkFile.value)
    ElMessage.success(`APK 已安装到 ${d.serial}`)
  } catch (e: any) {
    ElMessage.error('安装失败: ' + (e.response?.data?.detail || e.message || e))
  } finally {
    installing.value = false
  }
}

async function listApps() {
  const d = devices.value.find((x) => x.state === 'device')
  if (!d) {
    ElMessage.warning('没有在线设备')
    return
  }
  const res = await api.androidListApps(d.serial)
  packages.value = res.data.packages
  ElMessage.success(`共 ${packages.value.length} 个第三方应用`)
}

async function launchApp(pkg: string) {
  const d = devices.value.find((x) => x.state === 'device')
  if (!d) return
  await api.androidLaunchApp({ serial: d.serial, package: pkg })
  ElMessage.success(`已启动 ${pkg}`)
}

async function uninstallApp(pkg: string) {
  const d = devices.value.find((x) => x.state === 'device')
  if (!d) return
  await api.androidUninstallApp({ serial: d.serial, package: pkg })
  ElMessage.success(`已卸载 ${pkg}`)
  packages.value = packages.value.filter((p) => p !== pkg)
}

async function trafficStart() {
  const res = await api.androidTrafficStart(8082)
  trafficRunning.value = true
  trafficText.value = res.message
  ElMessage.success('流量录制已开启（mitmproxy :8082）')
}

async function trafficStop() {
  await api.androidTrafficStop()
  trafficRunning.value = false
  ElMessage.success('录制已停止')
}

async function trafficRead() {
  const res = await api.androidTraffic('')
  trafficText.value = res.data.traffic
}

onMounted(() => {
  loadEnv()
  refreshDevices()
})
onUnmounted(() => {
  stopJobPolling() // 清理轮询定时器，防内存泄漏
})
</script>

<template>
  <div>
    <h2 class="page-title">移动靶场</h2>

    <el-card style="margin-bottom: 16px">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>Android 环境（模拟器运行时）</span>
          <div>
            <el-button size="small" @click="loadEnv">刷新检测</el-button>
            <el-button size="small" type="primary" :disabled="!!bootstrapJobId" @click="runBootstrap">
              一键引导安装
            </el-button>
          </div>
        </div>
      </template>
      <template v-if="env">
        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px">
          <el-tag :type="env.sdk_found ? 'success' : 'danger'" effect="dark" size="small">
            SDK {{ env.sdk_found ? '已就绪' : '未安装' }}
          </el-tag>
          <el-tag :type="env.java_ok ? 'success' : 'danger'" effect="dark" size="small">
            JDK {{ env.java_ok ? 'OK' : '缺失' }}
          </el-tag>
          <el-tag v-for="(v, k) in env.tools" :key="k" :type="v ? 'success' : 'info'" effect="plain" size="small">
            {{ k }} {{ v ? '✓' : '×' }}
          </el-tag>
          <el-tag :type="env.mitmproxy_cert_exists ? 'success' : 'info'" effect="plain" size="small">
            mitmproxy CA {{ env.mitmproxy_cert_exists ? '已生成' : '未生成（启动一次抓包即生成）' }}
          </el-tag>
        </div>
        <p class="muted" v-if="env.sdk_path">SDK 路径：{{ env.sdk_path }}</p>

        <div v-if="bootstrapJobId || job" style="margin-bottom: 8px">
          <el-progress :percentage="job?.progress || 0" :status="job?.status === 'failed' ? 'exception' : undefined" />
          <pre class="muted" style="white-space: pre-wrap; max-height: 120px; overflow: auto; font-size: 12px">{{ job?.log }}</pre>
        </div>
      </template>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header>系统镜像（google_apis 系可 root，便于装入 CA 证书）</template>
      <el-table :data="env?.recommended_images || []" border size="small">
        <el-table-column prop="pkg" label="镜像包名" min-width="280" />
        <el-table-column prop="label" label="说明" min-width="200" />
        <el-table-column prop="size_hint" label="体积" width="90" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="isImageInstalled(row.pkg) ? 'success' : 'info'" size="small">
              {{ isImageInstalled(row.pkg) ? '已安装' : '未安装' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" :disabled="!!isImageInstalled(row.pkg)" :loading="installingImage === row.pkg"
              @click="installImage(row.pkg)">
              安装
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header>创建虚拟机（AVD · 内存/CPU/分辨率自定义）</template>
      <el-form :inline="true" size="small">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="如 mall-app-lab" style="width: 160px" />
        </el-form-item>
        <el-form-item label="系统镜像">
          <el-select v-model="form.image" style="width: 320px">
            <el-option v-for="img in env?.recommended_images || []" :key="img.pkg" :label="img.label" :value="img.pkg" />
          </el-select>
        </el-form-item>
        <el-form-item label="内存 MB">
          <el-input-number v-model="form.memory_mb" :min="256" :max="16384" :step="256" />
        </el-form-item>
        <el-form-item label="CPU 核心">
          <el-input-number v-model="form.cores" :min="1" :max="16" />
        </el-form-item>
        <el-form-item label="分辨率">
          <el-input-number v-model="form.width" :min="320" :max="2160" :step="20" style="width: 110px" />
          <span class="muted" style="margin: 0 4px">x</span>
          <el-input-number v-model="form.height" :min="480" :max="3840" :step="20" style="width: 110px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="creating" :disabled="!env?.tools_ready" @click="createAvd">
            创建
          </el-button>
        </el-form-item>
      </el-form>
      <div style="display: flex; gap: 16px; margin-bottom: 8px">
        <el-checkbox v-model="headless">无头模式（服务器部署）</el-checkbox>
        <el-checkbox v-model="withProxy">自动挂 mitmproxy 抓包代理 + 装系统证书</el-checkbox>
      </div>
      <el-table :data="env?.avds || []" border size="small">
        <el-table-column prop="0" label="AVD 名称" />
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button size="small" type="success" :disabled="!env?.tools_ready" @click="startAvd(row[0])">启动</el-button>
            <el-button size="small" @click="stopAvd(row[0])">停止</el-button>
            <el-button size="small" type="danger" @click="deleteAvd(row[0])">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <p class="muted" style="margin-top: 8px">
        启动时自动分配 console 端口（serial 如 emulator-5554）；挂代理后所有 APP 流量经 mitmproxy 录制，可在下方读取。
      </p>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>设备与 APP</span>
          <el-button size="small" @click="refreshDevices">刷新设备</el-button>
        </div>
      </template>
      <el-table :data="devices" border size="small" style="margin-bottom: 12px">
        <el-table-column prop="serial" label="Serial" width="160" />
        <el-table-column prop="model" label="型号" />
        <el-table-column prop="state" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.state === 'device' ? 'success' : 'warning'" size="small">{{ row.state }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 12px">
        <el-upload :auto-upload="false" :on-change="onApkChange" :show-file-list="false" accept=".apk">
          <el-button size="small">选择 APK</el-button>
        </el-upload>
        <span class="muted" v-if="apkFile">{{ apkFile.name }}</span>
        <el-button size="small" type="primary" :loading="installing" @click="installApk">安装 APK</el-button>
        <el-button size="small" @click="listApps">列出第三方应用</el-button>
      </div>
      <div v-if="packages.length" style="max-height: 260px; overflow: auto">
        <div v-for="p in packages" :key="p"
          style="display: flex; justify-content: space-between; padding: 4px 8px; border-bottom: 1px solid rgba(255,255,255,0.06)">
          <span>{{ p }}</span>
          <span>
            <el-button size="small" text type="primary" @click="launchApp(p)">启动</el-button>
            <el-button size="small" text type="danger" @click="uninstallApp(p)">卸载</el-button>
          </span>
        </div>
      </div>
    </el-card>

    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>流量录制（mitmproxy :8082 · 与攻击探测端共用捕获通道）</span>
          <div>
            <el-button size="small" type="primary" :disabled="trafficRunning" @click="trafficStart">开始录制</el-button>
            <el-button size="small" :disabled="!trafficRunning" @click="trafficStop">停止</el-button>
            <el-button size="small" @click="trafficRead">读取流量</el-button>
          </div>
        </div>
      </template>
      <el-input v-model="trafficText" type="textarea" :rows="10" readonly placeholder="启动 AVD（勾选代理）并操作 APP 后，点击「读取流量」查看录制的 HTTP/HTTPS 请求" />
      <p class="muted" style="margin-top: 8px">
        工作流：创建 AVD → 启动（自动代理+证书）→ 安装并操作目标 APP/小程序 → 录制流量 → 回灌攻击探测流水线复现漏洞。
      </p>
    </el-card>
  </div>
</template>
