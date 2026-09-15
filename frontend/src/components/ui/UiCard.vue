<template>
  <section class="ui-card" :class="{ 'ui-card--flat': flat, 'cut-corner-tr': cut }">
    <header v-if="title || $slots.actions" class="ui-card__head">
      <h3 class="ui-card__title">{{ title }}</h3>
      <div v-if="$slots.actions" class="ui-card__actions">
        <slot name="actions" />
      </div>
    </header>
    <div class="ui-card__body" :class="{ 'ui-card__body--flush': flush }">
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  flat: { type: Boolean, default: false },
  flush: { type: Boolean, default: false },
  cut: { type: Boolean, default: false },
})
</script>

<style scoped>
.ui-card {
  background: var(--c-surface-2);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  box-shadow: var(--shadow-1);
  overflow: hidden;
}
.ui-card--flat {
  background: var(--c-surface-1);
  box-shadow: none;
}
.ui-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  border-bottom: 1px solid var(--c-border);
}
.ui-card__title {
  margin: 0;
  font-size: var(--fs-h3);
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--c-text);
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}
.ui-card__title::before {
  content: '';
  width: 3px;
  height: 14px;
  background: var(--c-accent);
}
.ui-card__actions { display: flex; align-items: center; gap: var(--sp-2); }
.ui-card__body { padding: var(--sp-4); }
.ui-card__body--flush { padding: 0; }
</style>
