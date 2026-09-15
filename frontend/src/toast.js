import { reactive } from 'vue'

// 模块级单例：任何组件（无论是否在 UiToast 子树内）都能直接 push，
// UiToast 只负责渲染这份状态，无挂载时序耦合。
export const toasts = reactive([])

let seq = 0

export function dismissToast(id) {
  const i = toasts.findIndex((t) => t.id === id)
  if (i !== -1) toasts.splice(i, 1)
}

export function pushToast(message, tone = 'info', duration = 3200) {
  const id = ++seq
  toasts.push({ id, message, tone })
  setTimeout(() => dismissToast(id), duration)
  return id
}

export const toastApi = {
  push: pushToast,
  success: (msg, duration) => pushToast(msg, 'success', duration),
  error: (msg, duration) => pushToast(msg, 'error', duration),
  info: (msg, duration) => pushToast(msg, 'info', duration),
}
