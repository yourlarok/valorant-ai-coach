<template>
  <div class="ui-table-wrap">
    <table class="ui-table">
      <thead>
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            :style="{ width: col.width, textAlign: col.align || 'left' }"
          >
            {{ col.label }}
          </th>
        </tr>
      </thead>
      <tbody v-if="rows.length">
        <tr v-for="(row, i) in rows" :key="rowKey ? row[rowKey] : i">
          <td
            v-for="col in columns"
            :key="col.key"
            :class="{ num: col.numeric !== false }"
            :style="{ textAlign: col.align || 'left' }"
          >
            <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]" :column="col">
              {{ row[col.key] }}
            </slot>
          </td>
        </tr>
      </tbody>
      <tbody v-else>
        <tr>
          <td class="ui-table__empty" :colspan="columns.length">{{ emptyText }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  rowKey: { type: String, default: '' },
  emptyText: { type: String, default: '暂无数据' },
})
</script>

<style scoped>
.ui-table-wrap { width: 100%; overflow-x: auto; }
.ui-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-body);
}
.ui-table th {
  padding: var(--sp-2) var(--sp-3);
  font-size: var(--fs-caption);
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--c-text-muted);
  text-transform: uppercase;
  border-bottom: 1px solid var(--c-border-strong);
  white-space: nowrap;
}
.ui-table td {
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--c-border);
  color: var(--c-text);
  white-space: nowrap;
}
.ui-table tbody tr {
  transition: background var(--dur-fast) var(--ease-out);
}
.ui-table tbody tr:hover { background: var(--c-surface-3); }
.ui-table__empty {
  padding: var(--sp-5) var(--sp-3);
  text-align: center;
  color: var(--c-text-faint);
}
</style>
