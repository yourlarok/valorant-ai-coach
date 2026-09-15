<template>
  <div class="onboarding">
    <div class="onboarding__panel">
      <!-- 步骤指示 -->
      <div class="steps">
        <span
          v-for="(label, i) in ['产品介绍', '绑定身份', '自动化授权']"
          :key="label"
          class="steps__item"
          :class="{ 'steps__item--active': step === i, 'steps__item--done': step > i }"
        >
          <span class="steps__num num">{{ i + 1 }}</span>
          <span class="steps__label">{{ label }}</span>
        </span>
      </div>

      <!-- 第 1 步：产品介绍 -->
      <section v-if="step === 0" class="step">
        <div class="step__brand">
          <span class="step__logo cut-corner">VAL</span>
        </div>
        <h1 class="step__title">无畏契约 AI 对局教练</h1>
        <p class="step__desc">
          自动分析你的每一局对局，找出问题所在，并开出针对性的训练处方。
        </p>
        <div class="caps">
          <div v-for="cap in capabilities" :key="cap.title" class="caps__item">
            <span class="caps__icon cut-corner" aria-hidden="true">{{ cap.icon }}</span>
            <span class="caps__title">{{ cap.title }}</span>
            <span class="caps__desc muted">{{ cap.desc }}</span>
          </div>
        </div>
        <UiButton @click="step = 1">开始使用</UiButton>
      </section>

      <!-- 第 2 步：绑定身份 -->
      <section v-else-if="step === 1" class="step">
        <h1 class="step__title">绑定你的游戏身份</h1>
        <p class="step__desc">输入你的玩家名（格式：昵称#数字ID），我们会验证并对齐你的对局数据。</p>
        <form class="bind" @submit.prevent="bind">
          <input
            v-model="nameInput"
            class="bind__input"
            placeholder="昵称#数字ID"
            :disabled="binding"
            @input="bindError = ''"
          />
          <UiButton type="submit" :disabled="binding || !nameInput.trim()">
            {{ binding ? '验证中…' : '验证并绑定' }}
          </UiButton>
        </form>
        <p v-if="bindError" class="bind__error">{{ bindError }}</p>
        <p class="muted bind__hint">演示通道可试：测试玩家#1234</p>
        <UiButton variant="ghost" size="sm" @click="step = 0">上一步</UiButton>
      </section>

      <!-- 第 3 步：自动化授权 -->
      <section v-else class="step">
        <h1 class="step__title">开启自动化</h1>
        <p class="step__desc">之后新对局会自动完成深度分析并通知你，可随时在设置中关闭。</p>
        <label class="automation">
          <span class="automation__text">
            <span class="automation__name">自动分析新对局</span>
            <span class="automation__hint muted">绑定身份后的历史对局不会重复分析</span>
          </span>
          <button
            type="button"
            class="switch"
            :class="{ 'switch--on': automationOn }"
            role="switch"
            :aria-checked="automationOn"
            @click="automationOn = !automationOn"
          >
            <span class="switch__thumb" />
          </button>
        </label>
        <UiButton :disabled="finishing" @click="finish">
          {{ finishing ? '保存中…' : '完成，进入总览' }}
        </UiButton>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { bindIdentity, putAutomation } from '../api'
import { setIdentity } from '../player'
import { UiButton, useToast } from '../components/ui'

const router = useRouter()
const toast = useToast()

const step = ref(0)
const nameInput = ref('')
const binding = ref(false)
const bindError = ref('')
const automationOn = ref(true)
const finishing = ref(false)

const capabilities = [
  { icon: '析', title: '对局分析', desc: '每场对局自动产出六维评分与深度复盘' },
  { icon: '格', title: '风格定位', desc: '识别你的打法风格，对标同段位基准' },
  { icon: '练', title: '训练闭环', desc: '按问题开出训练处方，复测验证进步' },
]

async function bind() {
  const name = nameInput.value.trim()
  if (!name || binding.value) return
  binding.value = true
  bindError.value = ''
  try {
    const data = await bindIdentity(name)
    setIdentity(data.name)
    step.value = 2
  } catch (e) {
    bindError.value = e.message || '找不到该玩家，请检查昵称#ID 是否输入正确'
  } finally {
    binding.value = false
  }
}

