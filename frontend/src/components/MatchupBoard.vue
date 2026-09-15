<template>
  <div class="matchup-board">
    <UiCard title="全场记分板" flush>
      <div class="matchup-board__teams">
        <section v-for="side in sides" :key="side.key" class="team-block">
          <header class="team-block__head">
            <UiTag :tone="side.key === 'ally' ? 'win' : 'loss'" dot>{{ side.title }}</UiTag>
            <span class="team-block__score num">{{ side.score }}</span>
          </header>
          <UiTable
            :columns="columns"
            :rows="side.rows"
            row-key="puuid"
            empty-text="该队暂无玩家数据"
          >
            <template #cell-name="{ row }">
              <span class="p-name" :class="{ 'p-name--me': row.isMe }">
                {{ row.name }}
                <UiTag v-if="row.isMe" tone="accent">我</UiTag>
              </span>
            </template>
            <template #cell-firstBloods="{ row }">
              <span class="num">{{ row.firstBloods }}</span>
              <span v-if="row.firstBloods >= 3" class="fb-hot"> ●</span>
            </template>
          </UiTable>
        </section>
      </div>
    </UiCard>

    <UiCard title="同英雄对位">
      <UiEmpty
        v-if="!matchups.length"
        title="本场没有同英雄对位"
        description="双方阵容没有重复英雄，无法生成镜像对位对比。"
      />
      <div v-else class="matchups">
        <div v-for="mu in matchups" :key="mu.agent" class="matchup cut-corner-tr">
          <header class="matchup__head">
            <span class="matchup__agent">{{ mu.agent }}</span>
            <UiTag :tone="mu.verdictTone">{{ mu.verdict }}</UiTag>
          </header>
          <div class="matchup__sides">
            <div class="matchup__side" :class="{ 'matchup__side--lead': mu.allyLead }">
              <span class="matchup__label muted">我方 · {{ mu.ally.name }}</span>
              <span class="matchup__acs num">{{ mu.ally.acs }}</span>
              <span class="matchup__sub muted num">
                KDA {{ mu.ally.kda }} · HS {{ mu.ally.hsRate }} · ADR {{ mu.ally.adr }}
              </span>
            </div>
            <span class="matchup__vs muted">VS</span>
            <div class="matchup__side" :class="{ 'matchup__side--lead': !mu.allyLead }">
              <span class="matchup__label muted">敌方 · {{ mu.enemy.name }}</span>
              <span class="matchup__acs num">{{ mu.enemy.acs }}</span>
              <span class="matchup__sub muted num">
                KDA {{ mu.enemy.kda }} · HS {{ mu.enemy.hsRate }} · ADR {{ mu.enemy.adr }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </UiCard>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { UiCard, UiEmpty, UiTable, UiTag } from './ui'

const props = defineProps({
  match: { type: Object, required: true },
  playerName: { type: String, default: '' },
})

const columns = [
  { key: 'name', label: '玩家', width: '28%' },
  { key: 'agent', label: '英雄' },
  { key: 'kda', label: 'K / D / A', numeric: true },
  { key: 'acs', label: 'ACS', numeric: true },
  { key: 'hsRate', label: 'HS%', numeric: true },
  { key: 'adr', label: 'ADR', numeric: true },
  { key: 'firstBloods', label: '首杀', numeric: true },
]

const roundCount = computed(() => {
  const n = props.match?.rounds?.length
  if (n) return n
  return (props.match?.blue_score ?? 0) + (props.match?.red_score ?? 0) || 1
})

function toRow(p) {
  const shots = (p.headshots ?? 0) + (p.bodyshots ?? 0) + (p.legshots ?? 0)
  const hsRate = shots ? Math.round((p.headshots / shots) * 100) : 0
  return {
    ...p,
    isMe: p.name === props.playerName,
    kda: `${p.kills} / ${p.deaths} / ${p.assists}`,
    acs: p.score,
    hsRate: `${hsRate}%`,
    hsRateNum: hsRate,
    adr: Math.round((p.damage_made ?? 0) / roundCount.value),
    firstBloods: p.first_bloods ?? 0,
  }
}

const me = computed(
  () => props.match?.players?.find((p) => p.name === props.playerName) || null
)
const myTeam = computed(() => me.value?.team || 'blue')

const sides = computed(() => {
  const players = props.match?.players || []
  const build = (team, title, score) => ({
    key: team === myTeam.value ? 'ally' : 'enemy',
    title,
    score,
    rows: players
      .filter((p) => p.team === team)
      .map(toRow)
      .sort((a, b) => b.acs - a.acs),
  })
  const allyTeam = myTeam.value
  const enemyTeam = allyTeam === 'blue' ? 'red' : 'blue'
  const scoreOf = (t) => (t === 'blue' ? props.match.blue_score : props.match.red_score)
  return [
    build(allyTeam, '我方', scoreOf(allyTeam)),
    build(enemyTeam, '敌方', scoreOf(enemyTeam)),
  ]
})

const matchups = computed(() => {
  const players = props.match?.players || []
  const byAgentTeam = new Map()
  for (const p of players) {
    byAgentTeam.set(`${p.agent}|${p.team}`, p)
  }
  const agents = [...new Set(players.map((p) => p.agent))]
  const allyTeam = myTeam.value
  const enemyTeam = allyTeam === 'blue' ? 'red' : 'blue'
  const list = []
  for (const agent of agents) {
    const ally = byAgentTeam.get(`${agent}|${allyTeam}`)
    const enemy = byAgentTeam.get(`${agent}|${enemyTeam}`)
    if (!ally || !enemy) continue
    const a = toRow(ally)
    const e = toRow(enemy)
    const diff = a.acs - e.acs
    list.push({
      agent,
      ally: a,
      enemy: e,
      allyLead: diff >= 0,
      verdict: diff >= 30 ? '我方优势' : diff <= -30 ? '敌方优势' : '均势',
      verdictTone: diff >= 30 ? 'win' : diff <= -30 ? 'loss' : 'draw',
    })
  }
  return list.sort((x, y) => (y.ally.acs - y.enemy.acs) - (x.ally.acs - x.enemy.acs))
})
</script>

<style scoped>
.matchup-board {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}
.matchup-board__teams {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  padding: var(--sp-4);
}
.team-block__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--sp-2);
}
.team-block__score {
  font-size: var(--fs-data);
  font-weight: 800;
  color: var(--c-text);
}
.p-name { display: inline-flex; align-items: center; gap: var(--sp-2); }
.p-name--me { color: var(--c-accent); font-weight: 700; }
.fb-hot { color: var(--c-firstblood); }

.matchups {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--sp-3);
}
.matchup {
  background: var(--c-surface-1);
  border: 1px solid var(--c-border);
  padding: var(--sp-3);
}
.matchup__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--sp-3);
}
.matchup__agent {
  font-size: var(--fs-h3);
  font-weight: 700;
  letter-spacing: 0.04em;
}
.matchup__sides {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: var(--sp-3);
}
.matchup__side {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--r-sm);
  border: 1px solid var(--c-border);
  background: var(--c-surface-2);
}
.matchup__side--lead { border-color: var(--c-win); }
.matchup__label { font-size: var(--fs-caption); }
.matchup__acs {
  font-size: var(--fs-h2);
  font-weight: 800;
  line-height: 1.1;
  color: var(--c-text);
}
.matchup__side--lead .matchup__acs { color: var(--c-win); }
.matchup__sub { font-size: var(--fs-caption); }
.matchup__vs { font-size: var(--fs-caption); font-weight: 700; letter-spacing: 0.1em; }
</style>
