import httpx
import pytest
from fastapi.testclient import TestClient

from app.analysis.llm import LLMClient
from app.main import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("COLLECTOR", "fixture")
    monkeypatch.setenv("DB_PATH_OVERRIDE", str(tmp_path / "test.db"))
    # 避免在导出过该环境变量的机器上测试真打 DeepSeek API
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    app = create_app()
    return TestClient(app)


def test_list_matches(client):
    resp = client.get("/api/matches", params={"name": "测试玩家#1234"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["match_id"] == "fixture-match-001"


def test_analyze_match(client):
    resp = client.get("/api/analysis/fixture-match-001",
                      params={"name": "测试玩家#1234"})
    assert resp.status_code == 200
    data = resp.json()
    assert 0 <= data["scores"]["overall"] <= 100
    assert data["primary"]["title"]
    assert data["analysis"]["summary"]
    assert isinstance(data["problems"], list)


def test_plan_and_checkin(client):
    # 先分析一场，产生问题点，再取计划
    client.get("/api/analysis/fixture-match-001", params={"name": "测试玩家#1234"})
    resp = client.get("/api/plan", params={"name": "测试玩家#1234"})
    assert resp.status_code == 200
    tasks = resp.json()["tasks"]
    assert isinstance(tasks, list)

    if tasks:
        toggle = client.post("/api/plan/toggle",
                             json={"task_name": tasks[0]["name"], "done": True},
                             params={"name": "测试玩家#1234"})
        assert toggle.status_code == 200
        tasks2 = client.get("/api/plan", params={"name": "测试玩家#1234"}).json()["tasks"]
        assert any(t["name"] == tasks[0]["name"] and t["done"] for t in tasks2)


def test_unknown_player_404(client):
    resp = client.get("/api/matches", params={"name": "不存在#9999"})
    assert resp.status_code == 200
    assert resp.json() == []


class _FailingLLMClient(LLMClient):
    def is_configured(self) -> bool:
        return True

    def chat(self, system: str, user: str) -> str:
        raise httpx.ConnectError("模拟 LLM 服务不可达")


def test_analyze_degrades_on_llm_http_error(client):
    client.app.state.llm = _FailingLLMClient("http://127.0.0.1:1", "fake-key", "fake-model")
    resp = client.get("/api/analysis/fixture-match-001",
                      params={"name": "测试玩家#1234"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["analysis"]["summary"]
