<template>
  <div>
    <div ref="cardEl" class="share-card">
      <div class="share-card__slash share-card__slash--tr" aria-hidden="true"></div>
      <div class="share-card__slash share-card__slash--bl" aria-hidden="true"></div>
      <div class="share-card__grade cut-corner num">{{ grade }}</div>

      <header class="share-card__head">
        <div class="share-card__brand muted">VALORANT · AI 教练</div>
        <div class="share-card__player num">{{ playerName || '昵称#数字ID' }}</div>
        <h2 class="share-card__title">{{ primary }}</h2>
        <div class="share-card__pro muted">职业哥定位：{{ proStyle }}</div>
      </header>

      <div class="share-card__radar">
        <RadarChart :scores="scores" :height="200" />
      </div>

      <div v-if="subs && subs.length" class="share-card__subs">
        <UiTag v-for="s in subs" :key="s" tone="accent">{{ s }}</UiTag>
      </div>

      <div v-if="roast" class="share-card__roast">“{{ roast }}”</div>

      <footer class="share-card__foot muted">
        <span class="num">{{ today }}</span>
        <span>本地数据 · 仅供本人复盘</span>
      </footer>
    </div>
    <UiButton class="share-card__save" @click="saveImage">保存分享图</UiButton>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import html2canvas from 'html2canvas'
import RadarChart from './RadarChart.vue'
import { UiButton, UiTag, useToast } from './ui'
import { proStyleFor } from '../pros'

const props = defineProps({
  primary: { type: String, default: '' },
  subs: { type: Array, default: () => [] },
  scores: { type: Object, required: true },
  roast: { type: String, default: '' },
  playerName: { type: String, default: '' },
})

const toast = useToast()
const cardEl = ref(null)
const saving = ref(false)

const grade = computed(() => props.scores?.grade || '—')
const proStyle = computed(() => proStyleFor(props.primary))
const today = new Date().toISOString().slice(0, 10)

async function saveImage() {
  if (saving.value) return
  saving.value = true
  try {
    const canvas = await html2canvas(cardEl.value, { backgroundColor: '#0f1923' })
    const link = document.createElement('a')
    link.download = `valorant-coach-${props.playerName || 'card'}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    toast.success('分享图已保存')
  } catch (err) {
    console.error('保存分享图失败:', err)
    toast.error('保存图片失败，请稍后重试')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.share-card {
  position: relative;
  width: 375px;
  height: 550px;
  margin: 0 auto;
  padding: var(--sp-4);
  background: var(--c-surface-2);
  border: 1px solid var(--c-border-strong);
  border-radius: var(--r-md);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-2);
}
.share-card__slash {
  position: absolute;
  width: 150px;
  height: 10px;
  background: var(--c-accent);
  transform: skewX(-30deg);
  opacity: 0.85;
}
.share-card__slash--tr { top: var(--sp-3); right: calc(-1 * var(--sp-5)); }
.share-card__slash--bl { bottom: var(--sp-3); left: calc(-1 * var(--sp-5)); }

.share-card__grade {
  position: absolute;
  top: var(--sp-4);
  right: var(--sp-4);
  min-width: 52px;
  padding: var(--sp-1) var(--sp-2);
  background: var(--c-accent);
  color: var(--c-on-accent);
  font-size: var(--fs-h1);
  font-weight: 900;
  line-height: 1.1;
  text-align: center;
  z-index: 1;
}

.share-card__head { text-align: center; }
.share-card__brand {
  font-size: var(--fs-micro);
  letter-spacing: 0.22em;
  margin-bottom: var(--sp-2);
}
.share-card__player { font-size: var(--fs-caption); color: var(--c-text-muted); }
.share-card__title {
  margin: var(--sp-2) 0 var(--sp-1);
  font-size: var(--fs-h1);
  font-weight: 800;
  color: var(--c-accent);
  letter-spacing: 0.08em;
}
.share-card__pro { font-size: var(--fs-caption); }

.share-card__radar { flex: 1; min-height: 0; }
.share-card__subs {
  display: flex;
  justify-content: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}
.share-card__roast {
  margin-top: var(--sp-3);
  text-align: center;
  font-size: var(--fs-body);
  color: var(--c-text);
  font-style: italic;
}
.share-card__foot {
  display: flex;
  justify-content: space-between;
  margin-top: var(--sp-3);
  font-size: var(--fs-caption);
}
.share-card__save { display: block; margin: var(--sp-3) auto 0; }
</style>
