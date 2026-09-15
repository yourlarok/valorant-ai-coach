import json
from pathlib import Path

from app.analysis.analyzer import analyze_match
from app.analysis.llm import LLMClient
from app.analysis.metrics import compute_raws
from app.coaching.archetypes import match_archetypes
from app.schemas import Match


class FakeLLM(LLMClient):
    def __init__(self, response: str):
        self._response = response
        self.calls: list[tuple[str, str]] = []

    def is_configured(self) -> bool:
        return True

    def chat(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self._response


def _context():
    raw = json.loads(
        (Path(__file__).parent / "fixtures" / "match_sample.json").read_text(encoding="utf-8")
    )
    match = Match.model_validate(raw)
    raws = compute_raws([match], "测试玩家#1234")
    primary, subs = match_archetypes(raws)
    return match, raws, primary, subs


def test_analyze_with_llm_parses_json():
    match, raws, primary, subs = _context()
    fake = FakeLLM(json.dumps({
        "summary": "全场carry但中期送了两波",
        "strengths": ["爆头效率高", "首杀积极"],
        "weaknesses": ["中期走位激进"],
        "roast": "你这爆头率，对面以为你在开锁头",
    }, ensure_ascii=False))
    result = analyze_match(match, "测试玩家#1234", raws, primary, subs, fake)
    assert result.summary == "全场carry但中期送了两波"
    assert len(result.strengths) == 2
    assert result.roast
    assert fake.calls, "LLM 应被调用"


def test_analyze_without_llm_degrades():
    match, raws, primary, subs = _context()
    result = analyze_match(match, "测试玩家#1234", raws, primary, subs, None)
    assert "测试玩家#1234" in result.summary
    assert result.strengths or result.weaknesses
    assert primary.title in result.roast


def test_llm_client_unconfigured():
    client = LLMClient(base_url="https://api.openai.com/v1", api_key="", model="gpt-4o-mini")
    assert client.is_configured() is False
