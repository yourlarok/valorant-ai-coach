<template>
  <span class="ui-tag" :class="`ui-tag--${tone}`">
    <span v-if="dot" class="ui-tag__dot" />
    <slot />
  </span>
</template>

<script setup>
defineProps({
  tone: {
    type: String,
    default: 'neutral',
    validator: (v) =>
      ['neutral', 'accent', 'win', 'loss', 'firstblood', 'warn', 'info'].includes(v),
  },
  dot: { type: Boolean, default: false },
})
</script>

<style scoped>
.ui-tag {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
  padding: 2px var(--sp-2);
  border-radius: var(--r-sm);
  font-size: var(--fs-caption);
  font-weight: 600;
  letter-spacing: 0.05em;
  line-height: 1.5;
  white-space: nowrap;
}
.ui-tag__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
.ui-tag--neutral { background: var(--c-surface-3); color: var(--c-text-muted); }
.ui-tag--accent { background: var(--c-accent-dim); color: var(--c-accent); }
.ui-tag--win { background: var(--c-win-dim); color: var(--c-win); }
.ui-tag--loss { background: var(--c-loss-dim); color: var(--c-loss); }
.ui-tag--firstblood { background: var(--c-firstblood-dim); color: var(--c-firstblood); }
.ui-tag--warn { background: var(--c-warn-dim); color: var(--c-warn); }
.ui-tag--info { background: var(--c-info-dim); color: var(--c-info); }
</style>
