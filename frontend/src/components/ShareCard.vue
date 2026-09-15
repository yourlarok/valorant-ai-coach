<template>
  <div>
    <div ref="cardEl" class="share-card">
      <div class="slash slash-top"></div>
      <div class="card-header">
        <div class="player muted">{{ playerName || '昵称#数字ID' }}</div>
        <div class="title">{{ primary }}</div>
        <div class="pro-line muted">职业哥定位：——</div>
      </div>
      <div class="card-radar">
        <RadarChart :scores="scores" :height="200" />
      </div>
      <div v-if="subs && subs.length" class="subs">
        <span v-for="s in subs" :key="s" class="sub-tag">{{ s }}</span>
      </div>
      <div v-if="roast" class="roast">"{{ roast }}"</div>
      <div class="grade accent">{{ grade }}</div>
      <div class="slash slash-bottom"></div>
    </div>
    <button class="save-btn" @click="saveImage">保存图片</button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import html2canvas from 'html2canvas'
import RadarChart from './RadarChart.vue'

const props = defineProps({
  primary: { type: String, default: '' },
  subs: { type: Array, default: () => [] },
  scores: { type: Object, required: true },
  roast: { type: String, default: '' },
  playerName: { type: String, default: '' },
})

const cardEl = ref(null)

const grade = computed(() => {
  const vals = Object.values(props.scores || {})
  if (!vals.length) return '—'
  const avg = vals.reduce((a, b) => a + b, 0) / vals.length
  return avg >= 70 ? 'S' : 'A'
})

async function saveImage() {
  const canvas = await html2canvas(cardEl.value, { backgroundColor: '#0f1923' })
  const link = document.createElement('a')
  link.download = `valorant-coach-${props.playerName || 'card'}.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
}
</script>

<style scoped>
.share-card {
  position: relative;
  width: 375px;
  height: 550px;
  margin: 0 auto;
  padding: 28px 24px;
  background: var(--panel);
  border: 2px solid var(--accent);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.slash {
  position: absolute;
  width: 140px;
  height: 10px;
  background: var(--accent);
  transform: skewX(-30deg);
  opacity: 0.85;
}
.slash-top { top: 14px; right: -30px; }
.slash-bottom { bottom: 14px; left: -30px; }
.card-header { text-align: center; }
.player { font-size: 13px; }
.title {
  font-size: 30px;
  font-weight: 800;
  color: var(--accent);
  margin: 8px 0 4px;
  letter-spacing: 2px;
}
.pro-line { font-size: 12px; }
.card-radar { flex: 1; min-height: 0; }
.subs { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; }
.sub-tag {
  font-size: 12px;
  padding: 2px 10px;
  border: 1px solid var(--accent);
  border-radius: 999px;
  color: var(--text);
}
.roast {
  margin-top: 12px;
  text-align: center;
  font-size: 13px;
  color: var(--text);
  font-style: italic;
}
.grade {
  position: absolute;
  right: 22px;
  bottom: 22px;
  font-size: 56px;
  font-weight: 900;
  line-height: 1;
  transform: skewX(-8deg);
}
.save-btn { display: block; margin: 12px auto 0; }
</style>
