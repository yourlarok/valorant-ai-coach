<template>
  <div ref="chartEl" class="radar" :style="{ height: height + 'px' }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  scores: { type: Object, required: true },
  height: { type: Number, default: 320 },
})

const chartEl = ref(null)
let chart = null

const AXES = [
  ['aim', '瞄准'],
  ['duel', '对枪'],
  ['awareness', '意识'],
  ['economy', '经济'],
  ['ability', '技能'],
  ['consistency', '稳定'],
]

function render() {
  if (!chart) return
  const values = AXES.map(([key]) => props.scores?.[key] ?? 0)
  chart.setOption({
    backgroundColor: 'transparent',
    radar: {
      indicator: AXES.map(([, label]) => ({ name: label, max: 100 })),
      radius: '65%',
      axisName: { color: '#ece8e1', fontSize: 12 },
      splitLine: { lineStyle: { color: '#2b3a47' } },
      splitArea: { areaStyle: { color: ['#111c26', '#1a2733'] } },
      axisLine: { lineStyle: { color: '#2b3a47' } },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: values,
            name: '六维评分',
            lineStyle: { color: '#ff4655', width: 2 },
            itemStyle: { color: '#ff4655' },
            areaStyle: { color: 'rgba(255, 70, 85, 0.35)' },
          },
        ],
      },
    ],
  })
}

function onResize() {
  chart && chart.resize()
}

onMounted(() => {
  chart = echarts.init(chartEl.value)
  render()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart && chart.dispose()
  chart = null
})

watch(() => props.scores, render, { deep: true })
</script>

<style scoped>
.radar { width: 100%; }
</style>
