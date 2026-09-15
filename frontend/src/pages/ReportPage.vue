<template>
  <div class="report">
    <UiCard v-if="!playerName" class="report__intro" cut>
      <UiEmpty
        title="先填入你的玩家名"
        description="在右上角填入玩家名（格式：昵称#数字ID）即可生成单场报告。"
      />
    </UiCard>

    <template v-else-if="loading">
      <UiCard class="report__intro"><UiSkeleton :lines="2" height="24px" /></UiCard>
      <UiCard><UiSkeleton :lines="1" height="32px" /></UiCard>
      <UiCard v-for="i in 2" :key="i"><UiSkeleton :lines="4" /></UiCard>
    </template>

    <UiCard v-else-if="error" class="report__intro">
      <UiEmpty title="无法生成报告" :description="error">
        <div class="report__error-actions">
          <UiButton variant="ghost" @click="load">重试</UiButton>
          <router-link to="/matches" class="report__back">返回战绩列表</router-link>
        </div>
      </UiEmpty>
    </UiCard>

    <template v-else-if="report && match">
      <!-- 报告头：比分 / 结果 / 评级 -->
      <UiCard class="report__head" cut>
        <div class="head">
          <div class="head__score">
            <span class="head__team muted">我方</span>
            <span class="head__num num" :class="`head__num--${resultKey}`">{{ myScore }}</span>
            <span class="head__sep muted">:</span>
            <span class="head__num num head__num--opp">{{ oppScore }}</span>
            <span class="head__team muted">敌方</span>
          </div>
          <div class="head__meta">
            <UiTag :tone="resultKey" dot>{{ resultText }}</UiTag>
            <span class="muted">{{ match.map }} · {{ match.mode }} · {{ matchDate }}</span>
          </div>
          <div class="head__side">
            <UiTag tone="accent">评级 {{ grade }}</UiTag>
            <UiTag v-if="report.mock" tone="warn" dot>演示数据</UiTag>
          </div>
        </div>
      </UiCard>

      <UiTabs v-model="activeTab" :tabs="tabs">
        <template #default="{ active }">
          <!-- Tab 1 战况总览 -->
          <div v-if="active === 'overview'" class="tab-stack">
            <UiCard title="比分演进">
              <template v-if="progression.length">
                <div class="evo">
                  <div class="evo__bar">
                    <template v-for="(cell, i) in progression" :key="cell.round_num">
                      <span v-if="i === halfIndex" class="evo__half-line" title="半场" />
                      <span
                        class="evo__cell"
                        :class="`evo__cell--${cell.outcome}`"
                        :title="`第 ${cell.round_num} 回合后 ${cell.my}:${cell.opp}`"
                      />
                    </template>
                  </div>
                  <div class="evo__labels muted num">
                    <span>上半场 {{ halfScore.my }}:{{ halfScore.opp }}</span>
                    <span>下半场 {{ secondHalf.my }}:{{ secondHalf.opp }}</span>
                    <span>终场 {{ myScore }}:{{ oppScore }}</span>
                  </div>
                </div>
              </template>
              <UiEmpty v-else title="无回合级数据" description="该对局缺少回合明细，无法绘制比分演进。" />
            </UiCard>

            <UiCard title="半场对比">
              <div class="halves">
                <div v-for="h in halfStats" :key="h.label" class="half cut-corner-tr">
                  <span class="half__label muted">{{ h.label }}</span>
                  <span class="half__score num">{{ h.my }} : {{ h.opp }}</span>
                  <div class="half__stats">
                    <span class="num">击杀 {{ h.kills }}</span>
                    <span class="num half__fb">首杀 {{ h.firstBloods }}</span>
                    <span class="num half__fd">首死 {{ h.firstDeaths }}</span>
                  </div>
                </div>
              </div>
            </UiCard>

            <UiCard title="关键时刻">
              <ol v-if="moments.length" class="moments">
                <li v-for="(m, i) in moments" :key="i" class="moments__item">
                  <span class="moments__idx num">{{ String(i + 1).padStart(2, '0') }}</span>
                  <span>{{ m }}</span>
                </li>
              </ol>
              <UiEmpty v-else title="暂无关键时刻点评" />
            </UiCard>
          </div>

          <!-- Tab 2 记分板与对位 -->
          <MatchupBoard v-else-if="active === 'board'" :match="match" :player-name="playerName" />

          <!-- Tab 3 回合分解 -->
          <UiCard v-else-if="active === 'rounds'" title="回合分解">
            <RoundTimeline v-if="match.rounds?.length" :rounds="match.rounds" :my-team="myTeam" />
            <UiEmpty v-else title="无回合级数据" description="该对局缺少回合明细。" />
          </UiCard>

          <!-- Tab 4 AI 复盘 -->
          <div v-else-if="active === 'review'" class="tab-stack">
            <UiCard title="总评">
              <template #actions>
                <UiTag v-if="report.mock" tone="warn" dot>演示数据</UiTag>
              </template>
              <p v-for="(para, i) in overviewParas" :key="i" class="review__para">{{ para }}</p>
              <UiEmpty v-if="!overviewParas.length" title="暂无总评" />
            </UiCard>

            <UiCard title="六维诊断">
              <div class="dims">
                <section v-for="d in dimReviews" :key="d.key" class="dim">
                  <header class="dim__head">
                    <span class="dim__name">{{ d.label }}</span>
                    <span class="dim__score num">{{ d.score }}</span>
                  </header>
                  <p class="dim__text">{{ d.text }}</p>
                </section>
              </div>
            </UiCard>

            <UiCard v-if="deep.roast" title="锐评" class="review__roast">
              <blockquote class="roast">“{{ deep.roast }}”</blockquote>
            </UiCard>
          </div>

          <!-- Tab 5 训练建议 -->
          <div v-else-if="active === 'training'" class="tab-stack">
            <UiCard title="本场问题点">
              <UiEmpty v-if="!problems.length" title="本场未发现明显问题点" description="各维度均在段位基准之上，保持当前训练节奏。" />
              <div v-else class="problems">
                <div v-for="(p, i) in problems" :key="i" class="problem">
                  <div class="problem__head">
                    <UiTag tone="loss" dot>{{ dimLabel(p.dimension) }}</UiTag>
                    <span class="problem__title">{{ p.description }}</span>
                  </div>
                  <p v-if="p.evidence" class="problem__evidence muted">数据依据：{{ p.evidence }}</p>
                </div>
              </div>
            </UiCard>

            <UiCard title="训练处方">
              <UiEmpty v-if="!prescription.length" title="暂无训练处方" />
              <div v-else class="tasks">
                <div v-for="t in prescription" :key="t.name" class="task">
                  <div class="task__head">
                    <span class="task__name">{{ t.name }}</span>
                    <UiTag tone="info">{{ t.tool }}</UiTag>
                    <span class="task__freq muted num">{{ t.freq }}</span>
                  </div>
                  <p class="task__detail muted">{{ t.detail }}</p>
                </div>
              </div>
              <div class="tasks__footer">
                <UiButton @click="router.push('/plan')">前往训练中心</UiButton>
              </div>
            </UiCard>
          </div>
        </template>
      </UiTabs>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listMatches, getAnalysis } from '../api'
