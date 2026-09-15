<template>
  <div class="shell cut-corner">
    <header class="shell__bar">
      <UiButton variant="ghost" size="sm" :cut="false" @click="onExit">
        ← 退出科目
      </UiButton>
      <div class="shell__title">
        <span class="shell__title-cn">{{ title }}</span>
        <span class="shell__title-en muted">{{ drill.toUpperCase().replace('_', ' ') }}</span>
      </div>
      <div class="shell__hud">
        <div class="shell__hud-item">
          <span class="shell__hud-label muted">剩余时间</span>
          <span class="shell__hud-value num" :class="{ 'shell__hud-value--low': timeLeft <= 10 && playing }">
            {{ timeLeft.toFixed(1) }}s
          </span>
        </div>
        <div class="shell__hud-item">
          <span class="shell__hud-label muted">实时得分</span>
          <span class="shell__hud-value num accent">{{ hud.score.toFixed(1) }}</span>
        </div>
      </div>
    </header>

    <div class="shell__stage">
      <slot
        v-if="state !== 'result'"
        :active="playing"
        :time-left="timeLeft"
        :hud="hud"
        :report="report"
      />

      <!-- 开始前的准备遮罩 -->
      <div v-if="state === 'ready'" class="shell__overlay">
        <div class="shell__ready">
          <p class="shell__ready-kicker num">{{ drill.toUpperCase() }}</p>
          <h2 class="shell__ready-title">{{ title }}</h2>
          <p class="shell__ready-desc muted">
            一局 {{ duration }} 秒。点击「开始」后 3 秒倒计时，结束后成绩自动入库。
          </p>
          <UiButton @click="startCountdown">开始训练</UiButton>
        </div>
      </div>

      <!-- 3-2-1 倒计时 -->
      <div v-else-if="state === 'countdown'" class="shell__overlay">
        <span :key="countdown" class="shell__count num">{{ countdown }}</span>
      </div>

      <!-- 成绩卡 -->
      <div v-else class="shell__result-wrap">
        <div class="shell__result cut-corner" :class="{ 'shell__result--record': isRecord }">
          <div v-if="isRecord" class="shell__record">
            <span class="shell__record-slash" />
            <span class="shell__record-text num">新纪录 NEW RECORD</span>
            <span class="shell__record-slash" />
          </div>
          <p class="shell__result-kicker muted">{{ title }} · 成绩卡</p>
          <div class="shell__result-score">
            <span class="shell__result-num num">{{ lastResult?.score.toFixed(1) }}</span>
            <span class="shell__result-unit muted">本次成绩</span>
          </div>
          <div class="shell__result-best">
            <span class="muted">历史最佳</span>
            <span class="num" :class="{ accent: isRecord }">
              {{ best != null ? best.toFixed(1) : '—' }}
            </span>
          </div>
          <div v-if="extraStats.length" class="shell__result-extra">
            <div v-for="s in extraStats" :key="s.label" class="shell__result-stat">
              <span class="shell__result-stat-value num">{{ s.value }}</span>
              <span class="shell__result-stat-label muted">{{ s.label }}</span>
            </div>
          </div>
          <p v-if="postError" class="shell__result-error">成绩上报失败：{{ postError }}</p>
          <div class="shell__result-actions">
            <UiButton @click="restart">再来一局</UiButton>
            <UiButton variant="ghost" @click="onExit">退出返回</UiButton>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onUnmounted, reactive, ref } from 'vue'
import { postTrainingScore } from '../../api'
import { playerName } from '../../player'
import { UiButton } from '../ui'

const props = defineProps({
  drill: { type: String, required: true },
  title: { type: String, required: true },
  duration: { type: Number, default: 60 },
})
const emit = defineEmits(['finish', 'exit'])

const EXTRA_LABELS = {
  hits: '命中数',
  shots: '开枪数',
  avg_reaction_ms: '平均反应',
}

const state = ref('ready') // ready | countdown | playing | result
const countdown = ref(3)
const timeLeft = ref(props.duration)
const hud = reactive({ score: 0, hits: 0, shots: 0 })

const lastResult = ref(null)
const best = ref(null)
const isRecord = ref(false)
const postError = ref('')

const playing = computed(() => state.value === 'playing' && timeLeft.value > 0)

const extraStats = computed(() => {
  const extra = lastResult.value?.extra || {}
  return Object.entries(EXTRA_LABELS)
    .filter(([key]) => typeof extra[key] === 'number')
    .map(([key, label]) => ({
      label,
      value: key === 'avg_reaction_ms' ? `${extra[key]}ms` : `${extra[key]}`,
    }))
})

let countdownTimer = null
let clockRaf = null
let clockStart = 0

function clearTimers() {
  if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null }
  if (clockRaf) { cancelAnimationFrame(clockRaf); clockRaf = null }
}

function startCountdown() {
  clearTimers()
  hud.score = 0
  hud.hits = 0
  hud.shots = 0
  postError.value = ''
  timeLeft.value = props.duration
  countdown.value = 3
  state.value = 'countdown'
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
      startClock()
    }
  }, 900)
}

function startClock() {
  state.value = 'playing'
  clockStart = performance.now()
  const tick = (now) => {
    const left = props.duration - (now - clockStart) / 1000
    timeLeft.value = Math.max(0, left)
    if (left > 0) {
      clockRaf = requestAnimationFrame(tick)
    } else {
      clockRaf = null // 时间到，等待科目组件结算后调用 report
    }
  }
  clockRaf = requestAnimationFrame(tick)
}

