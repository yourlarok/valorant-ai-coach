<template>
  <div class="range">
    <!-- 科目进行视图 -->
    <DrillShell
      v-if="activeDrill"
      :drill="activeDrill.drill"
      :title="activeDrill.title"
      :duration="activeDrill.duration"
      @finish="onFinish"
      @exit="closeDrill"
    >
      <template #default="slotProps">
        <HeadlineFlick
          v-if="activeDrill.drill === 'headline_flick'"
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
            <div class="range__card-foot">
              <div class="range__best">
                <span class="range__best-label muted">历史最佳</span>
                <span class="range__best-value num" :class="{ accent: bests[d.drill] != null }">
                  {{ bests[d.drill] != null ? bests[d.drill].toFixed(1) : '—' }}
                </span>
              </div>
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
import { getTrainingScores } from '../api'
import { playerName } from '../player'
import DrillShell from '../components/range/DrillShell.vue'
import HeadlineFlick from '../components/range/HeadlineFlick.vue'
import { UiButton, UiCard, UiTag } from '../components/ui'

const drills = [
  {
    drill: 'headline_flick',
    title: '爆头线定位',
    en: 'HEADLINE FLICK',
    desc: '目标只会出现在爆头线高度带内。快速甩枪定位并点击命中，命中即刻刷新下一个。60 秒，得分 = 命中数 × 命中率。',
    duration: 60,
    playable: true,
  },
  {
    drill: 'reaction',
    title: '反应速度',
    en: 'REACTION',
    desc: '画面变色或目标出现的瞬间尽快点击，测毫秒级反应。对应「对枪」维度。',
    duration: 30,
    playable: false,
  },
  {
    drill: 'tracking',
    title: '跟枪追踪',
    en: 'TRACKING',
    desc: '目标平滑变速移动，准星持续压住目标累计命中时间占比。对应「瞄准 / 稳定」维度。',
    duration: 45,
    playable: false,
  },
]

const activeDrill = ref(null)
const bests = ref({})
const loadError = ref('')

async function loadBests() {
  if (!playerName.value) return
  try {
    const data = await getTrainingScores(playerName.value)
    bests.value = data.bests || {}
    loadError.value = ''
  } catch (e) {
    loadError.value = e.message || '获取历史成绩失败'
  }
}

function openDrill(d) {
  activeDrill.value = d
}

function onFinish() {
  loadBests()
}

function closeDrill() {
  activeDrill.value = null
  loadBests()
}

onMounted(loadBests)
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
.range__card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid var(--c-border);
  padding-top: var(--sp-3);
}
.range__best { display: flex; flex-direction: column; line-height: 1.3; }
.range__best-label { font-size: var(--fs-micro); letter-spacing: 0.12em; }
.range__best-value { font-size: var(--fs-data); font-weight: 700; }
</style>
