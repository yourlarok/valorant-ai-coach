import { ref } from 'vue'
import { getSettings } from './api'

// LLM 配置状态共享模块：顶栏徽标与设置页共同消费，
// 设置页保存成功后调用 updateConfigured 让顶栏立即刷新，无需重载页面。
export const configured = ref(false)

export async function loadSettings() {
  const data = await getSettings()
  configured.value = !!data?.configured
  return data
}

export function updateConfigured(value) {
  configured.value = !!value
}
