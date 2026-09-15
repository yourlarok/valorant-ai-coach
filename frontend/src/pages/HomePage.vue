<template>
  <div class="dash">
    <!-- 空态：未绑定身份 -->
    <UiCard v-if="!playerName" class="dash__intro" cut>
      <UiEmpty
        title="欢迎来到无畏契约 AI 对局教练"
        description="先绑定你的游戏身份（昵称#数字ID），即可生成档案卡、六维评分与今日训练待办。"
      >
        <router-link to="/onboarding">
          <UiButton>去绑定身份</UiButton>
        </router-link>
      </UiEmpty>
    </UiCard>

    <!-- 骨架屏加载态 -->
    <template v-else-if="loading">
      <UiCard v-for="i in 4" :key="i" class="dash__skeleton" :class="`dash__skeleton--${i}`">
        <UiSkeleton :lines="3" />
      </UiCard>
    </template>

    <!-- 错误态 -->
    <UiCard v-else-if="error" class="dash__intro">
      <UiEmpty title="加载失败" :description="error">
        <UiButton variant="ghost" @click="load">重试</UiButton>
      </UiEmpty>
    </UiCard>

    <!-- Dashboard 栅格 -->
    <template v-else-if="result">
      <PlayerCard class="dash__player" :matches="matches" :player-name="playerName" />

      <UiCard class="dash__score" title="综合评分" cut>
        <div class="score">
          <div class="score__main">
            <span class="score__num num">{{ overall }}</span>
            <UiTag tone="accent" class="score__grade">{{ grade }} 级</UiTag>
          </div>
          <p v-if="result.analysis?.summary" class="score__summary muted">
            {{ result.analysis.summary }}
          </p>
          <div class="score__ext">
            <div v-for="s in extStats" :key="s.label" class="score__ext-item">
              <span class="score__ext-value num">{{ s.value }}</span>
              <span class="score__ext-label muted">{{ s.label }}</span>
            </div>
          </div>
        </div>
      </UiCard>

      <ShareCard
        class="dash__share"
        :primary="result.primary?.title || ''"
        :subs="subTitles"
        :scores="result.scores"
        :roast="result.analysis?.roast || ''"
        :player-name="playerName"
      />

      <UiCard class="dash__radar" title="六维雷达">
        <RadarChart :scores="result.scores" :height="240" />
      </UiCard>

      <UiCard class="dash__trend" title="近 5 场评分走势">
        <UiSkeleton v-if="trendLoading" :lines="2" height="20px" />
        <TrendMini v-else :points="trendPoints" />
      </UiCard>

      <UiCard class="dash__todo" title="今日训练待办">
        <template #actions>
          <router-link to="/plan" class="dash__link">全部计划</router-link>
        </template>
        <UiSkeleton v-if="planLoading" :lines="2" />
        <p v-else-if="!todoTasks.length" class="muted dash__note">
          {{ planDone ? '今日任务全部完成，继续保持。' : '暂无待办，去训练中心生成计划。' }}
        </p>
        <ul v-else class="todo">
          <li v-for="t in todoTasks" :key="t.name" class="todo__item">
            <div class="todo__body">
              <span class="todo__name">{{ t.name }}</span>
              <span class="todo__detail muted">{{ t.detail }}</span>
            </div>
            <div class="todo__meta">
              <UiTag tone="info">{{ t.tool }}</UiTag>
              <span class="todo__freq muted num">{{ t.freq }}</span>
            </div>
          </li>
        </ul>
      </UiCard>

      <UiCard class="dash__weekly" title="本周叙事">
        <UiSkeleton v-if="weeklyLoading" :lines="3" />
        <template v-else-if="weekly">
          <p class="weekly__narrative">{{ weekly.narrative }}</p>
          <div class="weekly__dims">
            <div v-if="weekly.improved?.length" class="weekly__row">
              <span class="weekly__label muted">进步</span>
              <UiTag v-for="d in weekly.improved" :key="d" tone="win">{{ d }}</UiTag>
            </div>
            <div v-if="weekly.regressed?.length" class="weekly__row">
              <span class="weekly__label muted">退步</span>
              <UiTag v-for="d in weekly.regressed" :key="d" tone="loss">{{ d }}</UiTag>
            </div>
            <span class="weekly__games muted num">样本 {{ weekly.games }} 场</span>
          </div>
        </template>
        <p v-else class="muted dash__note">周度分析暂不可用。</p>
      </UiCard>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { listMatches, getAnalysis, getWeekly, getPlan } from '../api'
import { playerName } from '../player'
import RadarChart from '../components/RadarChart.vue'
import ShareCard from '../components/ShareCard.vue'
import PlayerCard from '../components/PlayerCard.vue'
import TrendMini from '../components/TrendMini.vue'
import { UiButton, UiCard, UiEmpty, UiSkeleton, UiTag } from '../components/ui'

const loading = ref(false)
const error = ref('')
const matches = ref([])
const result = ref(null)

const weekly = ref(null)
const weeklyLoading = ref(false)
const planTasks = ref([])
const planLoading = ref(false)
const planDone = ref(false)
const trendPoints = ref([])
const trendLoading = ref(false)

const subTitles = computed(() => {
  const subs = result.value?.subs || []
  return subs.map((s) => (typeof s === 'string' ? s : s.title || s.name || String(s)))
})

const overall = computed(() => Math.round(result.value?.scores?.overall ?? 0))
const grade = computed(() => result.value?.scores?.grade || '—')

