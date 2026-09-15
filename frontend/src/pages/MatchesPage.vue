<template>
  <div class="panel">
    <h2>最近战绩</h2>

    <p v-if="!playerName" class="muted">请先在右上角填入你的玩家名（昵称#数字ID）。</p>
    <p v-else-if="loading" class="muted">加载中，正在拉取对局列表…</p>

    <div v-else-if="error">
      <p class="accent">加载失败：{{ error }}</p>
      <button @click="load">重试</button>
    </div>

    <p v-else-if="!matches.length" class="muted">没有找到该玩家的对局记录。</p>

    <table v-else class="match-table">
      <thead>
        <tr>
          <th>时间</th>
          <th>地图</th>
          <th>英雄</th>
          <th>KDA</th>
          <th>ACS</th>
          <th>胜负</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="m in rows"
          :key="m.match.match_id"
          class="match-row"
          @click="goReport(m.match.match_id)"
        >
          <td>{{ m.time }}</td>
          <td>{{ m.match.map }}</td>
          <td>{{ m.agent }}</td>
          <td>{{ m.kda }}</td>
          <td>{{ m.acs }}</td>
          <td>
            <span :class="['result', m.result.cls]">{{ m.result.text }}</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listMatches } from '../api'
import { playerName } from '../player'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const matches = ref([])

function findMe(match) {
  return match.players?.find((p) => p.name === playerName.value) || null
}

function formatTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const rows = computed(() =>
  matches.value.map((match) => {
    const me = findMe(match)
    let result = { text: '—', cls: 'draw' }
    if (me) {
      const myScore = me.team === 'blue' ? match.blue_score : match.red_score
      const oppScore = me.team === 'blue' ? match.red_score : match.blue_score
      if (myScore > oppScore) result = { text: '胜利', cls: 'win' }
      else if (myScore < oppScore) result = { text: '败北', cls: 'loss' }
      else result = { text: '平局', cls: 'draw' }
    }
    return {
      match,
      time: formatTime(match.started_at),
      agent: me?.agent || '—',
      kda: me ? `${me.kills} / ${me.deaths} / ${me.assists}` : '—',
      acs: me ? me.score : '—',
      result,
    }
  })
)

async function load() {
  loading.value = true
  error.value = ''
  matches.value = []
  try {
    const data = await listMatches(playerName.value)
    matches.value = Array.isArray(data) ? data : []
  } catch (e) {
    error.value = e.message || '请求失败'
  } finally {
    loading.value = false
  }
}

function goReport(matchId) {
  router.push(`/report/${matchId}`)
}

onMounted(() => {
  if (playerName.value) load()
})

watch(playerName, (name, prev) => {
  if (name && name !== prev) load()
  if (!name) matches.value = []
})
</script>

<style scoped>
h2 { margin-top: 0; }
.match-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.match-table th {
  text-align: left; color: var(--muted); font-weight: 500;
  padding: 8px 10px; border-bottom: 1px solid #2b3a47;
}
.match-table td { padding: 10px; border-bottom: 1px solid #111c26; }
.match-row { cursor: pointer; transition: background 0.15s; }
.match-row:hover { background: #111c26; }
.result { font-weight: 700; }
.result.win { color: #4ade80; }
.result.loss { color: var(--accent); }
.result.draw { color: var(--muted); }
</style>
