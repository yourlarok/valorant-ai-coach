<template>
  <div v-if="points.length < 2" class="trend-mini__empty muted">
    至少 2 场评分后生成趋势
  </div>
  <div v-else ref="chartEl" class="trend-mini"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

// 近 5 场综合评分迷你折线：无坐标轴噪声，只留走势与端点
const props = defineProps({
  points: { type: Array, default: () => [] }, // [{ label, score }]
  height: { type: Number, default: 120 },
})

const chartEl = ref(null)
let chart = null

function render() {
  if (!chart) return
  const scores = props.points.map((p) => p.score)
  chart.setOption({
    backgroundColor: 'transparent',
    grid: { left: 8, right: 8, top: 12, bottom: 8 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1a2733',
      borderColor: '#2b3a47',
      textStyle: { color: '#ece8e1', fontSize: 12 },
      formatter: (params) => {
        const p = params[0]
        const item = props.points[p.dataIndex]
        return `${item?.label || ''}<br/>综合评分 ${p.value}`
      },
    },
    xAxis: {
      type: 'category',
      data: props.points.map((p) => p.label),
      show: false,
      boundaryGap: false,
    },
    yAxis: { type: 'value', min: 0, max: 100, show: false },
    series: [
      {
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2, color: '#ff4655' },
        itemStyle: { color: '#ff4655', borderColor: '#0f1923', borderWidth: 2 },
        areaStyle: { color: 'rgba(255, 70, 85, 0.12)' },
        data: scores,
      },
    ],
  })
}

async function syncChart() {
  if (props.points.length < 2) {
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

watch(() => props.points, syncChart, { deep: true })
</script>

<style scoped>
.trend-mini { width: 100%; height: 120px; }
.trend-mini__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 120px;
  font-size: var(--fs-caption);
}
</style>
