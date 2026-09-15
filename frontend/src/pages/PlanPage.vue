<template>
  <div>
    <p v-if="!playerName" class="panel muted">请先在右上角填入你的玩家名（昵称#数字ID）。</p>
    <p v-else-if="loading" class="panel muted">加载中，正在生成训练计划…</p>

    <div v-else-if="error" class="panel">
      <p class="accent">{{ error }}</p>
      <button @click="loadPlan">重试</button>
    </div>

    <template v-else>
      <div class="panel">
        <h2>训练计划</h2>
        <p v-if="toggleError" class="accent toggle-error">{{ toggleError }}</p>
        <div class="task-list">
          <label
            v-for="t in tasks"
            :key="t.name"
            class="task-card"
            :class="{ done: t.done }"
          >
            <input
              type="checkbox"
              :checked="t.done"
              @change="onToggle(t, $event.target.checked)"
            />
            <div class="task-body">
              <div class="task-head">
                <span class="task-name">{{ t.name }}</span>
                <span class="tool-tag" :style="tagStyle(t.tool)">{{ t.tool }}</span>
                <span class="freq muted">{{ t.freq }}</span>
              </div>
              <p class="detail muted">{{ t.detail }}</p>
            </div>
          </label>
        </div>
      </div>

      <div class="panel retest">
        <div class="retest-head">
          <h3>复测</h3>
          <button :disabled="retestLoading" @click="retest">
            {{ retestLoading ? '复测中…' : '重新拉取最近对局复测' }}
          </button>
        </div>
        <p v-if="retestError" class="accent">{{ retestError }}</p>

        <template v-if="currentScores">
          <p class="muted">
            {{ prevSnapshot ? `与上次快照（${prevSnapshot.date}）对比` : '首次复测，已记录为基线快照' }}
          </p>
          <table class="compare">
            <thead>
              <tr>
                <th>维度</th>
                <th>本次</th>
                <th>上次</th>
                <th>变化</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in compareRows" :key="row.key">
                <td>{{ row.label }}</td>
                <td>{{ row.current }}</td>
                <td>{{ row.prev ?? '—' }}</td>
                <td :class="deltaClass(row.delta)">{{ deltaText(row.delta) }}</td>
              </tr>
            </tbody>
          </table>
        </template>
      </div>

      <div class="panel">
        <h3>评分趋势</h3>
        <ScoreTrend :history="history" />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { getPlan, toggleTask, listMatches, getAnalysis } from '../api'
import { playerName } from '../player'
import ScoreTrend from '../components/ScoreTrend.vue'

const HISTORY_KEY = 'val_score_history'

const DIMS = [
  ['aim', '瞄准'],
  ['duel', '对枪'],
  ['awareness', '意识'],
  ['economy', '经济'],
  ['utility', '技能'],
  ['consistency', '稳定'],
  ['overall', '综合'],
]

const TAG_COLORS = ['#ff4655', '#4ade80', '#38bdf8', '#fbbf24', '#c084fc', '#f472b6']

const loading = ref(false)
const error = ref('')
const tasks = ref([])
const toggleError = ref('')

const history = ref(loadHistory())
const retestLoading = ref(false)
const retestError = ref('')
const currentScores = ref(null)
const prevSnapshot = ref(null)

function loadHistory() {
  try {
    const raw = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
    return Array.isArray(raw) ? raw : []
  } catch {
    return []
  }
}

function tagStyle(tool) {
  let hash = 0
  for (const ch of String(tool || '')) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0
  const color = TAG_COLORS[hash % TAG_COLORS.length]
  return { color, borderColor: color, backgroundColor: `${color}1f` }
}

const compareRows = computed(() => {
  const cur = currentScores.value
  if (!cur) return []
  const prev = prevSnapshot.value?.scores || null
  return DIMS.map(([key, label]) => {
    const current = Math.round(cur[key] ?? 0)
    const prevVal = prev && prev[key] != null ? Math.round(prev[key]) : null
    return {
      key,
      label,
      current,
      prev: prevVal,
      delta: prevVal == null ? null : current - prevVal,
    }
  })
})

