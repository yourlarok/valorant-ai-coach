SYSTEM_COACH = """你是一位毒舌但专业的无畏契约教练。
根据玩家对局数据输出 JSON（不要输出别的）：
{"summary": "一句话总结", "strengths": ["优势1", ...], "weaknesses": ["问题1", ...], "roast": "一句锐评"}
锐评要有电竞梗、有话题性，但不要人身攻击。所有输出用中文。"""


def build_match_prompt(player_name: str, stats_block: str, archetype_title: str) -> str:
    return f"""玩家 {player_name} 的本局数据：
{stats_block}

系统判定的风格原型：{archetype_title}
请基于数据给出分析，weaknesses 里每条都要引用具体数字。"""