async function finish() {
  if (finishing.value) return
  finishing.value = true
  try {
    await putAutomation({ enabled: automationOn.value, poll_interval_min: 5 })
  } catch (e) {
    // 自动化设置保存失败不阻塞进入，后端默认即为开启
    toast.error(e.message || '自动化设置保存失败，可在设置页重试')
  } finally {
    finishing.value = false
  }
  router.push('/')
}
</script>

<style scoped>
.onboarding {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--sp-4);
  background:
    radial-gradient(60% 50% at 50% 0%, var(--c-accent-dim), transparent),
    var(--c-bg);
}
.onboarding__panel {
  width: 100%;
  max-width: 640px;
  background: var(--c-surface-1);
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  padding: var(--sp-6) var(--sp-6) var(--sp-5);
  box-shadow: var(--shadow-3);
}

/* ---- 步骤指示 ---- */
.steps {
  display: flex;
  gap: var(--sp-4);
  margin-bottom: var(--sp-6);
}
.steps__item {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  color: var(--c-text-faint);
  font-size: var(--fs-caption);
  letter-spacing: 0.06em;
}
.steps__num {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: 1px solid var(--c-border-strong);
  border-radius: var(--r-sm);
  font-weight: 700;
}
.steps__item--active { color: var(--c-text); }
.steps__item--active .steps__num {
  background: var(--c-accent);
  border-color: var(--c-accent);
  color: var(--c-on-accent);
}
.steps__item--done { color: var(--c-text-muted); }
.steps__item--done .steps__num {
  border-color: var(--c-win);
  color: var(--c-win);
}

/* ---- 各步骤通用 ---- */
.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-3);
  text-align: center;
}
.step__brand { margin-bottom: var(--sp-2); }
.step__logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: var(--c-accent);
  color: var(--c-on-accent);
  font-family: var(--font-num);
  font-weight: 800;
  font-size: var(--fs-h1);
}
.step__title { margin: 0; font-size: var(--fs-h1); font-weight: 800; }
.step__desc { margin: 0; color: var(--c-text-muted); max-width: 420px; }

/* ---- 第 1 步：三能力区 ---- */
.caps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--sp-3);
  width: 100%;
  margin: var(--sp-3) 0;
}
.caps__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-1);
  background: var(--c-surface-2);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  padding: var(--sp-3) var(--sp-2);
}
.caps__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--c-accent-dim);
  color: var(--c-accent);
  font-weight: 800;
  font-size: var(--fs-h3);
  margin-bottom: var(--sp-1);
}
.caps__title { font-weight: 700; font-size: var(--fs-body); }
.caps__desc { font-size: var(--fs-caption); line-height: 1.5; }

/* ---- 第 2 步：绑定表单 ---- */
.bind { display: flex; gap: var(--sp-2); margin-top: var(--sp-2); }
.bind__input { width: 260px; }
.bind__error {
  margin: 0;
  color: var(--c-loss);
  font-size: var(--fs-body);
}
.bind__hint { margin: 0; font-size: var(--fs-caption); }

/* ---- 第 3 步：自动化开关 ---- */
.automation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  width: 100%;
  max-width: 420px;
  background: var(--c-surface-2);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  padding: var(--sp-3) var(--sp-4);
  margin: var(--sp-3) 0;
  cursor: pointer;
}
.automation__text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--sp-1);
  text-align: left;
}
.automation__name { font-weight: 700; }
.automation__hint { font-size: var(--fs-caption); }
.switch {
  position: relative;
  flex-shrink: 0;
  width: 44px;
  height: 24px;
  border: 1px solid var(--c-border-strong);
  border-radius: 12px;
  background: var(--c-surface-3);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out),
    border-color var(--dur-fast) var(--ease-out);
}
.switch__thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--c-text-muted);
  transition: transform var(--dur-base) var(--ease-out),
    background var(--dur-fast) var(--ease-out);
}
.switch--on { background: var(--c-accent-dim); border-color: var(--c-accent); }
.switch--on .switch__thumb {
  transform: translateX(20px);
  background: var(--c-accent);
}

@media (max-width: 560px) {
  .onboarding__panel { padding: var(--sp-4); }
  .caps { grid-template-columns: 1fr; }
  .steps { gap: var(--sp-3); }
}
</style>
