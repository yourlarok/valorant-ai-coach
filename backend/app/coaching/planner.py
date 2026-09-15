from app.coaching.rules import Problem
from pydantic import BaseModel


class TrainingTask(BaseModel):
    name: str
    tool: str  # Aim Lab / KovaaK's / 游戏内 Range / 死斗 / 对局自查
    detail: str
    freq: str
    done: bool = False


RULE_TABLE: dict[str, list[TrainingTask]] = {
    "aim": [
        TrainingTask(name="Sixshot 精准爆头", tool="Aim Lab",
                     detail="每天 15 分钟 Sixshot，目标分数逐日记录", freq="每天"),
        TrainingTask(name="爆头死斗", tool="死斗",
                     detail="每天 5 局死斗，强制只瞄头线，不泼水", freq="每天"),
    ],
    "duel": [
        TrainingTask(name="预瞄点位练习", tool="游戏内 Range",
                     detail="在常用地图跑图 20 分钟，逐个拐角练预瞄爆头线", freq="每天"),
        TrainingTask(name="死斗抢首发", tool="死斗",
                     detail="死斗中主动找人打，练习 peek 时机与急停", freq="每天 3 局"),
    ],
    "awareness": [
        TrainingTask(name="复盘被击杀回合", tool="对局自查",
                     detail="每局结束后回想 3 次死亡：信息从哪漏的", freq="每局后"),
    ],
    "economy": [
        TrainingTask(name="买枪前自查清单", tool="对局自查",
                     detail="每回合买枪前问自己：这局该 eco 吗？队友经济如何？", freq="每回合"),
    ],
    "utility": [
        TrainingTask(name="技能连招跑图", tool="游戏内 Range",
                     detail="为主玩英雄练 3 套固定技能释放点位", freq="每周 3 次"),
    ],
    "consistency": [
        TrainingTask(name="固定热身流程", tool="Aim Lab",
                     detail="每天开打前固定 10 分钟热身，稳定手感基线", freq="每天开局前"),
    ],
}


def build_plan(problems: list[Problem]) -> list[TrainingTask]:
    plan: list[TrainingTask] = []
    for p in problems:
        plan.extend(RULE_TABLE.get(p.dimension, []))
    return plan
