<template>
  <UiCard title="玩家档案" cut>
    <div class="profile">
      <div class="profile__identity">
        <span class="profile__avatar cut-corner">{{ avatarChar }}</span>
        <div class="profile__names">
          <span class="profile__name">{{ playerName || '—' }}</span>
          <span class="profile__sub muted">数据源：本地对局记录</span>
        </div>
      </div>

      <div class="profile__stats">
        <div class="stat">
          <span class="stat__label muted">段位基准</span>
          <span class="stat__value num">{{ rank }}</span>
        </div>
        <div class="stat">
          <span class="stat__label muted">RR</span>
          <span class="stat__value num">{{ rr }}</span>
        </div>
        <div class="stat">
          <span class="stat__label muted">主英雄</span>
          <span class="stat__value">{{ mainAgent }}</span>
        </div>
        <div class="stat">
          <span class="stat__label muted">近 {{ record.total }} 场</span>
          <span class="stat__value num">
            <span class="win">{{ record.wins }}W</span>
            <span class="stat__sep muted">·</span>
            <span class="loss">{{ record.losses }}L</span>
          </span>
        </div>
      </div>

      <div v-if="record.total" class="profile__bar" aria-label="近10场胜负分布">
        <span
          class="profile__bar-win"
          :style="{ width: `${(record.wins / record.total) * 100}%` }"
        />
      </div>
      <div v-if="record.total" class="profile__bar-legend muted">
        <span>胜率 <span class="num win">{{ winRate }}%</span></span>
        <span>{{ record.total }} 场样本</span>
      </div>
    </div>
  </UiCard>
</template>

<script setup>
import { computed } from 'vue'
import { UiCard } from './ui'

const props = defineProps({
  matches: { type: Array, default: () => [] },
  playerName: { type: String, default: '' },
  // 后端暂无档案接口：段位取分析基准段位，RR 暂无数据源
  rank: { type: String, default: '钻石' },
  rr: { type: String, default: '—' },
})

const avatarChar = computed(() => (props.playerName || '?').trim().charAt(0).toUpperCase())

const mainAgent = computed(() => {
  const counts = new Map()
  for (const m of props.matches) {
    const me = m.players?.find((p) => p.name === props.playerName)
    if (me?.agent) counts.set(me.agent, (counts.get(me.agent) || 0) + 1)
  }
  let best = null
  for (const [agent, n] of counts) {
    if (!best || n > best.n) best = { agent, n }
  }
  return best ? best.agent : '—'
})

const record = computed(() => {
  let wins = 0
  let losses = 0
  for (const m of props.matches) {
    const me = m.players?.find((p) => p.name === props.playerName)
    if (!me) continue
    const myScore = me.team === 'blue' ? m.blue_score : m.red_score
    const oppScore = me.team === 'blue' ? m.red_score : m.blue_score
    if (myScore > oppScore) wins += 1
    else if (myScore < oppScore) losses += 1
  }
  return { wins, losses, total: wins + losses }
})

const winRate = computed(() =>
  record.value.total ? Math.round((record.value.wins / record.value.total) * 100) : 0
)
</script>

<style scoped>
.profile { display: flex; flex-direction: column; gap: var(--sp-4); }
.profile__identity { display: flex; align-items: center; gap: var(--sp-3); }
.profile__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: var(--c-accent);
  color: var(--c-on-accent);
  font-family: var(--font-num);
  font-size: var(--fs-h2);
  font-weight: 800;
}
.profile__names { display: flex; flex-direction: column; line-height: 1.35; }
.profile__name { font-size: var(--fs-h3); font-weight: 700; word-break: break-all; }
.profile__sub { font-size: var(--fs-caption); }

.profile__stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--sp-3);
}
.stat {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  background: var(--c-surface-1);
  border: 1px solid var(--c-border);
  border-radius: var(--r-sm);
  padding: var(--sp-2) var(--sp-3);
}
.stat__label { font-size: var(--fs-caption); letter-spacing: 0.06em; }
.stat__value { font-size: var(--fs-h3); font-weight: 700; }
.stat__sep { margin: 0 var(--sp-1); }
.win { color: var(--c-win); }
.loss { color: var(--c-loss); }

.profile__bar {
  height: 6px;
  border-radius: var(--r-sm);
  background: var(--c-loss-dim);
  overflow: hidden;
}
.profile__bar-win { display: block; height: 100%; background: var(--c-win); }
.profile__bar-legend {
  display: flex;
  justify-content: space-between;
  font-size: var(--fs-caption);
  margin-top: calc(-1 * var(--sp-2));
}
</style>
