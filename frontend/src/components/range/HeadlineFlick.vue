<template>
  <canvas
    ref="canvasEl"
    class="flick"
    @mousedown="onShoot"
    @mousemove="onMove"
    @mouseleave="mouse.inside = false"
  />
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  active: { type: Boolean, default: false },
  timeLeft: { type: Number, default: 0 },
  hud: { type: Object, required: true },
  report: { type: Function, required: true },
})

const canvasEl = ref(null)

// Canvas 无法直接用 CSS 变量，挂载时从 tokens 读取一次
const colors = {
  bg: '#0f1923',
  grid: '#1a2733',
  band: 'rgba(255, 70, 85, 0.05)',
  bandLine: 'rgba(255, 70, 85, 0.45)',
  accent: '#ff4655',
  onAccent: '#ffffff',
  text: '#ece8e1',
  miss: '#ff9f1c',
}

let ctx = null
let W = 0
let H = 0
let rafId = null
let resizeObserver = null

// 纯逻辑状态，不走响应式以保证 60fps
const game = {
  started: false,
  reported: false,
  target: null, // {x, y, r, spawnAt}
  hits: 0,
  shots: 0,
  reactions: [],
  effects: [], // {type: 'hit'|'miss', x, y, born}
}
const mouse = { x: -1, y: -1, inside: false }

const TARGET_LIFE_POP = 120 // 目标出现弹出动画 ms
const HIT_FX_MS = 320
const MISS_FX_MS = 260

function bandHeight() {
  return Math.max(H * 0.25, 64)
}

function targetRadius() {
  return Math.max(16, Math.min(28, Math.min(W, H) * 0.05, bandHeight() / 2 - 10))
}

function spawnTarget(now) {
  const r = targetRadius()
  const bh = bandHeight()
  game.target = {
    x: r + 12 + Math.random() * (W - 2 * (r + 12)),
    y: r + 10 + Math.random() * (bh - 2 * (r + 10)),
    r,
    spawnAt: now,
  }
}

function resetGame() {
  game.started = true
  game.reported = false
  game.hits = 0
  game.shots = 0
  game.reactions = []
  game.effects = []
  props.hud.score = 0
  props.hud.hits = 0
  props.hud.shots = 0
  spawnTarget(performance.now())
}

function liveScore() {
  if (!game.shots) return 0
  return game.hits * (game.hits / game.shots)
}

function finalize() {
  if (!game.started || game.reported) return
  game.reported = true
  game.started = false
  game.target = null
  const avg = game.reactions.length
    ? Math.round(game.reactions.reduce((a, b) => a + b, 0) / game.reactions.length)
    : 0
  const score = Math.round(liveScore() * 10) / 10
  props.report({
    score,
    extra: { hits: game.hits, shots: game.shots, avg_reaction_ms: avg },
  })
}

watch(() => props.active, (on) => {
  if (on) resetGame()
  else finalize()
})

function canvasPos(e) {
  const rect = canvasEl.value.getBoundingClientRect()
  return { x: e.clientX - rect.left, y: e.clientY - rect.top }
}

function onMove(e) {
  const p = canvasPos(e)
  mouse.x = p.x
  mouse.y = p.y
  mouse.inside = true
}

function onShoot(e) {
  const p = canvasPos(e)
  mouse.x = p.x
  mouse.y = p.y
  mouse.inside = true
  if (!props.active || !game.target) return
  const now = performance.now()
  game.shots += 1
  props.hud.shots = game.shots
  const dx = p.x - game.target.x
  const dy = p.y - game.target.y
  if (Math.hypot(dx, dy) <= game.target.r) {
    game.hits += 1
    props.hud.hits = game.hits
    game.reactions.push(now - game.target.spawnAt)
    game.effects.push({ type: 'hit', x: game.target.x, y: game.target.y, r: game.target.r, born: now })
    spawnTarget(now)
  } else {
    game.effects.push({ type: 'miss', x: p.x, y: p.y, born: now })
  }
  props.hud.score = Math.round(liveScore() * 10) / 10
}

/* ---------- 渲染 ---------- */

function drawBackground() {
  ctx.fillStyle = colors.bg
  ctx.fillRect(0, 0, W, H)
  // 细网格
  ctx.strokeStyle = colors.grid
  ctx.lineWidth = 1
  const step = 48
  ctx.beginPath()
  for (let x = step; x < W; x += step) { ctx.moveTo(x, 0); ctx.lineTo(x, H) }
  for (let y = step; y < H; y += step) { ctx.moveTo(0, y); ctx.lineTo(W, y) }
  ctx.stroke()
}

function drawBand() {
  const bh = bandHeight()
  ctx.fillStyle = colors.band
  ctx.fillRect(0, 0, W, bh)
  // 爆头线：带中虚线
  ctx.strokeStyle = colors.bandLine
  ctx.lineWidth = 1
  ctx.setLineDash([10, 8])
  ctx.beginPath()
  ctx.moveTo(0, bh / 2)
  ctx.lineTo(W, bh / 2)
  ctx.stroke()
  ctx.setLineDash([])
  // 带底边线
  ctx.strokeStyle = colors.grid
  ctx.beginPath()
  ctx.moveTo(0, bh)
  ctx.lineTo(W, bh)
  ctx.stroke()
  // 斜切标签
  ctx.fillStyle = colors.bandLine
  ctx.font = '10px Rajdhani, Bahnschrift, monospace'
  ctx.textBaseline = 'top'
  ctx.fillText('HEADLINE', 10, bh - 16)
}