import { playerName } from '../player'
import MatchupBoard from '../components/MatchupBoard.vue'
import RoundTimeline from '../components/RoundTimeline.vue'
import { UiButton, UiCard, UiEmpty, UiSkeleton, UiTabs, UiTag } from '../components/ui'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const error = ref('')
const report = ref(null)
const match = ref(null)
const activeTab = ref('overview')

const tabs = [
  { key: 'overview', label: '战况总览' },
  { key: 'board', label: '记分板与对位' },
  { key: 'rounds', label: '回合分解' },
  { key: 'review', label: 'AI 复盘' },
  { key: 'training', label: '训练建议' },
]

const DIM_LABELS = {
  aim: '瞄准', duel: '对枪', awareness: '意识',
  economy: '经济', utility: '技能', consistency: '稳定',
}
function dimLabel(key) {
  return DIM_LABELS[key] || key
}

const deep = computed(() => report.value?.deep || {})
const problems = computed(() => report.value?.problems || [])
const prescription = computed(() => deep.value.prescription || [])
const moments = computed(() => deep.value.moments || [])
const grade = computed(() => report.value?.scores?.grade || '—')

const overviewParas = computed(() =>
  (deep.value.overview || '').split(/\n+/).map((s) => s.trim()).filter(Boolean)
)

