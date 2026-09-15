import { toastApi } from '../../toast'

// 模块级单例，无 provide/inject 作用域与时序要求
export function useToast() {
  return toastApi
}
