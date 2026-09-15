<template>
  <teleport to="body">
    <div class="ui-toast-stack" role="status" aria-live="polite">
      <transition-group name="ui-toast">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="ui-toast cut-corner-tr"
          :class="`ui-toast--${t.tone}`"
        >
          <span class="ui-toast__bar" />
          <span class="ui-toast__msg">{{ t.message }}</span>
        </div>
      </transition-group>
    </div>
  </teleport>
</template>

<script setup>
import { reactive, provide } from 'vue'
import { TOAST_KEY } from './toast'

let seq = 0
const toasts = reactive([])

function dismiss(id) {
  const i = toasts.findIndex((t) => t.id === id)
  if (i !== -1) toasts.splice(i, 1)
}

function push(message, tone = 'info', duration = 3200) {
  const id = ++seq
  toasts.push({ id, message, tone })
  setTimeout(() => dismiss(id), duration)
  return id
}

const api = {
  push,
  success: (msg, duration) => push(msg, 'success', duration),
  error: (msg, duration) => push(msg, 'error', duration),
  info: (msg, duration) => push(msg, 'info', duration),
}

provide(TOAST_KEY, api)
</script>

<style scoped>
.ui-toast-stack {
  position: fixed;
  top: calc(var(--topbar-h) + var(--sp-3));
  right: var(--sp-4);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  pointer-events: none;
}
.ui-toast {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  min-width: 240px;
  max-width: 420px;
  padding: var(--sp-2) var(--sp-3);
  background: var(--c-surface-3);
  border: 1px solid var(--c-border-strong);
  box-shadow: var(--shadow-3);
  font-size: var(--fs-body);
  color: var(--c-text);
}
.ui-toast__bar { width: 3px; align-self: stretch; }
.ui-toast--success .ui-toast__bar { background: var(--c-win); }
.ui-toast--error .ui-toast__bar { background: var(--c-loss); }
.ui-toast--info .ui-toast__bar { background: var(--c-info); }

.ui-toast-enter-active,
.ui-toast-leave-active {
  transition: opacity var(--dur-base) var(--ease-out),
    transform var(--dur-base) var(--ease-out);
}
.ui-toast-enter-from,
.ui-toast-leave-to {
  opacity: 0;
  transform: translateX(16px);
}
</style>
