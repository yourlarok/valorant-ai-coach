<template>
  <div class="settings-page">
    <h1 class="settings-page__title">设置</h1>
    <UiCard title="LLM 配置">
      <UiEmpty
        title="功能建设中"
        description="LLM 配置（base_url / key / model，运行时生效）与数据源状态（fixture / wegame）将在后续任务中上线。"
      />
    </UiCard>
  </div>
</template>

<script setup>
import { UiCard, UiEmpty } from '../components/ui'
</script>

<style scoped>
.settings-page__title {
  margin: 0 0 var(--sp-4);
  font-size: var(--fs-h1);
  font-weight: 700;
}
</style>