function deltaText(delta) {
  if (delta == null) return '—'
  if (delta > 0) return `+${delta}`
  return String(delta)
}

function deltaClass(delta) {
  if (delta == null || delta === 0) return 'muted'
  return delta > 0 ? 'up' : 'down'
}

async function loadPlan() {
  loading.value = true
  error.value = ''
  tasks.value = []
  try {
    const data = await getPlan(playerName.value)
    tasks.value = data?.tasks || []
  } catch (e) {
    error.value = e.message || '获取训练计划失败'
  } finally {
    loading.value = false
  }
}

async function onToggle(task, done) {
  toggleError.value = ''
  const old = task.done
  task.done = done
  try {
    await toggleTask(playerName.value, task.name, done)
  } catch (e) {
    task.done = old
    toggleError.value = '打卡保存失败，请重试'
  }
}

async function retest() {
  retestLoading.value = true
  retestError.value = ''
  try {
    const matches = await listMatches(playerName.value)
    if (!matches || !matches.length) {
      retestError.value = '没有找到该玩家的对局记录'
      return
    }
    const analysis = await getAnalysis(matches[0].match_id, playerName.value)
    const scores = analysis?.scores
    if (!scores) {
      retestError.value = '分析结果中没有评分数据'
      return
    }
    const list = loadHistory()
    prevSnapshot.value = list.length ? list[list.length - 1] : null
    currentScores.value = scores
    const snap = { date: new Date().toISOString().slice(0, 10), scores }
    if (list.length && list[list.length - 1].date === snap.date) {
      list[list.length - 1] = snap
    } else {
      list.push(snap)
    }
    localStorage.setItem(HISTORY_KEY, JSON.stringify(list))
    history.value = list
  } catch (e) {
    retestError.value = e.message || '复测失败'
  } finally {
    retestLoading.value = false
  }
}

function resetRetest() {
  currentScores.value = null
  prevSnapshot.value = null
  retestError.value = ''
  history.value = loadHistory()
}

onMounted(() => {
  if (playerName.value) loadPlan()
})

watch(playerName, (name, prev) => {
  if (name === prev) return
  resetRetest()
  toggleError.value = ''
  if (name) {
    loadPlan()
  } else {
    tasks.value = []
    error.value = ''
  }
})
</script>

<style scoped>
h2, h3 { margin-top: 0; }
.task-list { display: flex; flex-direction: column; gap: 12px; }
.task-card {
  display: flex; gap: 12px; align-items: flex-start;
  background: #111c26; border-radius: 6px; padding: 14px;
  cursor: pointer; border: 1px solid transparent;
}
.task-card.done { border-color: #2b3a47; opacity: 0.75; }
.task-card input { margin-top: 4px; accent-color: var(--accent); }
.task-body { flex: 1; }
.task-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.task-name { font-weight: 700; }
.task-card.done .task-name { text-decoration: line-through; color: var(--muted); }
.tool-tag {
  font-size: 12px; border: 1px solid; border-radius: 4px;
  padding: 1px 8px; white-space: nowrap;
}
.freq { font-size: 13px; }
.detail { margin: 6px 0 0; font-size: 14px; }
.toggle-error { font-size: 14px; }
.retest { margin-top: 20px; }
.retest-head {
  display: flex; justify-content: space-between;
  align-items: center; gap: 12px; flex-wrap: wrap;
}
.retest-head h3 { margin: 0; }
.retest button:disabled { opacity: 0.6; cursor: default; }
.compare { width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 8px; }
.compare th {
  text-align: left; color: var(--muted); font-weight: 500;
  padding: 6px 8px; border-bottom: 1px solid #2b3a47;
}
.compare td { padding: 7px 8px; border-bottom: 1px solid #111c26; }
.up { color: #4ade80; font-weight: 700; }
.down { color: var(--accent); font-weight: 700; }
.panel:last-child { margin-top: 20px; }
</style>
