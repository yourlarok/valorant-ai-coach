import { ref } from 'vue'
import { getIdentity } from './api'

const STORAGE_KEY = 'val_player_name'

// 身份状态以后端 GET /api/identity 为准；localStorage 仅作首屏缓存避免闪烁
export const playerName = ref(localStorage.getItem(STORAGE_KEY) || '')
export const onboarded = ref(false)

let initialized = null

export function initIdentity() {
  if (!initialized) {
    initialized = getIdentity()
      .then((data) => {
        onboarded.value = !!data?.onboarded
        playerName.value = data?.name || ''
        localStorage.setItem(STORAGE_KEY, playerName.value)
      })
      .catch(() => {
        // 后端不可达时退回缓存判定，避免把已绑定用户锁在向导里
        onboarded.value = !!playerName.value
      })
  }
  return initialized
}

export function setIdentity(name) {
  playerName.value = name
  onboarded.value = true
  localStorage.setItem(STORAGE_KEY, name)
}
