<template>
  <div class="matches">
    <UiCard v-if="!playerName" class="matches__intro" cut>
      <UiEmpty
        title="先填入你的玩家名"
        description="在右上角填入玩家名（格式：昵称#数字ID）即可查看战绩中心。演示玩家：测试玩家#1234"
      />
    </UiCard>

    <template v-else>
      <UiCard class="matches__filters" flush>
        <div class="filters">
          <label class="filters__item">
            <span class="filters__label">地图</span>
            <select v-model="filterMap" class="filters__select">
              <option value="">全部地图</option>
              <option v-for="m in mapOptions" :key="m" :value="m">{{ m }}</option>
            </select>
          </label>
          <label class="filters__item">
            <span class="filters__label">英雄</span>
            <select v-model="filterAgent" class="filters__select">
              <option value="">全部英雄</option>
              <option v-for="a in agentOptions" :key="a" :value="a">{{ a }}</option>
            </select>
          </label>
          <label class="filters__item">
            <span class="filters__label">胜负</span>
            <select v-model="filterResult" class="filters__select">
              <option value="">全部</option>
              <option value="win">胜利</option>
              <option value="loss">败北</option>
              <option value="draw">平局</option>
            </select>
          </label>
          <span class="filters__count muted num">
            {{ filteredRows.length }} / {{ rows.length }} 场
          </span>
        </div>
      </UiCard>

      <template v-if="loading">
        <UiCard v-for="i in 3" :key="i">
          <UiSkeleton :lines="3" />
        </UiCard>
      </template>

      <UiCard v-else-if="error" class="matches__intro">
        <UiEmpty title="战绩加载失败" :description="error">
          <UiButton variant="ghost" @click="load">重试</UiButton>
        </UiEmpty>
      </UiCard>

      <UiCard v-else-if="!rows.length" class="matches__intro">
        <UiEmpty
          title="没有找到该玩家的对局记录"
          description="确认玩家名拼写，或先打几把再回来。演示玩家：测试玩家#1234"
        />
      </UiCard>

      <UiCard v-else-if="!filteredRows.length" class="matches__intro">
        <UiEmpty title="没有符合筛选条件的对局" description="调整地图 / 英雄 / 胜负筛选试试。">
          <UiButton variant="ghost" @click="resetFilters">清除筛选</UiButton>
        </UiEmpty>
      </UiCard>

      <section v-else v-for="group in groupedRows" :key="group.date" class="match-group">
        <header class="match-group__head">
          <h3 class="match-group__date">{{ group.label }}</h3>
          <span class="match-group__meta muted num">
            {{ group.rows.length }} 场 ·
            <span class="t-win">{{ group.wins }} 胜</span> /
            <span class="t-loss">{{ group.rows.length - group.wins - group.draws }} 负</span>
            <template v-if="group.draws"> / {{ group.draws }} 平</template>
          </span>
        </header>
        <UiCard flush>
          <UiTable
            :columns="columns"
            :rows="group.rows"
            row-key="matchId"
            empty-text="暂无对局"
          >
            <template #cell-result="{ row }">
              <UiTag :tone="row.result.tone" dot>{{ row.result.text }}</UiTag>
            </template>
            <template #cell-actions="{ row }">
              <UiButton variant="ghost" size="sm" @click="goReport(row.matchId)">
                查看报告
              </UiButton>
            </template>
          </UiTable>
        </UiCard>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listMatches } from '../api'
import { playerName } from '../player'
import { UiButton, UiCard, UiEmpty, UiSkeleton, UiTable, UiTag } from '../components/ui'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const matches = ref([])

const filterMap = ref('')
const filterAgent = ref('')
const filterResult = ref('')

const columns = [
  { key: 'time', label: '时间', width: '10%' },
  { key: 'map', label: '地图' },
  { key: 'agent', label: '英雄' },
  { key: 'kda', label: 'K / D / A', numeric: true },
  { key: 'acs', label: 'ACS', numeric: true },
  { key: 'hsRate', label: 'HS%', numeric: true },
  { key: 'adr', label: 'ADR', numeric: true },
  { key: 'result', label: '胜负' },
  { key: 'actions', label: '', align: 'right' },
]

function findMe(match) {
  return match.players?.find((p) => p.name === playerName.value) || null
}

const pad = (n) => String(n).padStart(2, '0')

