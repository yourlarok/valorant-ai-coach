<template>
  <button
    class="ui-btn"
    :class="[`ui-btn--${variant}`, `ui-btn--${size}`, { 'cut-corner': cut }]"
    :type="type"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'ghost', 'subtle', 'danger'].includes(v),
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md'].includes(v),
  },
  type: { type: String, default: 'button' },
  disabled: { type: Boolean, default: false },
  cut: { type: Boolean, default: true },
})
</script>

<style scoped>
.ui-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  border: 1px solid transparent;
  border-radius: var(--r-sm);
  font-family: var(--font-ui);
  font-weight: 600;
  letter-spacing: 0.06em;
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out),
    border-color var(--dur-fast) var(--ease-out),
    color var(--dur-fast) var(--ease-out);
  white-space: nowrap;
}
.ui-btn--md { padding: var(--sp-2) var(--sp-4); font-size: var(--fs-body); }
.ui-btn--sm { padding: var(--sp-1) var(--sp-3); font-size: var(--fs-caption); }

.ui-btn--primary { background: var(--c-accent); color: var(--c-on-accent); }
.ui-btn--primary:hover:not(:disabled) { background: var(--c-accent-hover); }
.ui-btn--primary:active:not(:disabled) { background: var(--c-accent-active); }

.ui-btn--danger { background: transparent; border-color: var(--c-loss); color: var(--c-loss); }
.ui-btn--danger:hover:not(:disabled) { background: var(--c-loss-dim); }

.ui-btn--ghost { background: transparent; border-color: var(--c-border-strong); color: var(--c-text); }
.ui-btn--ghost:hover:not(:disabled) { border-color: var(--c-accent); color: var(--c-accent); }

.ui-btn--subtle { background: var(--c-surface-3); color: var(--c-text); }
.ui-btn--subtle:hover:not(:disabled) { background: var(--c-border-strong); }

.ui-btn:disabled { opacity: 0.45; cursor: not-allowed; }
</style>
