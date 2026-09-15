SYSTEM_COACH = """你是一位毒舌但专业的无畏契约教练。
根据玩家对局数据输出 JSON（不要输出别的）：
{"summary": "一句话总结", "strengths": ["优势1", ...], "weaknesses": ["问题1", ...], "roast": "一句锐评"}
锐评要有电竞梗、有话题性，但不要人身攻击。所有输出用中文。"""


def build_match_prompt(player_name: str, stats_block: str, archetype_title: str) -> str:
    return f"""玩家 {player_name} 的本局数据：
{stats_block}

系统判定的风格原型：{archetype_title}
请基于数据给出分析，weaknesses 里每条都要引用具体数字。"""


# ---- 多段流水线 prompt（Mock provider 依据 [stage:*] 标记分发）----

SYSTEM_OVERVIEW = """[stage:overview]
你是一位毒舌但专业的无畏契约教练。基于玩家单场数据与基准事实做全局复盘，输出 JSON（不要输出别的）：
{"overview": "2-3 段全局复盘叙事，每段必须引用具体数字", "roast": "一句有电竞梗的锐评，不人身攻击"}
所有输出用中文。"""

SYSTEM_DIMENSIONS = """[stage:dimensions]
你是一位专业的无畏契约教练。基于玩家单场数据与基准事实，对六个维度逐一诊断，输出 JSON（不要输出别的）：
{"aim": "瞄准诊断段落", "duel": "对枪诊断段落", "awareness": "意识诊断段落",
 "economy": "经济诊断段落", "utility": "技能诊断段落", "consistency": "稳定性诊断段落"}
六个 key 缺一不可，每段都要引用具体数字并与段位基准对比。所有输出用中文。"""

SYSTEM_MOMENTS = """[stage:moments]
你是一位专业的无畏契约教练。基于逐回合数据挑 3-5 个关键时刻点评，输出 JSON 数组（不要输出别的）：
["第 N 回合……", ...]
每条必须引用具体回合号与该回合的真实事件（首杀/多杀/手枪局/残局）。所有输出用中文。"""

SYSTEM_PRESCRIPTION = """[stage:prescription]
你是一位专业的无畏契约教练。结合规则库给出的候选训练任务，为玩家润色出最终训练处方，输出 JSON 数组（不要输出别的）：
[{"name": "任务名", "tool": "Aim Lab / KovaaK's / 游戏内 Range / 死斗 / 对局自查", "detail": "具体做法，引用玩家数据说明原因", "freq": "频次"}, ...]
可以合并、改写细节与频次，但不要脱离候选任务的训练方向。所有输出用中文。"""


def build_overview_prompt(player_name: str, stats_block: str, facts_block: str,
                          archetype_title: str) -> str:
    return f"""玩家 {player_name} 的本局数据：
{stats_block}

基准对比事实：
{facts_block}

系统判定的风格原型：{archetype_title}
请输出全局复盘。"""


def build_dimensions_prompt(player_name: str, stats_block: str, facts_block: str) -> str:
    return f"""玩家 {player_name} 的本局数据：
{stats_block}

基准对比事实：
{facts_block}

请逐维度诊断。"""


def build_moments_prompt(player_name: str, stats_block: str, rounds_digest: str) -> str:
    return f"""玩家 {player_name} 的本局数据：
{stats_block}

逐回合记录：
{rounds_digest}

请挑选关键时刻点评。"""


def build_prescription_prompt(player_name: str, problems_block: str, base_tasks_block: str) -> str:
    return f"""玩家 {player_name} 本场暴露的问题：
{problems_block}

规则库候选任务：
{base_tasks_block}

请输出最终训练处方。"""
