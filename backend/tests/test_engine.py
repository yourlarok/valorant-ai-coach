import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.analysis import prompts
from app.analysis.baselines import load_baseline
from app.analysis.engine import DIMENSION_KEYS, DeepAnalysis, analyze_deep
from app.analysis.llm import LLMClient
from app.analysis.metrics import compute_raws, extended_stats
from app.analysis.mock_provider import MockProvider
from app.coaching.archetypes import match_archetypes
from app.coaching.planner import TrainingTask, build_plan
from app.coaching.rules import detect_problems
from app.main import create_app
from app.schemas import Match

FIXTURE_DIR = Path(__file__).parent / "fixtures"
PLAYER = "测试玩家#1234"


def _context():
    raw = json.loads((FIXTURE_DIR / "match_sample.json").read_text(encoding="utf-8"))
    match = Match.model_validate(raw)
    raws = compute_raws([match], PLAYER)
    ext = extended_stats([match], PLAYER)
    primary, subs = match_archetypes(raws)
    problems = detect_problems(raws, load_baseline("钻石"))
    return match, raws, ext, primary, subs, problems


def _mock() -> MockProvider:
    match, raws, ext, primary, subs, problems = _context()
    return MockProvider(match=match, player_name=PLAYER, raws=raws, ext=ext,
                        primary=primary, subs=subs, problems=problems)


def test_mock_provider_is_always_configured():
    assert _mock().is_configured() is True


def test_mock_provider_stage_outputs_validate():
    mock = _mock()
    match, raws, ext, primary, subs, problems = _context()

    overview = json.loads(mock.chat(prompts.SYSTEM_OVERVIEW, "user"))
    assert isinstance(overview["overview"], str) and overview["overview"]
    assert isinstance(overview["roast"], str) and overview["roast"]

    dims = json.loads(mock.chat(prompts.SYSTEM_DIMENSIONS, "user"))
    assert set(dims.keys()) == set(DIMENSION_KEYS)
    assert all(isinstance(v, str) and v for v in dims.values())

    moments = json.loads(mock.chat(prompts.SYSTEM_MOMENTS, "user"))
    assert isinstance(moments, list) and moments
    assert all(isinstance(m, str) for m in moments)

    base_tasks = build_plan(problems)
    user = prompts.build_prescription_prompt(PLAYER, "问题清单", json.dumps(
        [t.model_dump() for t in base_tasks], ensure_ascii=False))
    prescription = json.loads(mock.chat(prompts.SYSTEM_PRESCRIPTION, user))
    tasks = [TrainingTask.model_validate(t) for t in prescription]
    assert tasks, "Mock 处方不应为空"

    # mock 文案必须基于真实指标填充数字，而不是空模板
    assert f"{ext.adr:.0f}" in overview["overview"]


def test_analyze_deep_with_mock_provider_full_structure():
    match, raws, ext, primary, subs, problems = _context()
    deep = analyze_deep(match, PLAYER, raws, ext, primary, subs, problems, _mock())
    assert isinstance(deep, DeepAnalysis)
    assert deep.mock is True
    assert set(deep.dimensions.keys()) == set(DIMENSION_KEYS)
    assert all(isinstance(t, TrainingTask) for t in deep.prescription)
    assert deep.overview and deep.roast and deep.moments


class _GarbageLLM(LLMClient):
    def __init__(self):
        self.calls = 0

    def is_configured(self) -> bool:
        return True

    def chat(self, system: str, user: str) -> str:
        self.calls += 1
        return "这不是合法 JSON，{[损坏"


def test_analyze_deep_retries_once_then_falls_back_to_mock():
    match, raws, ext, primary, subs, problems = _context()
    bad = _GarbageLLM()
    deep = analyze_deep(match, PLAYER, raws, ext, primary, subs, problems, bad)
    assert isinstance(deep, DeepAnalysis)
    assert deep.mock is True
    assert set(deep.dimensions.keys()) == set(DIMENSION_KEYS)
    # 四个阶段各调用 2 次（首次 + 重试一次）后回退 mock
    assert bad.calls == 8


