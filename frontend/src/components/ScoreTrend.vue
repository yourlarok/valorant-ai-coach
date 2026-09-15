<template>
  <p v-if="history.length < 2" class="muted">至少复测一次后生成趋势</p>
  <div v-else ref="chartEl" class="trend" :style="{ height: height + 'px' }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  history: { type: Array, required: true },
  height: { type: Number, default: 340 },
})

const chartEl = ref(null)
let chart = null

const DIMS = [
  ['aim', '瞄准', '#38bdf8'],
  ['duel', '对枪', '#fbbf24'],
  ['awareness', '意识', '#4ade80'],
  ['economy', '经济', '#c084fc'],
  ['utility', '技能', '#f472b6'],
  ['consistency', '稳定', '#94a3b8'],
]

function render() {
  if (!chart) return
  const dates = props.history.map((h) => h.date)
  const dimSeries = DIMS.map(([key, label, color]) => ({
    name: label,
    type: 'line',
    smooth: true,
    symbolSize: 5,
    lineStyle: { width: 1.5, color },
    itemStyle: { color },
    data: props.history.map((h) => h.scores?.[key] ?? null),
  }))
  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    legend: {
      data: [...DIMS.map(([, label]) => label), '综合'],
      textStyle: { color: '#ece8e1', fontSize: 12 },
      bottom: 0,
    },
    grid: { left: 40, right: 20, top: 20, bottom: 56 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#2b3a47' } },
      axisLabel: { color: '#768079' },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      splitLine: { lineStyle: { color: '#2b3a47' } },
      axisLabel: { color: '#768079' },
    },
    series: [
      ...dimSeries,
      {
        name: '综合',
        type: 'line',
        smooth: true,
        symbolSize: 8,
        lineStyle: { width: 4, color: '#ff4655' },
        itemStyle: { color: '#ff4655' },
        data: props.history.map((h) => h.scores?.overall ?? null),
      },
    ],
  })
}

async function syncChart() {
  if (props.history.length < 2) {
    if (chart) {
      chart.dispose()
      chart = null
    }
    return
  }
  await nextTick()
  if (!chart && chartEl.value) chart = echarts.init(chartEl.value)
  render()
}

function onResize() {
  chart && chart.resize()
}

onMounted(() => {
  syncChart()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart && chart.dispose()
  chart = null
})

watch(() => props.history, syncChart, { deep: true })
</script>

<style scoped>
.trend { width: 100%; }
</style>
