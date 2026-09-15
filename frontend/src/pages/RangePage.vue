<template>
  <div class="range">
    <!-- 科目进行视图 -->
    <DrillShell
      v-if="activeDrill"
      :drill="activeDrill.drill"
      :title="activeDrill.title"
      :duration="activeDrill.duration"
      :unit="activeDrill.unit"
      :decimals="activeDrill.decimals"
      :lower-is-better="activeDrill.lowerIsBetter"
      @finish="onFinish"
      @exit="closeDrill"
    >
      <template #default="slotProps">
        <HeadlineFlick
          v-if="activeDrill.drill === 'headline_flick'"
          v-bind="slotProps"
        />
        <ReactionDrill
          v-else-if="activeDrill.drill === 'reaction'"
          v-bind="slotProps"
        />
        <TrackingDrill
          v-else-if="activeDrill.drill === 'tracking'"
          v-bind="slotProps"
        />
      </template>
    </DrillShell>

    <!-- 训练场主页 -->
    <template v-else>
      <header class="range__head">
        <div>
          <h1 class="range__title">训练场</h1>
          <p class="range__subtitle muted">
            THE RANGE · 内置专项科目，成绩入库进入复测闭环
          </p>
        </div>
      </header>

      <p v-if="loadError" class="range__error">{{ loadError }}</p>

      <div class="range__grid">
        <UiCard
          v-for="d in drills"
          :key="d.drill"
          :title="d.title"
          class="range__card"
          :class="{ 'range__card--locked': !d.playable }"
          cut
        >
          <template #actions>
            <UiTag :tone="d.playable ? 'win' : 'neutral'" dot>
              {{ d.playable ? '可训练' : '即将上线' }}
            </UiTag>
          </template>
          <div class="range__card-body">
            <p class="range__card-en num">{{ d.en }}</p>
            <p class="range__card-desc muted">{{ d.desc }}</p>

            <div class="range__card-stats">
              <div class="range__stat">
                <span class="range__stat-label muted">最近成绩</span>
                <span class="range__stat-value num">
                  {{ latest[d.drill] != null ? formatScore(d, latest[d.drill]) : '—' }}
                </span>
              </div>
              <div class="range__stat">
                <span class="range__stat-label muted">
                  历史最佳{{ d.lowerIsBetter ? '·低优' : '' }}
                </span>
                <span class="range__stat-value num" :class="{ accent: bests[d.drill] != null }">
                  {{ bests[d.drill] != null ? formatScore(d, bests[d.drill]) : '—' }}
                </span>
              </div>
            </div>
            <ScoreSparkline
              class="range__spark"
              :points="trendOf(d.drill)"
              :lower-is-better="d.lowerIsBetter"
            />

            <div class="range__card-foot">
              <UiButton
                v-if="d.playable"
                size="sm"
                @click="openDrill(d)"
              >
                开始训练
              </UiButton>
              <UiButton v-else size="sm" variant="subtle" disabled>敬请期待</UiButton>
            </div>
          </div>
        </UiCard>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTrainingScores } from '../api'
import { playerName } from '../player'
import DrillShell from '../components/range/DrillShell.vue'
import HeadlineFlick from '../components/range/HeadlineFlick.vue'
import ReactionDrill from '../components/range/ReactionDrill.vue'
import TrackingDrill from '../components/range/TrackingDrill.vue'
import ScoreSparkline from '../components/range/ScoreSparkline.vue'
import { UiButton, UiCard, UiTag } from '../components/ui'

const drills = [
  {
    drill: 'headline_flick',
    title: '爆头线定位',
    en: 'HEADLINE FLICK',
    desc: '目标只会出现在爆头线高度带内。快速甩枪定位并点击命中，命中即刻刷新下一个。60 秒，得分 = 命中数 × 命中率。',
    duration: 60,
    playable: true,
    unit: '',
    decimals: 1,
    lowerIsBetter: false,
  },
  {
    drill: 'reaction',
    title: '反应速度',
    en: 'REACTION',
    desc: '画面变绿并出靶的瞬间尽快点击，共 5 轮取平均毫秒数，抢跑判罚时。成绩越低越好，对应「对枪」维度。',
    duration: 30,
    playable: true,
    unit: 'ms',
    decimals: 0,
    lowerIsBetter: true,
  },
  {
    drill: 'tracking',
    title: '跟枪追踪',
    en: 'TRACKING',
    desc: '目标沿平滑变速轨迹移动，准星持续压住目标累计命中时间。45 秒，得分 = 覆盖率百分比，对应「瞄准 / 稳定」维度。',
    duration: 45,
    playable: true,
    unit: '%',
    decimals: 1,
    lowerIsBetter: false,
  },
]

const route = useRoute()
const router = useRouter()

const activeDrill = ref(null)
const bests = ref({})
const latest = ref({})
const recent = ref({}) // drill -> 按时间正序的最近 5 次成绩
const loadError = ref('')

function formatScore(d, v) {
  return `${v.toFixed(d.decimals)}${d.unit}`
}

function trendOf(drill) {
  return recent.value[drill] || []
}

async function loadScores() {
  if (!playerName.value) return
  try {
    const data = await getTrainingScores(playerName.value)
    bests.value = data.bests || {}
    const byDrill = {}
    for (const s of data.scores || []) {
      (byDrill[s.drill] = byDrill[s.drill] || []).push(s.score)
    }
    latest.value = Object.fromEntries(
      Object.entries(byDrill).map(([k, list]) => [k, list[0]]),
    )
    // API 返回按时间倒序，翻转为正序供趋势展示
    recent.value = Object.fromEntries(
      Object.entries(byDrill).map(([k, list]) => [k, list.slice(0, 5).reverse()]),
    )
    loadError.value = ''
  } catch (e) {
    loadError.value = e.message || '获取历史成绩失败'
  }
}

function openDrill(d) {
  activeDrill.value = d
}

function onFinish() {
  loadScores()
}

function closeDrill() {
  activeDrill.value = null
  if (route.query.drill) router.replace({ path: '/range' })
  loadScores()
}

onMounted(() => {
  loadScores()
  // 训练计划跳转直达：/range?drill=<id> 直接开局
  const d = drills.find((x) => x.drill === route.query.drill && x.playable)
  if (d) openDrill(d)
})
</script>

<style scoped>
.range__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: var(--sp-4);
}
.range__title {
  margin: 0;
  font-size: var(--fs-h1);
  letter-spacing: 0.04em;
}
.range__subtitle { margin: var(--sp-1) 0 0; font-size: var(--fs-caption); letter-spacing: 0.08em; }
.range__error { color: var(--c-loss); margin: 0 0 var(--sp-3); }

.range__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--sp-4);
}

.range__card--locked { opacity: 0.65; }
.range__card-body { display: flex; flex-direction: column; gap: var(--sp-1); }
.range__card-en {
  margin: 0;
  color: var(--c-accent);
  font-size: var(--fs-micro);
  letter-spacing: 0.28em;
}
.range__card-desc { margin: 0 0 var(--sp-3); min-height: 66px; }

.range__card-stats {
  display: flex;
  gap: var(--sp-5);
  border-top: 1px solid var(--c-border);
  padding-top: var(--sp-3);
}
.range__stat { display: flex; flex-direction: column; line-height: 1.3; }
.range__stat-label { font-size: var(--fs-micro); letter-spacing: 0.12em; }
.range__stat-value { font-size: var(--fs-data); font-weight: 700; }
.range__spark { margin: var(--sp-2) 0 var(--sp-2); }

.range__card-foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  border-top: 1px solid var(--c-border);
  padding-top: var(--sp-3);
}
</style>