function dateKey(iso) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '未知日期'
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function dateLabel(key) {
  const today = dateKey(new Date().toISOString())
  const yesterday = dateKey(new Date(Date.now() - 86400000).toISOString())
  if (key === today) return `今天 · ${key}`
  if (key === yesterday) return `昨天 · ${key}`
  return key
}

function formatTime(iso) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const rows = computed(() =>
  matches.value.map((match) => {
    const me = findMe(match)
    const totalRounds =
      match.rounds?.length || (match.blue_score ?? 0) + (match.red_score ?? 0) || 1
    const shots = me ? (me.headshots ?? 0) + (me.bodyshots ?? 0) + (me.legshots ?? 0) : 0
    let result = { text: '—', tone: 'draw', key: 'draw' }
    if (me) {
      const myScore = me.team === 'blue' ? match.blue_score : match.red_score
      const oppScore = me.team === 'blue' ? match.red_score : match.blue_score
      if (myScore > oppScore) result = { text: '胜利', tone: 'win', key: 'win' }
      else if (myScore < oppScore) result = { text: '败北', tone: 'loss', key: 'loss' }
    }
    return {
      matchId: match.match_id,
      date: dateKey(match.started_at),
      time: formatTime(match.started_at),
      map: match.map || '—',
      agent: me?.agent || '—',
      kda: me ? `${me.kills} / ${me.deaths} / ${me.assists}` : '—',
      acs: me ? me.score : '—',
      hsRate: shots ? `${Math.round((me.headshots / shots) * 100)}%` : '—',
      adr: me ? Math.round((me.damage_made ?? 0) / totalRounds) : '—',
      result,
    }
  })
)

const mapOptions = computed(() => [...new Set(rows.value.map((r) => r.map))].filter((m) => m !== '—'))
const agentOptions = computed(() => [...new Set(rows.value.map((r) => r.agent))].filter((a) => a !== '—'))

const filteredRows = computed(() =>
  rows.value.filter(
    (r) =>
      (!filterMap.value || r.map === filterMap.value) &&
      (!filterAgent.value || r.agent === filterAgent.value) &&
      (!filterResult.value || r.result.key === filterResult.value)
  )
)

const groupedRows = computed(() => {
  const groups = []
  const byDate = new Map()
  for (const r of filteredRows.value) {
    if (!byDate.has(r.date)) {
      const g = { date: r.date, label: dateLabel(r.date), rows: [], wins: 0, draws: 0 }
      byDate.set(r.date, g)
      groups.push(g)
    }
    const g = byDate.get(r.date)
    g.rows.push(r)
    if (r.result.key === 'win') g.wins += 1
    if (r.result.key === 'draw') g.draws += 1
  }
  return groups
})

function resetFilters() {
  filterMap.value = ''
  filterAgent.value = ''
  filterResult.value = ''
}

async function load() {
  loading.value = true
  error.value = ''
  matches.value = []
  try {
    const data = await listMatches(playerName.value, 50)
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
  if (!name) {
    matches.value = []
    error.value = ''
    resetFilters()
  }
})
</script>

<style scoped>
.matches {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}
.filters {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
  padding: var(--sp-3) var(--sp-4);
}
.filters__item { display: flex; align-items: center; gap: var(--sp-2); }
.filters__label {
  font-size: var(--fs-caption);
  letter-spacing: 0.06em;
  color: var(--c-text-muted);
}
.filters__select {
  background: var(--c-surface-1);
  border: 1px solid var(--c-border);
  color: var(--c-text);
  border-radius: var(--r-sm);
  padding: var(--sp-1) var(--sp-3);
  font-size: var(--fs-body);
  font-family: var(--font-ui);
  cursor: pointer;
  transition: border-color var(--dur-fast) var(--ease-out);
}
.filters__select:focus { outline: none; border-color: var(--c-accent); }
.filters__count { margin-left: auto; font-size: var(--fs-caption); }

.match-group { display: flex; flex-direction: column; gap: var(--sp-2); }
.match-group__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--sp-3);
}
.match-group__date {
  margin: 0;
  font-size: var(--fs-h3);
  font-weight: 700;
  letter-spacing: 0.04em;
}
.match-group__meta { font-size: var(--fs-caption); }
.t-win { color: var(--c-win); }
.t-loss { color: var(--c-loss); }
</style>
