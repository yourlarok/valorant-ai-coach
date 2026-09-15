<template>
  <div>
    <div v-if="!playerName" class="panel intro">
      <h2>欢迎来到 <span class="accent">无畏契约 AI 对局教练</span></h2>
      <p class="muted">在右上角输入框填入你的玩家名（格式：<code>昵称#数字ID</code>），回车后即可查看最近一局的风格称号与六维雷达图。</p>
      <input v-model="nameInput" placeholder="昵称#数字ID" @keyup.enter="save" />
      <button @click="save">开始分析</button>
    </div>

    <div v-else-if="loading" class="panel muted">加载中，正在拉取最近一场对局数据…</div>

    <div v-else-if="error" class="panel">
      <p class="accent">加载失败：{{ error }}</p>
      <p class="muted">提示：未配置 LLM key 时为纯数据模式，仍可查看评分与模板化锐评。</p>
      <button @click="load">重试</button>
    </div>

    <div v-else-if="result" class="home-grid">
      <ShareCard
        :primary="result.primary.title || result.primary"
        :subs="subTitles"
        :scores="result.scores"
        :roast="result.analysis?.roast || ''"
        :player-name="playerName"
      />
      <div class="panel side">
        <h3>六维评分</h3>
        <RadarChart :scores="result.scores" />
        <div class="overall">
          综合评分：<span class="accent overall-num">{{ overall }}</span>
        </div>
        <p v-if="result.analysis?.summary" class="muted">{{ result.analysis.summary }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { listMatches, getAnalysis } from '../api'
import RadarChart from '../components/RadarChart.vue'
import ShareCard from '../components/ShareCard.vue'

const STORAGE_KEY = 'val_player_name'
const playerName = ref('')
const nameInput = ref('')
const loading = ref(false)
const error = ref('')
const result = ref(null)

const subTitles = computed(() => {
  const subs = result.value?.subs || []
  return subs.map((s) => (typeof s === 'string' ? s : s.title || s.name || String(s)))
})

const overall = computed(() => {
  const vals = Object.values(result.value?.scores || {})
  if (!vals.length) return 0
  return Math.round(vals.reduce((a, b) => a + b, 0) / vals.length)
})

function save() {
  const name = nameInput.value.trim()
  if (!name) return
  localStorage.setItem(STORAGE_KEY, name)
  playerName.value = name
  load()
}

async function load() {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const matches = await listMatches(playerName.value)
    if (!matches || !matches.length) {
      error.value = '没有找到该玩家的对局记录'
      return
    }
    const latest = matches[0]
    result.value = await getAnalysis(latest.match_id, playerName.value)
  } catch (e) {
    error.value = e.message || '请求失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  playerName.value = localStorage.getItem(STORAGE_KEY) || ''
  if (playerName.value) load()
})
</script>

<style scoped>
.intro h2 { margin-top: 0; }
.intro input { margin-right: 10px; }
.home-grid {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 20px;
  align-items: start;
}
@media (max-width: 860px) {
  .home-grid { grid-template-columns: 1fr; }
}
.side h3 { margin-top: 0; }
.overall { text-align: center; margin-top: 8px; }
.overall-num { font-size: 28px; font-weight: 800; }
</style>
