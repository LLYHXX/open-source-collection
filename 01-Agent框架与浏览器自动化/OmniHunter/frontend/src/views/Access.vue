<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const route = useRoute()
const router = useRouter()

// mode: 'setup' 首次设密码 / 'login' 登录
const mode = ref<'setup' | 'login'>('login')
const password = ref('')
const confirmPwd = ref('')
const loading = ref(false)

onMounted(async () => {
  const m = route.query.mode as string
  if (m === 'setup') {
    mode.value = 'setup'
    return
  }
  // 查询后端是否已设密码，决定显示哪个模式
  try {
    const s = await api.accessStatus()
    mode.value = s.password_set ? 'login' : 'setup'
  } catch {
    mode.value = 'login'
  }
})

async function submit() {
  if (!password.value) {
    ElMessage.warning('请输入密码')
    return
  }
  if (mode.value === 'setup' && password.value !== confirmPwd.value) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    const res =
      mode.value === 'setup'
        ? await api.accessSetup({ password: password.value })
        : await api.accessLogin({ password: password.value })
    localStorage.setItem('omnihunter_session', res.session_token)
    ElMessage.success(mode.value === 'setup' ? '密码设置成功' : '登录成功')
    router.push('/')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="access-wrap">
    <el-card class="access-card" shadow="always">
      <div class="logo">OmniHunter</div>
      <h3 class="title">{{ mode === 'setup' ? '设置访问密码' : '登录' }}</h3>
      <el-form @submit.prevent="submit">
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            placeholder="访问密码"
            show-password
            size="large"
          />
        </el-form-item>
        <el-form-item v-if="mode === 'setup'">
          <el-input
            v-model="confirmPwd"
            type="password"
            placeholder="确认密码"
            show-password
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click="submit"
            size="large"
            style="width: 100%"
          >
            {{ mode === 'setup' ? '设置并登录' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
      <p v-if="mode === 'setup'" class="hint">
        首次使用需设置访问密码，用于公网访问验证。本地（电脑）访问无需密码。
      </p>
      <p v-else class="hint">公网访问需密码验证，本地访问免密。</p>
    </el-card>
  </div>
</template>

<style scoped>
.access-wrap {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #001529;
}
.access-card {
  width: 380px;
}
.logo {
  text-align: center;
  font-size: 24px;
  font-weight: 700;
  color: #001529;
  margin-bottom: 8px;
}
.title {
  text-align: center;
  font-size: 16px;
  color: #606266;
  margin: 0 0 20px 0;
  font-weight: 500;
}
.hint {
  font-size: 12px;
  color: #909399;
  margin: 8px 0 0 0;
  text-align: center;
  line-height: 1.5;
}
</style>