const extStats = computed(() => {
  const ext = result.value?.ext
  if (!ext) return []
  const pct = (v) => (v == null ? '—' : `${Math.round(v * 100)}%`)
  return [
    { label: 'ADR', value: ext.adr != null ? Math.round(ext.adr) : '—' },
    { label: 'KAST', value: pct(ext.kast) },
    { label: '首杀参与', value: pct(ext.fb_participation) },
    { label: '手枪局胜率', value: pct(ext.pistol_wr) },
  ]
})

const todoTasks = computed(() => planTasks.value.filter((t) => !t.done).slice(0, 3))

// 主数据：对局列表 + 最近一场深度分析（阻塞渲染）
async function load() {
  loading.value = true
  error.value = ''
  result.value = null
  matches.value = []
  try {
    const list = await listMatches(playerName.value)
    if (!list || !list.length) {
      error.value = '没有找到该玩家的对局记录，试试演示玩家：测试玩家#1234'
      return
    }
    matches.value = list
    result.value = await getAnalysis(list[0].match_id, playerName.value)
  } catch (e) {
    error.value = e.message || '请求失败'
  } finally {
    loading.value = false
  }
  loadAux()
}

// 辅助区块：周报 / 训练计划 / 评分趋势，失败不阻塞主内容
function loadAux() {
  weeklyLoading.value = true
  weekly.value = null
  getWeekly(playerName.value)
    .then((data) => { weekly.value = data })
    .catch(() => { weekly.value = null })
    .finally(() => { weeklyLoading.value = false })

  planLoading.value = true
  planTasks.value = []
  getPlan(playerName.value)
    .then((data) => {
      planTasks.value = data?.tasks || []
      planDone.value = planTasks.value.length > 0 && planTasks.value.every((t) => t.done)
    })
    .catch(() => { planTasks.value = [] })
    .finally(() => { planLoading.value = false })

  const recent = matches.value.slice(0, 5)
  trendPoints.value = []
  trendLoading.value = recent.length > 1
  Promise.all(
    recent.map((m) => getAnalysis(m.match_id, playerName.value).catch(() => null))
  )
    .then((results) => {
      trendPoints.value = recent
        .map((m, i) => ({
          label: m.map,
          score: Math.round(results[i]?.scores?.overall ?? NaN),
        }))
        .filter((p) => Number.isFinite(p.score))
        .reverse()
    })
    .finally(() => { trendLoading.value = false })
}

onMounted(() => {
  if (playerName.value) load()
})

watch(playerName, (name, prev) => {
  if (name === prev) return
  if (name) {
    load()
  } else {
    result.value = null
    matches.value = []
    error.value = ''
    weekly.value = null
    planTasks.value = []
    trendPoints.value = []
  }
})
</script>

<style scoped>
.dash {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--sp-3);
  align-items: start;
}

.dash__intro { grid-column: 1 / -1; }

.dash__skeleton { grid-column: span 6; }

.dash__player { grid-column: span 4; }
.dash__score { grid-column: span 4; }
.dash__share { grid-column: span 4; grid-row: span 2; }
.dash__radar { grid-column: span 4; }
.dash__trend { grid-column: span 4; }
.dash__todo { grid-column: span 6; }
.dash__weekly { grid-column: span 6; }

@media (max-width: 1080px) {
  .dash__player,
  .dash__score,
  .dash__share,
  .dash__radar,
  .dash__trend,
  .dash__todo,
  .dash__weekly {
    grid-column: span 6;
    grid-row: auto;
  }
}
@media (max-width: 720px) {
  .dash > * { grid-column: 1 / -1 !important; }
}

/* 综合评分大数字区 */
.score { display: flex; flex-direction: column; gap: var(--sp-3); }
.score__main { display: flex; align-items: baseline; gap: var(--sp-3); }
.score__num {
  font-size: var(--fs-display);
  font-weight: 900;
  line-height: 1;
  color: var(--c-accent);
}
.score__grade { transform: translateY(calc(-1 * var(--sp-1))); }
.score__summary { margin: 0; font-size: var(--fs-body); }
.score__ext {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-2);
}
.score__ext-item {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  background: var(--c-surface-1);
  border: 1px solid var(--c-border);
  border-radius: var(--r-sm);
  padding: var(--sp-2) var(--sp-3);
}
.score__ext-value { font-size: var(--fs-h3); font-weight: 700; }
.score__ext-label { font-size: var(--fs-caption); }

/* 今日训练待办 */
.dash__note { margin: 0; font-size: var(--fs-body); }
.todo {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}
.todo__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  background: var(--c-surface-1);
  border: 1px solid var(--c-border);
  border-radius: var(--r-sm);
  padding: var(--sp-2) var(--sp-3);
}
.todo__body { display: flex; flex-direction: column; min-width: 0; }
.todo__name { font-weight: 700; font-size: var(--fs-body); }
.todo__detail {
  font-size: var(--fs-caption);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.todo__meta { display: flex; align-items: center; gap: var(--sp-2); flex-shrink: 0; }
.todo__freq { font-size: var(--fs-caption); }
.dash__link { font-size: var(--fs-caption); text-decoration: none; }

/* 本周叙事 */
.weekly__narrative { margin: 0 0 var(--sp-3); font-size: var(--fs-body); }
.weekly__dims {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
}
.weekly__row { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; }
.weekly__label { font-size: var(--fs-caption); letter-spacing: 0.06em; }
.weekly__games { margin-left: auto; font-size: var(--fs-caption); }
</style>
