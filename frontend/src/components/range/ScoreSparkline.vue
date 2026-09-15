<template>
  <div class="spark">
    <svg
      v-if="points.length >= 2"
      class="spark__svg"
      :viewBox="`0 0 ${W} ${H}`"
      preserveAspectRatio="none"
    >
      <polyline class="spark__line" :points="polyPoints" />
      <circle class="spark__dot" :cx="lastPoint[0]" :cy="lastPoint[1]" r="3" />
    </svg>
    <span v-else class="spark__empty muted">{{ points.length ? '仅 1 次成绩' : '暂无成绩' }}</span>
    <span
      v-if="trendDir"
      class="spark__trend num"
      :class="trendGood ? 'spark__trend--good' : 'spark__trend--bad'"
      :title="lowerIsBetter ? '该科目越低越好' : '该科目越高越好'"
    >
      {{ trendDir }}
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

// 最近几次成绩的迷你趋势：简单 SVG 折线 + 末点；箭头按科目方向（高优/低优）着色
const props = defineProps({
  points: { type: Array, default: () => [] }, // 按时间正序的 score 数组
  lowerIsBetter: { type: Boolean, default: false },
})

const W = 120
const H = 32
const PAD = 4

const coords = computed(() => {
  const pts = props.points
  if (pts.length < 2) return []
  const min = Math.min(...pts)
  const max = Math.max(...pts)
  const span = max - min || 1
  return pts.map((v, i) => [
    PAD + (i / (pts.length - 1)) * (W - PAD * 2),
    H - PAD - ((v - min) / span) * (H - PAD * 2),
  ])
})

const polyPoints = computed(() => coords.value.map(([x, y]) => `${x},${y}`).join(' '))
const lastPoint = computed(() => coords.value[coords.value.length - 1] || [0, 0])

const trendDir = computed(() => {
  const pts = props.points
  if (pts.length < 2) return ''
  const diff = pts[pts.length - 1] - pts[pts.length - 2]
  if (diff === 0) return ''
  return diff > 0 ? '▲' : '▼'
})

const trendGood = computed(() => {
  const up = trendDir.value === '▲'
  return props.lowerIsBetter ? !up : up
})
</script>

<style scoped>
.spark {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}
.spark__svg {
  width: 100%;
  height: 32px;
  display: block;
}
.spark__line {
  fill: none;
  stroke: var(--c-accent);
  stroke-width: 2;
  vector-effect: non-scaling-stroke;
  stroke-linejoin: round;
  stroke-linecap: round;
}
.spark__dot {
  fill: var(--c-accent);
  stroke: var(--c-bg);
  stroke-width: 1.5;
  vector-effect: non-scaling-stroke;
}
.spark__empty { font-size: var(--fs-micro); letter-spacing: 0.08em; }
.spark__trend { font-size: var(--fs-caption); font-weight: 700; }
.spark__trend--good { color: var(--c-win); }
.spark__trend--bad { color: var(--c-loss); }
</style>
