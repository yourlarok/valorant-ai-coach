import { inject } from 'vue'

export const TOAST_KEY = Symbol('ui-toast')

export function useToast() {
  const toast = inject(TOAST_KEY)
  if (!toast) {
    throw new Error('useToast() 必须在挂载了 <UiToast /> 的组件树内使用')
  }
  return toast
}