async function report(result) {
  if (state.value !== 'playing') return
  clearTimers()
  timeLeft.value = 0
  state.value = 'result'
  lastResult.value = result
  isRecord.value = false
  best.value = null
  try {
    const resp = await postTrainingScore({
      player: playerName.value,
      drill: props.drill,
      score: result.score,
      extra: result.extra || {},
    })
    best.value = resp.best
    isRecord.value = !!resp.is_record
  } catch (e) {
    postError.value = e.message || '网络错误'
  }
  emit('finish', result)
}

function restart() {
  startCountdown()
}

function onExit() {
  clearTimers()
  emit('exit')
}

onUnmounted(clearTimers)
</script>

<style scoped>
.shell {
  background: var(--c-surface-1);
  border: 1px solid var(--c-border);
  box-shadow: var(--shadow-2);
  overflow: hidden;
}

/* ---- 顶栏 + HUD ---- */
.shell__bar {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--c-border);
  background: var(--c-surface-2);
}
.shell__title { display: flex; align-items: baseline; gap: var(--sp-2); }
.shell__title-cn { font-size: var(--fs-h3); font-weight: 700; letter-spacing: 0.06em; }
.shell__title-en { font-size: var(--fs-micro); letter-spacing: 0.18em; }
.shell__hud { margin-left: auto; display: flex; gap: var(--sp-5); }
.shell__hud-item { display: flex; flex-direction: column; align-items: flex-end; line-height: 1.2; }
.shell__hud-label { font-size: var(--fs-micro); letter-spacing: 0.12em; }
.shell__hud-value { font-size: var(--fs-h2); font-weight: 700; }
.shell__hud-value--low { color: var(--c-warn); }

/* ---- 舞台 ---- */
.shell__stage {
  position: relative;
  height: min(62vh, 560px);
  min-height: 360px;
}

.shell__overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 25, 35, 0.82);
  z-index: 5;
}

.shell__ready { text-align: center; max-width: 420px; padding: var(--sp-4); }
.shell__ready-kicker {
  margin: 0 0 var(--sp-1);
  color: var(--c-accent);
  font-size: var(--fs-caption);
  letter-spacing: 0.3em;
}
.shell__ready-title { margin: 0 0 var(--sp-2); font-size: var(--fs-h1); letter-spacing: 0.04em; }
.shell__ready-desc { margin: 0 0 var(--sp-4); }

.shell__count {
  font-size: 96px;
  font-weight: 800;
  color: var(--c-accent);
  text-shadow: 0 0 32px rgba(255, 70, 85, 0.55);
  animation: count-pop 0.9s var(--ease-out);
}
@keyframes count-pop {
  0% { transform: scale(1.6); opacity: 0; }
  25% { transform: scale(1); opacity: 1; }
  100% { transform: scale(0.92); opacity: 0.85; }
}

/* ---- 成绩卡 ---- */
.shell__result-wrap {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(ellipse at 50% 0%, rgba(255, 70, 85, 0.08), transparent 60%),
    var(--c-surface-1);
}
.shell__result {
  position: relative;
  width: min(460px, calc(100% - var(--sp-6)));
  background: var(--c-surface-2);
  border: 1px solid var(--c-border-strong);
  box-shadow: var(--shadow-3);
  padding: var(--sp-5) var(--sp-5) var(--sp-4);
  text-align: center;
  animation: result-in 0.35s var(--ease-out);
}
@keyframes result-in {
  from { transform: translateY(12px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
.shell__result--record { border-color: var(--c-accent); }

.shell__record {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-3);
  margin: calc(-1 * var(--sp-5)) calc(-1 * var(--sp-5)) var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  background: var(--c-accent);
  color: var(--c-on-accent);
  clip-path: polygon(
    0 0, calc(100% - var(--cut-size)) 0, 100% var(--cut-size),
    100% 100%, var(--cut-size) 100%, 0 calc(100% - var(--cut-size))
  );
  animation: record-glow 1.2s ease-in-out infinite alternate;
}
@keyframes record-glow {
  from { box-shadow: 0 0 8px rgba(255, 70, 85, 0.4); }
  to { box-shadow: 0 0 28px rgba(255, 70, 85, 0.9); }
}
.shell__record-text { font-size: var(--fs-h3); font-weight: 800; letter-spacing: 0.22em; }
.shell__record-slash {
  width: 28px;
  height: 3px;
  background: var(--c-on-accent);
  transform: skewX(-24deg);
}

.shell__result-kicker { margin: 0; font-size: var(--fs-caption); letter-spacing: 0.12em; }
.shell__result-score { display: flex; align-items: baseline; justify-content: center; gap: var(--sp-2); }
.shell__result-num {
  font-size: 64px;
  font-weight: 800;
  line-height: 1.1;
  color: var(--c-text);
}
.shell__result-unit { font-size: var(--fs-caption); }
.shell__result-best {
  display: flex;
  justify-content: center;
  gap: var(--sp-2);
  font-size: var(--fs-body);
  margin-bottom: var(--sp-3);
}
.shell__result-extra {
  display: flex;
  justify-content: center;
  gap: var(--sp-5);
  padding: var(--sp-3) 0;
  border-top: 1px solid var(--c-border);
  border-bottom: 1px solid var(--c-border);
  margin-bottom: var(--sp-3);
}
.shell__result-stat { display: flex; flex-direction: column; line-height: 1.3; }
.shell__result-stat-value { font-size: var(--fs-h2); font-weight: 700; }
.shell__result-stat-label { font-size: var(--fs-micro); letter-spacing: 0.1em; }
.shell__result-error { color: var(--c-loss); font-size: var(--fs-caption); margin: 0 0 var(--sp-2); }
.shell__result-actions { display: flex; justify-content: center; gap: var(--sp-3); }
</style>
