<template>
  <div class="plan">
    <UiCard v-if="!playerName" cut>
      <UiEmpty
        title="先绑定你的游戏身份"
        description="绑定玩家名（格式：昵称#数字ID）后即可生成本周训练计划。"
      >
        <router-link to="/onboarding">
          <UiButton>去绑定身份</UiButton>
        </router-link>
      </UiEmpty>
    </UiCard>

    <template v-else-if="loading">
      <UiCard><UiSkeleton :lines="4" height="20px" /></UiCard>
      <UiCard><UiSkeleton :lines="3" /></UiCard>
      <UiCard><UiSkeleton :lines="2" height="28px" /></UiCard>
    </template>

    <UiCard v-else-if="error">
      <UiEmpty title="无法生成训练计划" :description="error">
        <UiButton variant="ghost" @click="loadPlan">重试</UiButton>
      </UiEmpty>
    </UiCard>

    <template v-else>
      <!-- 本周计划 -->
      <UiCard title="本周计划" cut>
        <p v-if="toggleError" class="plan__error">{{ toggleError }}</p>
        <UiEmpty
          v-if="!tasks.length"
          title="暂无训练任务"
          description="后端尚未为该玩家生成训练任务，请稍后重试。"
        />
        <div v-else class="tasks">
          <label
            v-for="t in tasks"
            :key="t.name"
            class="task"
            :class="{ 'task--done': t.done }"
          >
            <input
              type="checkbox"
              :checked="t.done"
              @change="onToggle(t, $event.target.checked)"
            />
            <div class="task__body">
              <div class="task__head">
                <span class="task__name">{{ t.name }}</span>
                <UiTag :tone="tagTone(t.tool)">{{ t.tool }}</UiTag>
                <span class="task__freq muted num">{{ t.freq }}</span>
              </div>
              <p class="task__detail muted">{{ t.detail }}</p>
            </div>
            <span
              v-if="drillForTask(t)"
              class="task__go"
              @click.stop
            >
              <router-link
                :to="{ path: '/range', query: { drill: drillForTask(t) } }"
                class="task__go-link"
                @click.stop
              >
                去训练场 →
              </router-link>
            </span>
          </label>
        </div>
      </UiCard>

      <!-- 复测对比 -->
      <UiCard title="复测对比">
        <template #actions>
          <UiButton size="sm" variant="ghost" :disabled="retestLoading" @click="retest">
            {{ retestLoading ? '复测中…' : '重新拉取最近对局复测' }}
          </UiButton>
        </template>
        <p v-if="retestError" class="plan__error">{{ retestError }}</p>

        <UiEmpty
          v-if="!currentScores"
          title="尚未复测"
          description="点击右上角按钮，拉取最近一场对局重新评分，与上次快照对比。"
        />
        <template v-else>
          <p class="plan__compare-note muted">
            {{ prevSnapshot ? `与上次快照（${prevSnapshot.date}）对比` : '首次复测，已记录为基线快照' }}
          </p>
          <UiTable :columns="compareColumns" :rows="compareRows" row-key="key">
            <template #cell-prev="{ row }">
              <span class="num">{{ row.prev ?? '—' }}</span>
            </template>
            <template #cell-delta="{ row }">
              <span class="num" :class="deltaClass(row.delta)">{{ deltaText(row.delta) }}</span>
            </template>
          </UiTable>
        </template>
      </UiCard>

      <!-- 历史趋势 -->
      <UiCard title="历史趋势">
        <ScoreTrend :history="history" />
      </UiCard>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { getPlan, toggleTask, listMatches, getAnalysis } from '../api'
import { playerName } from '../player'
import ScoreTrend from '../components/ScoreTrend.vue'
import { UiButton, UiCard, UiEmpty, UiSkeleton, UiTable, UiTag } from '../components/ui'

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

const TAG_TONES = ['accent', 'win', 'info', 'firstblood', 'warn', 'loss']

// dimension → 内置科目映射；任务卡无 dimension 字段，按后端规则表任务名反查
const DRILL_BY_DIMENSION = {
  aim: 'headline_flick',
  duel: 'reaction',
  consistency: 'tracking',
}
const DIMENSION_BY_TASK = {
  'Sixshot 精准爆头': 'aim',
  爆头死斗: 'aim',
  预瞄点位练习: 'duel',
  死斗抢首发: 'duel',
  固定热身流程: 'consistency',
}

function drillForTask(task) {
  const dim = DIMENSION_BY_TASK[task.name]
  return dim ? DRILL_BY_DIMENSION[dim] : null
}

const compareColumns = [
  { key: 'label', label: '维度' },
  { key: 'current', label: '本次', numeric: true },
  { key: 'prev', label: '上次', numeric: true },
  { key: 'delta', label: '变化', numeric: true },
]

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

function tagTone(tool) {
  let hash = 0
  for (const ch of String(tool || '')) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0
  return TAG_TONES[hash % TAG_TONES.length]
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
  return delta > 0 ? 'plan__delta--up' : 'plan__delta--down'
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
.plan {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}
.plan__error {
  margin: 0 0 var(--sp-3);
  font-size: var(--fs-body);
  color: var(--c-loss);
}

/* 本周计划任务卡 */
.tasks {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}
.task {
  display: flex;
  gap: var(--sp-3);
  align-items: flex-start;
  background: var(--c-surface-1);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  padding: var(--sp-3);
  cursor: pointer;
  transition: border-color var(--dur-fast) var(--ease-out),
    opacity var(--dur-fast) var(--ease-out);
}
.task:hover { border-color: var(--c-border-strong); }
.task--done { opacity: 0.7; }
.task input { margin-top: 4px; accent-color: var(--c-accent); }
.task__body { flex: 1; }
.task__head {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}
.task__name { font-weight: 700; }
.task--done .task__name {
  text-decoration: line-through;
  color: var(--c-text-muted);
}
.task__freq { font-size: var(--fs-caption); }
.task__detail { margin: var(--sp-2) 0 0; font-size: var(--fs-body); }
.task__go { flex-shrink: 0; align-self: center; }
.task__go-link {
  font-size: var(--fs-caption);
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--c-accent);
  text-decoration: none;
  white-space: nowrap;
}
.task__go-link:hover { color: var(--c-accent-hover); text-decoration: underline; }

/* 复测对比 */
.plan__compare-note { margin: 0 0 var(--sp-2); }
.plan__delta--up { color: var(--c-win); font-weight: 700; }
.plan__delta--down { color: var(--c-loss); font-weight: 700; }
</style>
