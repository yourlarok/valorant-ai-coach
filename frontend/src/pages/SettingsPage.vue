<template>
  <div class="settings-page">
    <h1 class="settings-page__title">设置</h1>

    <!-- LLM 配置 -->
    <UiCard title="LLM 配置">
      <template #actions>
        <UiTag v-if="!loading" :tone="configured ? 'win' : 'warn'" dot>
          {{ configured ? 'LLM 已连接' : '未配置 · Mock 演示通道' }}
        </UiTag>
      </template>

      <UiSkeleton v-if="loading" :lines="3" height="20px" />
      <UiEmpty
        v-else-if="loadError"
        title="无法读取当前配置"
        :description="loadError"
      >
        <UiButton variant="ghost" @click="load">重试</UiButton>
      </UiEmpty>

      <form v-else class="form" @submit.prevent="save">
        <label class="field">
          <span class="field__label">Base URL</span>
          <input
            v-model.trim="form.base_url"
            placeholder="https://api.openai.com/v1"
            spellcheck="false"
          />
          <span class="field__hint muted">兼容 OpenAI 协议的任意服务端点</span>
        </label>
        <label class="field">
          <span class="field__label">API Key</span>
          <input
            v-model="form.api_key"
            type="password"
            placeholder="留空保持不变"
            autocomplete="off"
          />
          <span class="field__hint muted">出于安全考虑，已保存的 key 不会回显</span>
        </label>
        <label class="field">
          <span class="field__label">模型</span>
          <input v-model.trim="form.model" placeholder="gpt-4o-mini" spellcheck="false" />
        </label>
        <div class="form__actions">
          <UiButton type="submit" :disabled="saving">
            {{ saving ? '保存中…' : '保存并生效' }}
          </UiButton>
          <span class="muted">保存后写入本地 config.json，后端即时生效，无需重启。</span>
        </div>
      </form>
    </UiCard>

    <!-- 数据源状态 -->
    <UiCard title="数据源状态">
      <div class="source">
        <div class="source__row">
          <UiTag tone="info" dot>COLLECTOR 环境变量控制</UiTag>
        </div>
        <p class="muted source__text">
          当前数据源由后端启动时的 COLLECTOR 环境变量决定：默认为
          <span class="num">fixture</span>，使用内置演示对局数据；设为
          <span class="num">wegame</span> 时切换为 WeGame 真机采集。切换数据源需重启后端生效。
        </p>
      </div>
    </UiCard>

    <!-- 红线声明 -->
    <UiCard title="红线声明">
      <ul class="redline">
        <li>只分析本人账号及公开对局数据，不获取他人隐私信息。</li>
        <li>API Key 等凭证仅保存在本地 config.json，不上传任何服务器。</li>
        <li>不提供任何绕过反作弊系统的能力。</li>
      </ul>
    </UiCard>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getSettings, saveSettings } from '../api'
import { UiButton, UiCard, UiEmpty, UiSkeleton, UiTag, useToast } from '../components/ui'

const toast = useToast()

const loading = ref(false)
const loadError = ref('')
const saving = ref(false)
const configured = ref(false)
const form = ref({ base_url: '', api_key: '', model: '' })

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const data = await getSettings()
    configured.value = !!data?.configured
    form.value = {
      base_url: data?.base_url || '',
      api_key: '',
      model: data?.model || '',
    }
  } catch (e) {
    loadError.value = e.message || '获取 LLM 配置失败'
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const body = {
      base_url: form.value.base_url || null,
      model: form.value.model || null,
    }
    // api_key 留空 = 保持不变（后端语义：不传字段则不覆盖）
    if (form.value.api_key) body.api_key = form.value.api_key
    const data = await saveSettings(body)
    configured.value = !!data?.configured
    form.value.api_key = ''
    toast.success('LLM 配置已保存，即时生效')
  } catch (e) {
    toast.error(e.message || '保存失败，请重试')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  max-width: 720px;
}
.settings-page__title {
  margin: 0;
  font-size: var(--fs-h1);
  font-weight: 700;
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}
.field {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}
.field__label {
  font-size: var(--fs-caption);
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--c-text-muted);
  text-transform: uppercase;
}
.field__hint { font-size: var(--fs-caption); }
.form__actions {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
  margin-top: var(--sp-2);
}

.source__row { margin-bottom: var(--sp-2); }
.source__text { margin: 0; }

.redline {
  margin: 0;
  padding-left: var(--sp-4);
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  color: var(--c-text-muted);
}
</style>
