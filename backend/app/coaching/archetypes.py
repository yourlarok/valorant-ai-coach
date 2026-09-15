from pydantic import BaseModel

from app.analysis.metrics import DimensionRaws


class Archetype(BaseModel):
    key: str
    title: str
    roast_hint: str  # 给 LLM 生成锐评的提示


ARCHETYPES: list[Archetype] = [
    Archetype(key="headshot_machine", title="爆头机器",
              roast_hint="夸他的爆头率，顺便阴阳一句是不是开了"),
    Archetype(key="suicide_squad", title="开局敢死队",
              roast_hint="首杀和首死一样多，每局第一个躺的总是他"),
    Archetype(key="econ_blackhole", title="经济黑洞",
              roast_hint="eco 局全甲大狙，全队的钱包因他而哭泣"),
    Archetype(key="stable_pillar", title="定海神针",
              roast_hint="发挥稳定得像机器人，从不超神也从不超鬼"),
    Archetype(key="clutch_god", title="残局之神",
              roast_hint="队友死光了他才开始认真玩"),
    Archetype(key="utility_bot", title="人形闪光弹",
              roast_hint="技能扔得比谁都勤，白的经常是队友"),
    Archetype(key="balanced_default", title="六边形战士（毛坯版）",
              roast_hint="哪都会一点，哪都不突出，典型的潜力股"),
]

_HS_ELITE = 0.35
_ECON_OVERSPEND = 2400.0
_STABLE_CV = 0.10
_CLUTCH_HIGH = 0.30
_UTILITY_HIGH = 2.5


def match_archetypes(raws: DimensionRaws) -> tuple[Archetype, list[Archetype]]:
    by_key = {a.key: a for a in ARCHETYPES}
    subs: list[Archetype] = []

    if raws.economy_spend_per_round >= _ECON_OVERSPEND:
        subs.append(by_key["econ_blackhole"])
    if raws.consistency_acs_cv <= _STABLE_CV:
        subs.append(by_key["stable_pillar"])
    if raws.utility_casts_per_round >= _UTILITY_HIGH:
        subs.append(by_key["utility_bot"])

    if raws.aim_hs_rate >= _HS_ELITE:
        primary = by_key["headshot_machine"]
    elif raws.awareness_clutch_proxy >= _CLUTCH_HIGH:
        primary = by_key["clutch_god"]
    elif raws.duel_first_blood_diff <= 0 and raws.duel_first_duel_winrate <= 0.45:
        primary = by_key["suicide_squad"]
    else:
        primary = by_key["balanced_default"]

    subs = [a for a in subs if a.key != primary.key]
    return primary, subs
