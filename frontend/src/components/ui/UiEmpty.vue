<template>
  <div class="ui-empty">
    <div class="ui-empty__mark cut-corner" aria-hidden="true">
      <slot name="icon">?</slot>
    </div>
    <p class="ui-empty__title">{{ title }}</p>
    <p v-if="description" class="ui-empty__desc">{{ description }}</p>
    <div v-if="$slots.default" class="ui-empty__action">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '暂无数据' },
  description: { type: String, default: '' },
})
</script>

<style scoped>
.ui-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-7) var(--sp-4);
  text-align: center;
}
.ui-empty__mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: var(--c-surface-3);
  color: var(--c-text-faint);
  font-size: var(--fs-h2);
  font-weight: 700;
  margin-bottom: var(--sp-2);
}
.ui-empty__title {
  margin: 0;
  font-size: var(--fs-h3);
  font-weight: 600;
  color: var(--c-text);
}
.ui-empty__desc {
  margin: 0;
  font-size: var(--fs-body);
  color: var(--c-text-muted);
  max-width: 420px;
}
.ui-empty__action { margin-top: var(--sp-3); }
</style>
