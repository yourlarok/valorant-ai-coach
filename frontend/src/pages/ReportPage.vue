<template>
  <div>
    <p v-if="!playerName" class="panel muted">请先在右上角填入你的玩家名（昵称#数字ID）。</p>
    <p v-else-if="loading" class="panel muted">加载中，正在生成对局报告…</p>

    <div v-else-if="error" class="panel">
      <p class="accent">{{ error }}</p>
      <button @click="load">重试</button>
      <router-link to="/matches" class="back-link muted">返回战绩列表</router-link>
    </div>

    <template v-else-if="report">
      <div class="panel scoreboard-head">
        <div class="score-line">
          <span class="score-num">{{ match?.blue_score ?? '—' }}</span>
          <span class="score-sep">:</span>
          <span class="score-num red">{{ match?.red_score ?? '—' }}</span>
        </div>
        <p class="muted">{{ match?.map }} · {{ match?.mode }}</p>
      </div>

      <div class="report-grid">
        <div class="panel">
          <h3>记分板</h3>
          <table class="board">
            <thead>
              <tr>
                <th>玩家</th>
                <th>英雄</th>
                <th>K/D/A</th>
                <th>ACS</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="p in boardRows"
                :key="p.puuid || p.name"
                :class="{ me: p.name === playerName, ally: p.team === myTeam }"
              >
                <td>{{ p.name }}</td>
                <td>{{ p.agent }}</td>
                <td>{{ p.kills }}/{{ p.deaths }}/{{ p.assists }}</td>
                <td>{{ acs(p) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="right-col">
          <div class="panel">
            <h3>AI 总结 <span v-if="grade" class="grade accent">{{ grade }}</span></h3>
            <p>{{ report.analysis?.summary || '暂无总结' }}</p>
          </div>

          <div class="panel" v-if="strengths.length">
            <h3 class="green">优势</h3>
            <ul class="strength-list">
              <li v-for="(s, i) in strengths" :key="i">{{ s }}</li>
            </ul>
          </div>

          <div class="panel" v-if="report.problems?.length">
            <h3 class="red-text">问题点</h3>
            <div v-for="(p, i) in report.problems" :key="i" class="problem-card">
              <div class="problem-title">{{ dimLabel(p.dimension) }}</div>
              <p>{{ p.description }}</p>
              <p v-if="p.evidence" class="evidence">数据依据：{{ p.evidence }}</p>
            </div>
          </div>

          <div v-if="report.analysis?.roast" class="panel roast">
            <h3>锐评</h3>
            <blockquote>“{{ report.analysis.roast }}”</blockquote>
          </div>
        </div>
      </div>

      <div class="panel bottom">
        <h3>本场六维评分（综合 {{ overall }}）</h3>
        <RadarChart :scores="report.scores" />
        <button @click="router.push('/plan')">生成训练计划</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listMatches, getAnalysis } from '../api'
import { playerName } from '../player'
import RadarChart from '../components/RadarChart.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const error = ref('')
const report = ref(null)
const match = ref(null)

const DIM_LABELS = {
  aim: '瞄准', duel: '对枪', awareness: '意识',
  economy: '经济', utility: '技能', consistency: '稳定',
}
function dimLabel(key) {
  return DIM_LABELS[key] || key
}

const overall = computed(() => Math.round(report.value?.scores?.overall ?? 0))
const grade = computed(() => report.value?.scores?.grade || '')
const strengths = computed(() => report.value?.analysis?.strengths || [])

const me = computed(() =>
  match.value?.players?.find((p) => p.name === playerName.value) || null
)
const myTeam = computed(() => me.value?.team || '')

const rounds = computed(() =>
  (match.value?.blue_score ?? 0) + (match.value?.red_score ?? 0)
)
function acs(p) {
  return rounds.value > 0 ? Math.round(p.score / rounds.value) : '—'
}

const boardRows = computed(() => {
  const players = match.value?.players || []
  const rank = (p) =>
    p.name === playerName.value ? 0 : p.team === myTeam.value ? 1 : 2
  return [...players].sort((a, b) => rank(a) - rank(b) || b.score - a.score)
})

async function load() {
  loading.value = true
  error.value = ''
  report.value = null
  match.value = null
  try {
    const [matches, analysis] = await Promise.all([
      listMatches(playerName.value),
      getAnalysis(route.params.matchId, playerName.value),
    ])
    report.value = analysis
    match.value =
      (Array.isArray(matches) ? matches : []).find(
        (m) => m.match_id === route.params.matchId
      ) || null
  } catch (e) {
    error.value = e.message || '对局不存在或该玩家不在此对局'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (playerName.value) load()
})

watch(playerName, (name, prev) => {
  if (name && name !== prev) load()
})
</script>

<style scoped>
h3 { margin-top: 0; }
.scoreboard-head { text-align: center; margin-bottom: 20px; }
.score-line { font-size: 40px; font-weight: 800; }
.score-num { color: #4ade80; }
.score-num.red { color: var(--accent); }
.score-sep { color: var(--muted); margin: 0 12px; }
.report-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 20px; align-items: start; margin-bottom: 20px;
}
@media (max-width: 860px) {
  .report-grid { grid-template-columns: 1fr; }
}
.right-col { display: flex; flex-direction: column; gap: 20px; }
.board { width: 100%; border-collapse: collapse; font-size: 13px; }
.board th {
  text-align: left; color: var(--muted); font-weight: 500;
  padding: 6px 8px; border-bottom: 1px solid #2b3a47;
}
.board td { padding: 7px 8px; border-bottom: 1px solid #111c26; }
.board tr.ally td { background: rgba(74, 222, 128, 0.06); }
.board tr.me td { background: rgba(255, 70, 85, 0.15); font-weight: 700; }
.grade { margin-left: 8px; font-size: 18px; }
.green { color: #4ade80; }
.red-text { color: var(--accent); }
.strength-list { margin: 0; padding-left: 18px; }
.strength-list li { color: #4ade80; margin-bottom: 6px; }
.problem-card {
  background: #111c26; border-left: 3px solid var(--accent);
  border-radius: 4px; padding: 10px 14px; margin-bottom: 10px;
}
.problem-card p { margin: 6px 0 0; font-size: 14px; }
.problem-title { font-weight: 700; color: var(--accent); }
.evidence { color: var(--muted); font-size: 13px; }
.roast blockquote {
  margin: 0; padding-left: 12px; border-left: 3px solid var(--accent);
  font-size: 16px; font-style: italic;
}
.bottom { text-align: center; }
.bottom button { margin-top: 8px; }
.back-link { margin-left: 16px; font-size: 14px; }
</style>
