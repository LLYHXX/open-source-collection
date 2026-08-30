import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './styles.css'

// 主题白闪避免：在 mount 前一次性把 data-theme 写到 <html>
try {
  const t = localStorage.getItem('ui.theme') || document.documentElement.getAttribute('data-theme') || 'default'
  document.documentElement.setAttribute('data-theme', t)
  if (t === 'cyber' || t === 'mono') document.body.setAttribute('data-theme', t)
} catch { /* ignore */ }

const app = createApp(App)
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component as any)
}
app.use(router)
app.use(ElementPlus)
app.mount('#app')