const dimReviews = computed(() =>
  Object.keys(DIM_LABELS).map((key) => ({
    key,
    label: DIM_LABELS[key],
    score: Math.round(report.value?.scores?.[key] ?? 0),
    text: deep.value.dimensions?.[key] || '暂无该维度诊断。',
  }))
)

const me = computed(() =>
  match.value?.players?.find((p) => p.name === playerName.value) || null
)
const myTeam = computed(() => me.value?.team || 'blue')

const myScore = computed(() =>
  myTeam.value === 'blue' ? match.value?.blue_score ?? 0 : match.value?.red_score ?? 0
)
const oppScore = computed(() =>
  myTeam.value === 'blue' ? match.value?.red_score ?? 0 : match.value?.blue_score ?? 0
)

const resultKey = computed(() => {
  if (myScore.value > oppScore.value) return 'win'
  if (myScore.value < oppScore.value) return 'loss'
  return 'draw'
})
const resultText = computed(
  () => ({ win: '胜利', loss: '败北', draw: '平局' })[resultKey.value]
)

const matchDate = computed(() => {
  const d = new Date(match.value?.started_at)
  if (Number.isNaN(d.getTime())) return ''
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}月${d.getDate()}日 ${pad(d.getHours())}:${pad(d.getMinutes())}`
})

// 比分演进：逐回合累计比分（我方视角）
const progression = computed(() => {
  let my = 0
  let opp = 0
  return (match.value?.rounds || []).map((r) => {
    const win = r.winning_team === myTeam.value
    if (win) my += 1
    else opp += 1
    return { round_num: r.round_num, my, opp, outcome: win ? 'win' : 'loss' }
  })
})

// 半场切分：标准 12 回合半场；不足时按中点切
const halfIndex = computed(() => {
  const n = progression.value.length
  return n > 12 ? 12 : Math.ceil(n / 2)
})

const halfScore = computed(() => {
  const h = progression.value[halfIndex.value - 1]
  return h ? { my: h.my, opp: h.opp } : { my: 0, opp: 0 }
})
const secondHalf = computed(() => ({
  my: myScore.value - halfScore.value.my,
  opp: oppScore.value - halfScore.value.opp,
}))

const halfStats = computed(() => {
  const rounds = match.value?.rounds || []
  const split = halfIndex.value
  const build = (list, label) => ({
    label,
    my: list.filter((r) => r.winning_team === myTeam.value).length,
    opp: list.filter((r) => r.winning_team !== myTeam.value).length,
    kills: list.reduce((s, r) => s + (r.player_kills ?? 0), 0),
    firstBloods: list.filter((r) => r.player_first_blood).length,
    firstDeaths: list.filter((r) => r.player_first_death).length,
  })
  return [
    build(rounds.slice(0, split), '上半场'),
    build(rounds.slice(split), '下半场'),
  ]
})

async function load() {
  loading.value = true
  error.value = ''
  report.value = null
  match.value = null
  try {
    const [matches, analysis] = await Promise.all([
      listMatches(playerName.value, 50),
      getAnalysis(route.params.matchId, playerName.value),
    ])
    const found =
      (Array.isArray(matches) ? matches : []).find(
        (m) => m.match_id === route.params.matchId
      ) || null
    if (!found) {
      error.value = '找不到该对局的详情数据，无法生成报告'
      return
    }
    report.value = analysis
    match.value = found
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
  if (name === prev) return
  if (name) {
    load()
  } else {
    report.value = null
    match.value = null
    error.value = ''
  }
})

watch(
  () => route.params.matchId,
  (id, prev) => {
    if (id && id !== prev && playerName.value) {
      activeTab.value = 'overview'
      load()
    }
  }
)
</script>

<style scoped>
.report {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}
.report__error-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}
.report__back { font-size: var(--fs-body); text-decoration: none; }

/* 报告头 */
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  flex-wrap: wrap;
}
.head__score { display: flex; align-items: baseline; gap: var(--sp-2); }
.head__team { font-size: var(--fs-caption); letter-spacing: 0.08em; }
.head__num {
  font-size: var(--fs-display);
  font-weight: 900;
  line-height: 1;
}
.head__num--win { color: var(--c-win); }
.head__num--loss { color: var(--c-loss); }
.head__num--draw { color: var(--c-draw); }
.head__num--opp { color: var(--c-text); }
.head__sep { font-size: var(--fs-h1); font-weight: 700; }
.head__meta { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.head__side { display: flex; align-items: center; gap: var(--sp-2); }

.tab-stack {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

/* 比分演进 */
.evo__bar {
  display: flex;
  align-items: stretch;
  gap: 2px;
  height: 28px;
}
.evo__cell { flex: 1; border-radius: var(--r-sm); }
.evo__cell--win { background: var(--c-win); }
.evo__cell--loss { background: var(--c-loss); }
.evo__half-line {
  width: 2px;
  background: var(--c-text-faint);
}
.evo__labels {
  display: flex;
  justify-content: space-between;
  gap: var(--sp-3);
  margin-top: var(--sp-2);
  font-size: var(--fs-caption);
}

/* 半场对比 */
.halves {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--sp-3);
}
.half {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  background: var(--c-surface-1);
  border: 1px solid var(--c-border);
  padding: var(--sp-3) var(--sp-4);
}
.half__label { font-size: var(--fs-caption); letter-spacing: 0.08em; }
.half__score {
  font-size: var(--fs-data);
  font-weight: 800;
  line-height: 1;
  color: var(--c-text);
}
.half__stats {
  display: flex;
  gap: var(--sp-3);
  font-size: var(--fs-caption);
  color: var(--c-text-muted);
}
.half__fb { color: var(--c-firstblood); }
.half__fd { color: var(--c-loss); }

/* 关键时刻 */
.moments {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}
.moments__item {
  display: flex;
  gap: var(--sp-3);
  align-items: baseline;
  background: var(--c-surface-1);
  border: 1px solid var(--c-border);
  border-radius: var(--r-sm);
  padding: var(--sp-2) var(--sp-3);
}
.moments__idx {
  color: var(--c-accent);
  font-weight: 800;
  font-size: var(--fs-h3);
  flex-shrink: 0;
}

/* AI 复盘 */
.review__para { margin: 0 0 var(--sp-3); }
.review__para:last-child { margin-bottom: 0; }
.dims {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--sp-3);
}
.dim {
  background: var(--c-surface-1);
  border: 1px solid var(--c-border);
  border-radius: var(--r-sm);
  padding: var(--sp-3);
}
.dim__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--sp-2);
}
.dim__name { font-weight: 700; letter-spacing: 0.04em; }
.dim__score {
  font-size: var(--fs-h2);
  font-weight: 800;
  color: var(--c-accent);
}
.dim__text { margin: 0; font-size: var(--fs-body); color: var(--c-text-muted); }
.roast {
  margin: 0;
  padding-left: var(--sp-3);
  border-left: 3px solid var(--c-accent);
  font-size: var(--fs-h3);
  font-style: italic;
}

/* 训练建议 */
.problems {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}
.problem {
  background: var(--c-surface-1);
  border: 1px solid var(--c-border);
  border-left: 3px solid var(--c-loss);
  border-radius: var(--r-sm);
  padding: var(--sp-3);
}
.problem__head {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}
.problem__title { font-weight: 600; }
.problem__evidence { margin: var(--sp-2) 0 0; font-size: var(--fs-caption); }

.tasks {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}
.task {
  background: var(--c-surface-1);
  border: 1px solid var(--c-border);
  border-radius: var(--r-sm);
  padding: var(--sp-3);
}
.task__head {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}
.task__name { font-weight: 700; }
.task__freq { font-size: var(--fs-caption); margin-left: auto; }
.task__detail { margin: var(--sp-2) 0 0; font-size: var(--fs-body); }
.tasks__footer { margin-top: var(--sp-3); display: flex; justify-content: flex-end; }
</style>
