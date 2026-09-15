<template>
  <div class="round-timeline">
    <div class="round-timeline__track">
      <div
        v-for="r in cells"
        :key="r.round_num"
        class="round-cell"
        :class="[`round-cell--${r.outcome}`, { 'round-cell--pistol': r.pistol }]"
        :title="`第 ${r.round_num} 回合 · ${r.outcomeText} · ${r.endLabel}`"
      >
        <span class="round-cell__num num">{{ r.round_num }}</span>
        <span class="round-cell__kills num">{{ r.player_kills }}杀</span>
        <span class="round-cell__marks">
          <i v-if="r.player_first_blood" class="mark mark--fb" title="目标玩家首杀" />
          <i v-if="r.player_first_death" class="mark mark--fd" title="目标玩家首死" />
        </span>
      </div>
    </div>

    <div class="round-timeline__legend">
      <span class="legend-item"><i class="swatch swatch--win" />胜场回合</span>
      <span class="legend-item"><i class="swatch swatch--loss" />负场回合</span>
      <span class="legend-item"><i class="mark mark--fb" />目标玩家首杀</span>
      <span class="legend-item"><i class="mark mark--fd" />目标玩家首死</span>
      <span class="legend-item"><i class="swatch swatch--pistol" />手枪局</span>
    </div>

    <ul class="round-timeline__detail">
      <li v-for="r in cells" :key="`d-${r.round_num}`" class="round-row">
        <span class="round-row__num num">R{{ r.round_num }}</span>
        <UiTag :tone="r.outcome === 'win' ? 'win' : 'loss'">{{ r.outcomeText }}</UiTag>
        <UiTag v-if="r.pistol" tone="firstblood" dot>手枪局</UiTag>
        <span class="round-row__end muted">{{ r.endLabel }}</span>
        <span class="round-row__kills num">击杀 {{ r.player_kills }}</span>
        <span v-if="r.player_first_blood" class="round-row__fb">首杀</span>
        <span v-if="r.player_first_death" class="round-row__fd">首死</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { UiTag } from './ui'

const props = defineProps({
  rounds: { type: Array, default: () => [] },
  myTeam: { type: String, default: '' },
})

const END_TYPE_LABELS = {
  elimination: '歼灭',
  defuse: '拆弹成功',
  detonate: '爆能器引爆',
  time: '时间耗尽',
}

const cells = computed(() =>
  (props.rounds || []).map((r) => {
    const win = r.winning_team === props.myTeam
    return {
      ...r,
      outcome: win ? 'win' : 'loss',
      outcomeText: win ? '胜' : '负',
      endLabel: END_TYPE_LABELS[r.end_type] || r.end_type || '未知',
    }
  })
)
</script>

<style scoped>
.round-timeline__track {
  display: flex;
  gap: var(--sp-1);
  overflow-x: auto;
  padding-bottom: var(--sp-1);
}
.round-cell {
  flex: 1 0 44px;
  min-width: 44px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: var(--sp-1) var(--sp-1) var(--sp-2);
  border-radius: var(--r-sm);
  border-top: 3px solid transparent;
  background: var(--c-surface-1);
}
.round-cell--win { border-top-color: var(--c-win); background: var(--c-win-dim); }
.round-cell--loss { border-top-color: var(--c-loss); background: var(--c-loss-dim); }
.round-cell--pistol { box-shadow: inset 0 0 0 1px var(--c-firstblood); }
.round-cell__num {
  font-size: var(--fs-caption);
  font-weight: 700;
  color: var(--c-text);
}
.round-cell__kills {
  font-size: var(--fs-micro);
  color: var(--c-text-muted);
}
.round-cell__marks { display: flex; gap: 3px; min-height: 8px; }
.mark {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.mark--fb { background: var(--c-firstblood); }
.mark--fd { background: var(--c-loss); border: 1px solid var(--c-text); }

.round-timeline__legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  margin: var(--sp-3) 0;
  font-size: var(--fs-caption);
  color: var(--c-text-muted);
}
.legend-item { display: inline-flex; align-items: center; gap: var(--sp-1); }
.swatch {
  width: 10px;
  height: 10px;
  border-radius: var(--r-sm);
  display: inline-block;
}
.swatch--win { background: var(--c-win); }
.swatch--loss { background: var(--c-loss); }
.swatch--pistol { background: transparent; border: 1px solid var(--c-firstblood); }

.round-timeline__detail {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}
.round-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-2);
  border-bottom: 1px solid var(--c-border);
  font-size: var(--fs-body);
}
.round-row:last-child { border-bottom: 0; }
.round-row__num {
  width: 36px;
  flex-shrink: 0;
  font-weight: 700;
  color: var(--c-text-muted);
}
.round-row__end { min-width: 72px; }
.round-row__kills { color: var(--c-text); }
.round-row__fb { color: var(--c-firstblood); font-weight: 700; font-size: var(--fs-caption); }
.round-row__fd { color: var(--c-loss); font-weight: 700; font-size: var(--fs-caption); }
</style>
