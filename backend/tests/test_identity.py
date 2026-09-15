import pytest
from fastapi.testclient import TestClient

from app.automation import process_new_matches
from app.config import load_settings
from app.db import is_match_analyzed, list_profile_names
from app.main import create_app

PLAYER = "测试玩家#1234"
FIXTURE_MATCH_IDS = [f"fixture-match-{i:03d}" for i in range(1, 6)]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("COLLECTOR", "fixture")
    monkeypatch.setenv("DB_PATH_OVERRIDE", str(tmp_path / "test.db"))
    # 避免在导出过该环境变量的机器上测试真打 DeepSeek API
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    # 避免测试改写真实的 backend/config.json
    monkeypatch.setattr("app.config.CONFIG_PATH", tmp_path / "config.json")
    return TestClient(create_app())


def test_identity_initial_state(client):
    resp = client.get("/api/identity")
    assert resp.status_code == 200
    assert resp.json() == {"name": None, "onboarded": False}


def test_bind_unknown_player_404(client):
    resp = client.post("/api/identity", json={"name": "不存在#9999"})
    assert resp.status_code == 404
    assert "找不到该玩家" in resp.json()["detail"]
    # 绑定失败不写配置，仍未完成引导
    assert client.get("/api/identity").json() == {"name": None, "onboarded": False}


def test_bind_success_persists_and_premarked(client):
    resp = client.post("/api/identity", json={"name": PLAYER})
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "name": PLAYER}

    # 状态持久化到 config.json，重启读取仍在
    assert load_settings().identity.name == PLAYER
    assert client.get("/api/identity").json() == {"name": PLAYER, "onboarded": True}

    # 存量 5 场 fixture 对局全部预标记为已分析，自动化首轮不会轰炸
    for match_id in FIXTURE_MATCH_IDS:
        assert is_match_analyzed(match_id)
    assert process_new_matches(client.app, PLAYER) == []

    # 自动化轮询按档案表玩家名驱动，绑定后档案必须存在
    assert PLAYER in list_profile_names()


def test_rebind_replaces_identity(client):
    assert client.post("/api/identity", json={"name": PLAYER}).status_code == 200
    # 重复绑定同一玩家幂等，不报错、不重复建档
    resp = client.post("/api/identity", json={"name": PLAYER})
    assert resp.status_code == 200
    assert list_profile_names().count(PLAYER) == 1


def test_rebind_removes_old_profile_from_polling(client):
    # fixture 对局中该玩家以队友身份出场，查得到对局，可作为换绑目标
    player_b = "蓝队队友一#2001"
    assert client.post("/api/identity", json={"name": PLAYER}).status_code == 200
    assert PLAYER in list_profile_names()

    assert client.post("/api/identity", json={"name": player_b}).status_code == 200
    # 旧身份档案被移除，自动化轮询（遍历 list_profile_names）只为新身份工作
    assert list_profile_names() == [player_b]
    assert client.get("/api/identity").json() == {"name": player_b, "onboarded": True}
