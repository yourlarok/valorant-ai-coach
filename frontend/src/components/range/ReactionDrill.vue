<template>
  <div class="reaction" :class="`reaction--${phase}`" @mousedown="onClick">
    <div
      v-if="phase === 'go'"
      class="reaction__target"
      :style="{ left: `${target.x}%`, top: `${target.y}%` }"
    />
    <div class="reaction__center">
      <template v-if="phase === 'wait'">
        <p class="reaction__big">等待变绿…</p>
        <p class="reaction__sub">变绿并出靶的瞬间点击 · 提前点击判抢跑</p>
      </template>
      <template v-else-if="phase === 'go'">
        <p class="reaction__big reaction__big--go">点！</p>
      </template>
      <template v-else-if="phase === 'feedback'">
        <p class="reaction__big num" :class="{ 'reaction__big--foul': lastFoul }">
          {{ lastFoul ? `抢跑 +${PENALTY_MS}ms` : `${lastMs}ms` }}
        </p>
        <p class="reaction__sub">{{ lastFoul ? '该轮按罚时计入平均' : '本轮反应时间' }}</p>
      </template>
      <template v-else>
        <p class="reaction__big">反应速度</p>
        <p class="reaction__sub">共 {{ TOTAL_ROUNDS }} 轮，取平均毫秒数，越低越好</p>
      </template>
      <div class="reaction__dots">
        <span
          v-for="i in TOTAL_ROUNDS"
          :key="i"
          class="reaction__dot"
          :class="{
            'reaction__dot--done': i <= results.length && !results[i - 1]?.foul,
            'reaction__dot--foul': results[i - 1]?.foul,
          }"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  active: { type: Boolean, default: false },
  timeLeft: { type: Number, default: 0 },
  hud: { type: Object, required: true },
  report: { type: Function, required: true },
})

const TOTAL_ROUNDS = 5
const PENALTY_MS = 999 // 抢跑罚时，计入平均
const FEEDBACK_MS = 750

const phase = ref('idle') // idle | wait | go | feedback
const results = ref([]) // [{ ms, foul }]
const lastMs = ref(0)
const lastFoul = ref(false)
const target = ref({ x: 50, y: 50 })

let goAt = 0
let waitTimer = null
let feedbackTimer = null
let reported = false

function clearTimers() {
  if (waitTimer) { clearTimeout(waitTimer); waitTimer = null }
  if (feedbackTimer) { clearTimeout(feedbackTimer); feedbackTimer = null }
}

function liveAvg() {
  if (!results.value.length) return 0
  return Math.round(results.value.reduce((a, r) => a + r.ms, 0) / results.value.length)
}

function nextRound() {
  if (results.value.length >= TOTAL_ROUNDS) {
    finish()
    return
  }
  phase.value = 'wait'
  waitTimer = setTimeout(go, 1000 + Math.random() * 2000)
}

function go() {
  waitTimer = null
  target.value = { x: 20 + Math.random() * 60, y: 25 + Math.random() * 50 }
  goAt = performance.now()
  phase.value = 'go'
}

function recordRound(ms, foul) {
  results.value.push({ ms, foul })
  lastMs.value = Math.round(ms)
  lastFoul.value = foul
  props.hud.score = liveAvg()
  props.hud.shots = results.value.length
  phase.value = 'feedback'
  feedbackTimer = setTimeout(() => {
    feedbackTimer = null
    nextRound()
  }, FEEDBACK_MS)
}

function onClick() {
  if (!props.active) return
  if (phase.value === 'wait') {
    clearTimeout(waitTimer)
    waitTimer = null
    recordRound(PENALTY_MS, true)
  } else if (phase.value === 'go') {
    recordRound(performance.now() - goAt, false)
  }
}

function finish() {
  if (reported) return
  reported = true
  clearTimers()
  // 时间到等中断场景：未完成的轮次按罚时补齐，保证 5 轮口径且无法刷 0ms
  while (results.value.length < TOTAL_ROUNDS) {
    results.value.push({ ms: PENALTY_MS, foul: true })
  }
  const avg = liveAvg()
  const fouls = results.value.filter((r) => r.foul).length
  props.report({
    score: avg,
    extra: {
      rounds: results.value.map((r) => ({ ms: Math.round(r.ms), foul: r.foul })),
      fouls,
      avg_reaction_ms: avg,
    },
  })
}

watch(() => props.active, (on) => {
  if (on) {
    reported = false
    results.value = []
    props.hud.score = 0
    props.hud.hits = 0
    props.hud.shots = 0
    nextRound()
  } else {
    finish()
  }
})

onUnmounted(clearTimers)
</script>

<style scoped>
.reaction {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-surface-1);
  cursor: pointer;
  user-select: none;
  transition: background var(--dur-fast) var(--ease-out);
}
.reaction--go { background: var(--c-win); }
.reaction--feedback.reaction { background: var(--c-surface-2); }

.reaction__center { position: relative; text-align: center; padding: var(--sp-4); }
.reaction__big {
  margin: 0;
  font-size: var(--fs-h1);
  font-weight: 800;
  letter-spacing: 0.08em;
  color: var(--c-text);
}
.reaction--go .reaction__big { color: var(--c-on-accent); }
.reaction__big--go { text-shadow: 0 2px 16px rgba(0, 0, 0, 0.35); }
.reaction__big--foul { color: var(--c-warn); }
.reaction__sub {
  margin: var(--sp-2) 0 0;
  font-size: var(--fs-caption);
  letter-spacing: 0.1em;
  color: var(--c-text-muted);
}
.reaction--go .reaction__sub { color: rgba(255, 255, 255, 0.85); }

.reaction__target {
  position: absolute;
  width: 56px;
  height: 56px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: var(--c-accent);
  border: 4px solid var(--c-on-accent);
  box-shadow: 0 0 0 6px rgba(255, 70, 85, 0.35), 0 4px 18px rgba(0, 0, 0, 0.4);
  animation: target-pop 0.16s var(--ease-out);
}
@keyframes target-pop {
  from { transform: translate(-50%, -50%) scale(0.5); }
  to { transform: translate(-50%, -50%) scale(1); }
}

.reaction__dots {
  display: flex;
  justify-content: center;
  gap: var(--sp-2);
  margin-top: var(--sp-4);
}
.reaction__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--c-border-strong);
  opacity: 0.5;
}
.reaction--go .reaction__dot { background: rgba(255, 255, 255, 0.55); }
.reaction__dot--done { background: var(--c-win); opacity: 1; }
.reaction__dot--foul { background: var(--c-warn); opacity: 1; }
</style>