function drawTarget(now) {
  const t = game.target
  if (!t) return
  const pop = Math.min(1, (now - t.spawnAt) / TARGET_LIFE_POP)
  const scale = 0.6 + 0.4 * (1 - Math.pow(1 - pop, 3))
  const r = t.r * scale
  ctx.save()
  ctx.translate(t.x, t.y)
  // 外圈
  ctx.fillStyle = colors.accent
  ctx.beginPath()
  ctx.arc(0, 0, r, 0, Math.PI * 2)
  ctx.fill()
  // 内圈
  ctx.fillStyle = colors.bg
  ctx.beginPath()
  ctx.arc(0, 0, r * 0.62, 0, Math.PI * 2)
  ctx.fill()
  // 心点
  ctx.fillStyle = colors.accent
  ctx.beginPath()
  ctx.arc(0, 0, r * 0.26, 0, Math.PI * 2)
  ctx.fill()
  // 四向准星刻线
  ctx.strokeStyle = colors.onAccent
  ctx.lineWidth = 2
  ctx.beginPath()
  for (const [sx, sy] of [[0, -1], [0, 1], [-1, 0], [1, 0]]) {
    ctx.moveTo(sx * r * 0.72, sy * r * 0.72)
    ctx.lineTo(sx * r * 1.15, sy * r * 1.15)
  }
  ctx.stroke()
  ctx.restore()
}

function drawEffects(now) {
  game.effects = game.effects.filter((fx) => {
    const life = fx.type === 'hit' ? HIT_FX_MS : MISS_FX_MS
    const t = (now - fx.born) / life
    if (t >= 1) return false
    if (fx.type === 'hit') {
      // 命中：扩散圆环 + 斜切闪光
      const r = fx.r + t * 34
      ctx.strokeStyle = `rgba(255, 70, 85, ${1 - t})`
      ctx.lineWidth = 3 * (1 - t) + 1
      ctx.beginPath()
      ctx.arc(fx.x, fx.y, r, 0, Math.PI * 2)
      ctx.stroke()
      ctx.strokeStyle = `rgba(255, 255, 255, ${0.8 * (1 - t)})`
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.arc(fx.x, fx.y, r * 0.6, 0, Math.PI * 2)
      ctx.stroke()
    } else {
      // 点空：橙色叉号淡出
      const s = 9 + t * 4
      ctx.strokeStyle = `rgba(255, 159, 28, ${1 - t})`
      ctx.lineWidth = 2.5
      ctx.beginPath()
      ctx.moveTo(fx.x - s, fx.y - s)
      ctx.lineTo(fx.x + s, fx.y + s)
      ctx.moveTo(fx.x + s, fx.y - s)
      ctx.lineTo(fx.x - s, fx.y + s)
      ctx.stroke()
    }
    return true
  })
}

function drawCrosshair() {
  if (!mouse.inside || mouse.x < 0) return
  const { x, y } = mouse
  ctx.strokeStyle = colors.text
  ctx.lineWidth = 1.5
  ctx.beginPath()
  const g = 5
  const l = 9
  ctx.moveTo(x, y - g - l); ctx.lineTo(x, y - g)
  ctx.moveTo(x, y + g); ctx.lineTo(x, y + g + l)
  ctx.moveTo(x - g - l, y); ctx.lineTo(x - g, y)
  ctx.moveTo(x + g, y); ctx.lineTo(x + g + l, y)
  ctx.stroke()
  ctx.fillStyle = colors.accent
  ctx.beginPath()
  ctx.arc(x, y, 1.6, 0, Math.PI * 2)
  ctx.fill()
}

function frame(now) {
  drawBackground()
  drawBand()
  drawTarget(now)
  drawEffects(now)
  drawCrosshair()
  rafId = requestAnimationFrame(frame)
}

function resize() {
  const el = canvasEl.value
  if (!el) return
  const dpr = window.devicePixelRatio || 1
  W = el.clientWidth
  H = el.clientHeight
  el.width = Math.round(W * dpr)
  el.height = Math.round(H * dpr)
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
}

onMounted(() => {
  const el = canvasEl.value
  ctx = el.getContext('2d')
  const styles = getComputedStyle(document.documentElement)
  const pick = (key, fallback) => styles.getPropertyValue(key).trim() || fallback
  colors.bg = pick('--c-bg', colors.bg)
  colors.grid = pick('--c-surface-2', colors.grid)
  colors.accent = pick('--c-accent', colors.accent)
  colors.text = pick('--c-text', colors.text)
  colors.miss = pick('--c-warn', colors.miss)
  resize()
  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(el)
  rafId = requestAnimationFrame(frame)
})

onUnmounted(() => {
  if (rafId) cancelAnimationFrame(rafId)
  if (resizeObserver) resizeObserver.disconnect()
})
</script>

<style scoped>
.flick {
  display: block;
  width: 100%;
  height: 100%;
  cursor: none;
}
</style>
