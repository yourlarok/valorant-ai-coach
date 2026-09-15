import json

from app.analysis.metrics import DimensionRaws, ExtendedStats
from app.coaching.archetypes import Archetype
from app.coaching.planner import RULE_TABLE, TrainingTask
from app.coaching.rules import Problem
from app.schemas import Match

# 六维中文名，供诊断段落引用
_DIM_NAMES = {"aim": "瞄准", "duel": "对枪", "awareness": "意识",
              "economy": "经济", "utility": "技能", "consistency": "稳定性"}


class MockProvider:
    """无 api_key 时的本地演示通道：实现与 LLMClient 相同的接口，
    所有输出均基于本场真实计算的指标填充数字，呈现完整产品形态。"""

    def __init__(self, match: Match, player_name: str, raws: DimensionRaws,
                 ext: ExtendedStats, primary: Archetype, subs: list[Archetype],
                 problems: list[Problem]):
        self.match = match
        self.player_name = player_name
        self.raws = raws
        self.ext = ext
        self.primary = primary
        self.subs = subs
        self.problems = problems

    def is_configured(self) -> bool:
        return True

    def chat(self, system: str, user: str) -> str:
        if "[stage:overview]" in system:
            return json.dumps(self._overview(), ensure_ascii=False)
        if "[stage:dimensions]" in system:
            return json.dumps(self._dimensions(), ensure_ascii=False)
        if "[stage:moments]" in system:
            return json.dumps(self._moments(), ensure_ascii=False)
        if "[stage:prescription]" in system:
            return json.dumps([t.model_dump() for t in self._prescription()],
                              ensure_ascii=False)
        raise ValueError(f"MockProvider 不认识的 system prompt: {system[:30]}")

    # ---- 内部：各阶段演示输出 ----

    def _player(self):
        return next(p for p in self.match.players if p.name == self.player_name)

    def _won(self) -> bool:
        p = self._player()
        return (self.match.blue_score > self.match.red_score) == (p.team == "blue")

    def _clutch_text(self) -> str:
        if self.ext.clutch_wr is None:
            return "本场没有进入残局样本"
        p = self._player()
        return f"残局 {p.clutch_attempts} 次赢下 {p.clutch_wins} 次（胜率 {self.ext.clutch_wr:.0%}）"

    def _overview(self) -> dict:
        p = self._player()
        m = self.match
        result = "拿下胜利" if self._won() else "遗憾落败"
        para1 = (
            f"这场{m.map}你操刀{p.agent}，最终 {m.blue_score}:{m.red_score} {result}。"
            f"个人数据 {p.kills}/{p.deaths}/{p.assists}、ACS {p.score}，"
            f"ADR {self.ext.adr:.0f}、KAST {self.ext.kast:.0%}。"
        )
        hs = self.raws.aim_hs_rate
        if hs >= 0.25:
            para2 = (
                f"瞄准端是本场最大亮点：{p.kills} 次击杀里 {p.headshots} 次爆头，"
                f"爆头率 {hs:.0%}；首杀参与率 {self.ext.fb_participation:.0%}，"
                f"开局交火参与度不低。"
            )
        else:
            para2 = (
                f"瞄准端拖了后腿：爆头率只有 {hs:.0%}（{p.kills} 次击杀仅 {p.headshots} 次爆头），"
                f"对枪胜率 {self.raws.duel_first_duel_winrate:.0%}，"
                f"首杀 {p.first_bloods} 次却送出 {p.first_deaths} 次首死，开局节奏容易崩。"
            )
        para3 = (
            f"经济面回合均花费 {self.raws.economy_spend_per_round:.0f}，"
            f"技能端回合均释放 {self.raws.utility_casts_per_round:.1f} 次；"
            f"{self._clutch_text()}。系统把你判定为「{self.primary.title}」，"
            + ("基本符合本场观感。" if not self.problems
               else f"但{len(self.problems)} 个维度亮起红灯，优先解决「"
                    f"{_DIM_NAMES[self.problems[0].dimension]}」收益最大。")
        )
        return {"overview": para1 + para2 + para3, "roast": self._roast()}

    def _roast(self) -> str:
        p = self._player()
        hs = self.raws.aim_hs_rate
        if hs >= 0.35:
            return (f"爆头率 {hs:.0%}，对面举报键都快按冒烟了——"
                    f"这枪法不像演的，建议尿检。")
        if (self.raws.duel_first_blood_diff <= 0
                and self.raws.duel_first_duel_winrate <= 0.45):
            return (f"首杀 {p.first_bloods} 次、首死 {p.first_deaths} 次，"
                    f"开局第一个躺的怎么老是你？敢死队队长非你莫属。")
        if self.raws.economy_spend_per_round >= 2400:
            return (f"回合均花费 {self.raws.economy_spend_per_round:.0f}，"
                    f"eco 局也敢全甲起步，全队的钱包因你而哭泣。")
        return (f"ACS {p.score} 的「{self.primary.title}」——"
                f"稳是稳，但潜力股当久了，也该兑现一次了。")

    def _dimensions(self) -> dict:
        p = self._player()
        raws, ext = self.raws, self.ext
        evidence = {pr.dimension: pr.evidence for pr in self.problems}

        def _tail(dim: str) -> str:
            return f"段位基准对照：{evidence[dim]}。" if dim in evidence else "处于段位正常区间。"

        return {
            "aim": (
                f"爆头率 {raws.aim_hs_rate:.0%}（{p.kills} 杀中 {p.headshots} 次爆头），"
                + ("爆头线架得扎实，击杀质量高。" if raws.aim_hs_rate >= 0.25
                   else "泼水偏多、爆头线偏低，击杀质量一般。")
                + _tail("aim")
            ),
            "duel": (
                f"首杀 {p.first_bloods} 次、首死 {p.first_deaths} 次，"
                f"首轮对枪胜率 {raws.duel_first_duel_winrate:.0%}，"
                f"首杀参与率 {ext.fb_participation:.0%}。"
                + ("开局交火能打出优势。" if raws.duel_first_duel_winrate >= 0.5
                   else "开局交火经常吃亏，peek 时机需要打磨。")
                + _tail("duel")
            ),
            "awareness": (
                f"{self._clutch_text()}，多杀高光场次占比 {raws.awareness_clutch_proxy:.0%}。"
                + ("关键局面有存在感。" if raws.awareness_clutch_proxy >= 0.15
                   else "残局与少打多局面贡献不足，信息处理还有提升空间。")
                + _tail("awareness")
            ),
            "economy": (
                f"回合均花费 {raws.economy_spend_per_round:.0f}，手枪局胜率 {ext.pistol_wr:.0%}。"
                + ("买枪节奏合理。" if raws.economy_spend_per_round <= 2200
                   else "存在强行起枪嫌疑，经济管理需要收紧。")
                + _tail("economy")
            ),
            "utility": (
                f"回合均技能释放 {raws.utility_casts_per_round:.1f} 次"
                f"（全场 {sum(p.ability_casts.values())} 次），技能伤害 {p.ability_damage}、"
                f"技能辅助 {p.ability_assists} 次。"
                + ("技能价值兑现得不错。" if raws.utility_casts_per_round >= 1.5
                   else "技能使用率偏低，英雄上限没有打出来。")
                + _tail("utility")
            ),
            "consistency": (
                f"ACS 变异系数 {raws.consistency_acs_cv:.2f}，本场存活 {p.survival_rounds} 回合、"
                f"KAST {ext.kast:.0%}。"
                + ("发挥曲线平稳。" if raws.consistency_acs_cv <= 0.25
                   else "神一场鬼一场，稳定性是当前最大隐患。")
                + _tail("consistency")
            ),
        }

    def _moments(self) -> list[str]:
        p = self._player()
        moments: list[str] = []
        for r in self.match.rounds:
            win = r.winning_team == p.team
            if r.pistol:
                moments.append(
                    f"第 {r.round_num} 回合手枪局{'拿下' if win else '丢掉'}"
                    + (f"，你贡献 {r.player_kills} 杀" if r.player_kills else "")
                    + ("，开局气势打出来了" if win else "，开局经济被迫进入追赶节奏")
                    + "。"
                )
            elif r.player_first_blood:
                moments.append(
                    f"第 {r.round_num} 回合你率先完成首杀"
                    + ("并顺势带队拿分" if win else "但回合最终还是丢了，人数优势没转化成分数")
                    + "。"
                )
            elif r.player_kills >= 3:
                moments.append(
                    f"第 {r.round_num} 回合你单回合 {r.player_kills} 杀"
                    + ("强行carry收下这一分" if win else "仍无力回天，队友这局欠你一句谢谢")
                    + "。"
                )
            elif r.player_first_death:
                moments.append(
                    f"第 {r.round_num} 回合你不幸首死，队伍开局陷入 4v5"
                    + ("，队友硬是擦了屁股" if win else "，这分基本交代了")
                    + "。"
                )
        if self.ext.clutch_wr is not None and p.clutch_attempts:
            moments.append(
                f"残局环节：{p.clutch_attempts} 次少打多赢下 {p.clutch_wins} 次"
                f"（胜率 {self.ext.clutch_wr:.0%}），"
                + ("残局处理是本场的加分项。" if self.ext.clutch_wr >= 0.5
                   else "残局决策还有打磨空间。")
            )
        if not moments:
            moments.append(
                f"本场无回合级明细，整体来看 ACS {p.score}、ADR {self.ext.adr:.0f}，"
                f"关键时刻贡献需要回合数据回传后再细看。"
            )
        return moments[:5]

    def _prescription(self) -> list[TrainingTask]:
        tasks: list[TrainingTask] = []
        for prob in self.problems:
            for t in RULE_TABLE.get(prob.dimension, []):
                tasks.append(TrainingTask(
                    name=t.name, tool=t.tool,
                    detail=f"{t.detail}（本场依据：{prob.evidence}）",
                    freq=t.freq,
                ))
        if not tasks:
            tasks.append(TrainingTask(
                name="保持手感", tool="死斗",
                detail=(f"本场爆头率 {self.raws.aim_hs_rate:.0%}、KAST {self.ext.kast:.0%} "
                        f"都在线，每天 3 局死斗维持当前状态"),
                freq="每天",
            ))
        return tasks[:4]
