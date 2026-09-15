<template>
  <div class="ui-skeleton" :style="{ width }">
    <div
      v-for="i in lines"
      :key="i"
      class="ui-skeleton__line"
      :style="{ height, width: i === lines && lines > 1 ? '60%' : '100%' }"
    />
  </div>
</template>

<script setup>
defineProps({
  lines: { type: Number, default: 3 },
  height: { type: String, default: '14px' },
  width: { type: String, default: '100%' },
})
</script>

<style scoped>
.ui-skeleton { display: flex; flex-direction: column; gap: var(--sp-2); }
.ui-skeleton__line {
  border-radius: var(--r-sm);
  background: linear-gradient(
    90deg,
    var(--c-surface-3) 25%,
    var(--c-border) 50%,
    var(--c-surface-3) 75%
  );
  background-size: 200% 100%;
  animation: ui-skeleton-shimmer 1.4s var(--ease-out) infinite;
}
@keyframes ui-skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
