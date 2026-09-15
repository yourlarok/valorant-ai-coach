<template>
  <div class="settings-page">
    <h1 class="settings-page__title">设置</h1>

    <!-- LLM 配置 -->
    <UiCard title="LLM 配置">
      <template #actions>
        <UiTag v-if="!loading && !loadError" :tone="configured ? 'win' : 'warn'" dot>
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
            placeholder="https://api.deepseek.com/v1"
            spellcheck="false"
          />
          <span class="field__hint muted">默认内置 DeepSeek，兼容 OpenAI 协议的端点均可替换</span>
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
          <input v-model.trim="form.model" placeholder="deepseek-chat" spellcheck="false" />
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

    <!-- 自动化 -->
    <UiCard title="自动化">
      <UiSkeleton v-if="autoLoading" :lines="2" height="20px" />
      <template v-else>
        <div class="form">
          <label class="switch">
            <input v-model="autoForm.enabled" type="checkbox" />
            <span class="switch__track" aria-hidden="true" />
            <span class="switch__text">
              <span class="field__label">自动分析新对局</span>
              <span class="field__hint muted">
                开启后后台定时检查新对局，自动完成深度分析并推送通知
              </span>
            </span>
          </label>
          <label class="field">
            <span class="field__label">轮询间隔（分钟）</span>
            <input
              v-model.number="autoForm.poll_interval_min"
              type="number"
              min="1"
              max="1440"
              class="auto-interval"
            />
          </label>
          <div class="form__actions">
            <UiButton :disabled="autoSaving" @click="saveAutomation">
              {{ autoSaving ? '保存中…' : '保存自动化设置' }}
            </UiButton>
            <UiButton variant="ghost" :disabled="simulating" @click="simulate">
              {{ simulating ? '模拟中…' : '模拟新对局' }}
            </UiButton>
            <span class="muted">“模拟新对局”仅 fixture 演示数据源可用。</span>
          </div>
        </div>
      </template>
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
import { getAutomation, putAutomation, saveSettings, simulateNewMatch } from '../api'
import { configured, loadSettings, updateConfigured } from '../settings'
import { playerName } from '../player'
import { UiButton, UiCard, UiEmpty, UiSkeleton, UiTag, useToast } from '../components/ui'

const toast = useToast()

const loading = ref(false)
const loadError = ref('')
const saving = ref(false)
const form = ref({ base_url: '', api_key: '', model: '' })

const autoLoading = ref(false)
const autoSaving = ref(false)
const simulating = ref(false)
// 后端 PUT /settings/automation 要求全量字段，缺省字段会被默认值重置
const autoForm = ref({ enabled: true, poll_interval_min: 5 })

async function loadAutomation() {
  autoLoading.value = true
  try {
    const data = await getAutomation()
    autoForm.value = {
      enabled: !!data?.enabled,
      poll_interval_min: data?.poll_interval_min || 5,
    }
  } catch (e) {
    toast.error(e.message || '获取自动化设置失败')
  } finally {
    autoLoading.value = false
  }
}

async function saveAutomation() {
  autoSaving.value = true
  try {
    const body = {
      enabled: !!autoForm.value.enabled,
      poll_interval_min: Math.max(1, Number(autoForm.value.poll_interval_min) || 5),
    }
    const data = await putAutomation(body)
    autoForm.value = {
      enabled: !!data?.enabled,
      poll_interval_min: data?.poll_interval_min || body.poll_interval_min,
    }
    toast.success('自动化设置已保存')
  } catch (e) {
    toast.error(e.message || '保存失败，请重试')
  } finally {
    autoSaving.value = false
  }
}

async function simulate() {
  simulating.value = true
  try {
    await simulateNewMatch(playerName.value || '测试玩家#1234')
    toast.success('已模拟，稍后在通知中心查看')
  } catch (e) {
    toast.error(e.message || '模拟失败，请重试')
  } finally {
    simulating.value = false
  }
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const data = await loadSettings()
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
    updateConfigured(data?.configured)
    form.value.api_key = ''
    toast.success('LLM 配置已保存，即时生效')
  } catch (e) {
    toast.error(e.message || '保存失败，请重试')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  load()
  loadAutomation()
})
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

.switch {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  cursor: pointer;
}
.switch input { position: absolute; opacity: 0; width: 0; height: 0; }
.switch__track {
  position: relative;
  flex: 0 0 40px;
  width: 40px;
  height: 22px;
  background: var(--c-surface-3);
  border: 1px solid var(--c-border-strong);
  border-radius: var(--r-lg);
  transition: background var(--dur-base) var(--ease-out),
    border-color var(--dur-base) var(--ease-out);
}
.switch__track::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--c-text-muted);
  transition: transform var(--dur-base) var(--ease-out),
    background var(--dur-base) var(--ease-out);
}
.switch input:checked + .switch__track {
  background: var(--c-accent-dim);
  border-color: var(--c-accent);
}
.switch input:checked + .switch__track::after {
  transform: translateX(18px);
  background: var(--c-accent);
}
.switch input:focus-visible + .switch__track { border-color: var(--c-accent); }
.switch__text { display: flex; flex-direction: column; gap: var(--sp-1); }

.auto-interval { max-width: 160px; }

.redline {
  margin: 0;
  padding-left: var(--sp-4);
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  color: var(--c-text-muted);
}
</style>