class _ScriptedLLM(LLMClient):
    """按 system prompt 阶段返回合法 JSON 的假 LLM。"""

    def __init__(self):
        self.calls = 0

    def is_configured(self) -> bool:
        return True

    def chat(self, system: str, user: str) -> str:
        self.calls += 1
        if "[stage:overview]" in system:
            return json.dumps({"overview": "真实LLM总评", "roast": "真实LLM锐评"}, ensure_ascii=False)
        if "[stage:dimensions]" in system:
            return json.dumps({k: f"{k} 诊断" for k in DIMENSION_KEYS}, ensure_ascii=False)
        if "[stage:moments]" in system:
            return json.dumps(["第 1 回合点评"], ensure_ascii=False)
        return json.dumps([{"name": "真实LLM任务", "tool": "死斗",
                            "detail": "细节", "freq": "每天"}], ensure_ascii=False)


def test_analyze_deep_uses_llm_output_when_valid():
    match, raws, ext, primary, subs, problems = _context()
    fake = _ScriptedLLM()
    deep = analyze_deep(match, PLAYER, raws, ext, primary, subs, problems, fake)
    assert deep.mock is False
    assert fake.calls == 4, "合法输出不应触发重试"
    assert deep.overview == "真实LLM总评"
    assert deep.roast == "真实LLM锐评"
    assert deep.prescription[0].name == "真实LLM任务"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("COLLECTOR", "fixture")
    monkeypatch.setenv("DB_PATH_OVERRIDE", str(tmp_path / "test.db"))
    app = create_app()
    return TestClient(app)


def test_analysis_endpoint_includes_deep_ext_mock(client):
    resp = client.get("/api/analysis/fixture-match-001", params={"name": PLAYER})
    assert resp.status_code == 200
    data = resp.json()
    # 原字段保留
    assert 0 <= data["scores"]["overall"] <= 100
    assert data["analysis"]["summary"]
    assert isinstance(data["problems"], list)
    # 新增字段
    assert set(data["deep"]["dimensions"].keys()) == set(DIMENSION_KEYS)
    assert data["deep"]["overview"] and data["deep"]["roast"]
    assert data["ext"]["adr"] > 0
    assert data["mock"] is True  # 未配置 api_key，应走 Mock 通道


def test_weekly_endpoint_aggregates_fixtures(client):
    resp = client.get("/api/analysis/weekly", params={"name": PLAYER})
    assert resp.status_code == 200
    data = resp.json()
    assert data["games"] == 5
    assert data["narrative"]
    assert isinstance(data["improved"], list)
    assert isinstance(data["regressed"], list)


def test_weekly_endpoint_unknown_player(client):
    resp = client.get("/api/analysis/weekly", params={"name": "不存在#9999"})
    assert resp.status_code == 200
    assert resp.json()["games"] == 0


def test_settings_llm_get_never_echoes_key(client):
    resp = client.get("/api/settings/llm")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == {"base_url", "model", "configured"}
    assert data["configured"] is False


def test_settings_llm_put_persists_and_hot_updates(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.CONFIG_PATH", tmp_path / "config.json")
    resp = client.put("/api/settings/llm", json={
        "base_url": "https://example.com/v1",
        "api_key": "sk-test-secret",
        "model": "test-model",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    assert "api_key" not in data
    assert "sk-test-secret" not in resp.text
    # 热更新：app.state.llm 立即生效，无需重启
    assert client.app.state.llm.api_key == "sk-test-secret"
    assert client.app.state.llm.model == "test-model"
    # 写回 config.json
    saved = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert saved["llm"]["api_key"] == "sk-test-secret"
    # GET 仍然不回显 key
    again = client.get("/api/settings/llm").json()
    assert again["configured"] is True
    assert "sk-test-secret" not in json.dumps(again)
