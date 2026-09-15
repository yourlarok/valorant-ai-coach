<template>
  <canvas
    ref="canvasEl"
    class="tracking"
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
  accent: '#ff4655',
  onAccent: '#ffffff',
  text: '#ece8e1',
  win: '#1ec98e',
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
  startAt: 0,
  lastFrameAt: 0,
  coveredMs: 0,
  elapsedMs: 0,
  coveredNow: false,
  target: { x: 0, y: 0, r: 26 },
  path: null, // 正弦叠加轨迹参数
  trail: [], // 最近目标位置，拖尾
}
const mouse = { x: -1, y: -1, inside: false }

const TRAIL_LEN = 22
const COVER_TOLERANCE = 6 // 准星距目标边缘的容差 px
const HUD_SYNC_MS = 250

function targetRadius() {
  return Math.max(20, Math.min(30, Math.min(W, H) * 0.06))
}

// 两路不同频率/相位的正弦叠加，构成平滑变速的利萨茹式轨迹
function makePath() {
  const r = targetRadius()
  const rand = (lo, hi) => lo + Math.random() * (hi - lo)
  return {
    ax1: (W / 2 - r - 16) * rand(0.55, 0.7),
    ax2: (W / 2 - r - 16) * rand(0.25, 0.35),
    ay1: (H / 2 - r - 16) * rand(0.55, 0.7),
    ay2: (H / 2 - r - 16) * rand(0.25, 0.35),
    wx1: rand(0.7, 1.1),
    wx2: rand(1.9, 2.6),
    wy1: rand(0.9, 1.4),
    wy2: rand(2.1, 2.9),
    px1: rand(0, Math.PI * 2),
    px2: rand(0, Math.PI * 2),
    py1: rand(0, Math.PI * 2),
    py2: rand(0, Math.PI * 2),
  }
}

function targetAt(t) {
  const p = game.path
  return {
    x: W / 2 + p.ax1 * Math.sin(t * p.wx1 + p.px1) + p.ax2 * Math.sin(t * p.wx2 + p.px2),
    y: H / 2 + p.ay1 * Math.sin(t * p.wy1 + p.py1) + p.ay2 * Math.sin(t * p.wy2 + p.py2),
  }
}

function liveScore() {
  if (!game.elapsedMs) return 0
  return Math.round((game.coveredMs / game.elapsedMs) * 1000) / 10
}

function resetGame(now) {
  game.started = true
  game.reported = false
  game.startAt = now
  game.lastFrameAt = now
  game.coveredMs = 0
  game.elapsedMs = 0
  game.coveredNow = false
  game.path = makePath()
  game.target = { ...targetAt(0), r: targetRadius() }
  game.trail = []
  props.hud.score = 0
  props.hud.hits = 0
  props.hud.shots = 0
}

function finalize() {
  if (!game.started || game.reported) return
  game.reported = true
  game.started = false
  props.report({
    score: liveScore(),
    extra: { coverage_s: Math.round(game.coveredMs / 100) / 10 },
  })
}

watch(() => props.active, (on) => {
  if (on) resetGame(performance.now())
  else finalize()
})

function onMove(e) {
  const rect = canvasEl.value.getBoundingClientRect()
  mouse.x = e.clientX - rect.left
  mouse.y = e.clientY - rect.top
  mouse.inside = true
}

/* ---------- 渲染 ---------- */

function drawBackground() {
  ctx.fillStyle = colors.bg
  ctx.fillRect(0, 0, W, H)
  ctx.strokeStyle = colors.grid
  ctx.lineWidth = 1
  const step = 48
  ctx.beginPath()
  for (let x = step; x < W; x += step) { ctx.moveTo(x, 0); ctx.lineTo(x, H) }
  for (let y = step; y < H; y += step) { ctx.moveTo(0, y); ctx.lineTo(W, y) }
  ctx.stroke()
}

function drawTrail() {
  game.trail.forEach((p, i) => {
    const t = (i + 1) / game.trail.length
    ctx.fillStyle = `rgba(255, 70, 85, ${0.06 + t * 0.14})`
    ctx.beginPath()
    ctx.arc(p.x, p.y, game.target.r * (0.4 + t * 0.6), 0, Math.PI * 2)
    ctx.fill()
  })
}

function drawTarget() {
  const t = game.target
  const ring = game.coveredNow ? colors.win : colors.onAccent
  ctx.save()
  ctx.translate(t.x, t.y)
  ctx.fillStyle = colors.accent
  ctx.beginPath()
  ctx.arc(0, 0, t.r, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = colors.bg
  ctx.beginPath()
  ctx.arc(0, 0, t.r * 0.55, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = colors.accent
  ctx.beginPath()
  ctx.arc(0, 0, t.r * 0.22, 0, Math.PI * 2)
  ctx.fill()
  // 覆盖时外圈变绿，给持续反馈
  ctx.strokeStyle = ring
  ctx.lineWidth = 2.5
  ctx.beginPath()
  ctx.arc(0, 0, t.r + 5, 0, Math.PI * 2)
  ctx.stroke()
  ctx.restore()
}

function drawCrosshair() {
  if (!mouse.inside || mouse.x < 0) return
  const { x, y } = mouse
  ctx.strokeStyle = game.coveredNow ? colors.win : colors.text
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

let hudSyncAt = 0

function frame(now) {
  if (game.started) {
    const dt = now - game.lastFrameAt
    game.lastFrameAt = now
    game.elapsedMs += dt
    const t = (now - game.startAt) / 1000
    const pos = targetAt(t)
    game.target.x = pos.x
    game.target.y = pos.y
    game.trail.push({ x: pos.x, y: pos.y })
    if (game.trail.length > TRAIL_LEN) game.trail.shift()
    game.coveredNow =
      mouse.inside &&
      Math.hypot(mouse.x - pos.x, mouse.y - pos.y) <= game.target.r + COVER_TOLERANCE
    if (game.coveredNow) game.coveredMs += dt
    if (now - hudSyncAt > HUD_SYNC_MS) {
      hudSyncAt = now
      props.hud.score = liveScore()
    }
  }
  drawBackground()
  if (game.started) {
    drawTrail()
    drawTarget()
  }
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
  colors.win = pick('--c-win', colors.win)
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
.tracking {
  display: block;
  width: 100%;
  height: 100%;
  cursor: none;
}
</style>
