<template>
  <div class="ui-tabs">
    <div class="ui-tabs__bar" role="tablist">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="ui-tabs__tab"
        :class="{ 'ui-tabs__tab--active': tab.key === modelValue }"
        role="tab"
        :aria-selected="tab.key === modelValue"
        @click="$emit('update:modelValue', tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>
    <div class="ui-tabs__panel">
      <slot :active="modelValue" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  tabs: { type: Array, required: true },
  modelValue: { type: String, required: true },
})
defineEmits(['update:modelValue'])
</script>

<style scoped>
.ui-tabs__bar {
  display: flex;
  gap: var(--sp-1);
  border-bottom: 1px solid var(--c-border);
}
.ui-tabs__tab {
  position: relative;
  background: transparent;
  border: 0;
  border-radius: 0;
  padding: var(--sp-2) var(--sp-3);
  font-size: var(--fs-body);
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--c-text-muted);
  cursor: pointer;
  transition: color var(--dur-fast) var(--ease-out);
}
.ui-tabs__tab:hover { background: transparent; color: var(--c-text); }
.ui-tabs__tab--active { color: var(--c-accent); }
.ui-tabs__tab--active::after {
  content: '';
  position: absolute;
  left: var(--sp-2);
  right: var(--sp-2);
  bottom: -1px;
  height: 2px;
  background: var(--c-accent);
  clip-path: polygon(0 0, calc(100% - 6px) 0, 100% 100%, 0 100%);
}
.ui-tabs__panel { padding-top: var(--sp-4); }
</style>
