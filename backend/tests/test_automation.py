import asyncio

import pytest
from fastapi.testclient import TestClient

from app.automation import process_new_matches
from app.main import create_app
from app.notifications import create_notification

PLAYER = "测试玩家#1234"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("COLLECTOR", "fixture")
    monkeypatch.setenv("DB_PATH_OVERRIDE", str(tmp_path / "test.db"))
    # 避免测试改写真实的 backend/config.json
    monkeypatch.setattr("app.config.CONFIG_PATH", tmp_path / "config.json")
    return TestClient(create_app())


# ---- 通知 CRUD ----

def test_notification_crud(client):
    n = create_notification("analysis_done", "深度复盘完成",
                            "莲华古城 13:9", "/report/fixture-match-001")
    assert n.id >= 1

    resp = client.get("/api/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert data["unread"] == 1
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["id"] == n.id
    assert item["type"] == "analysis_done"
    assert item["title"] == "深度复盘完成"
    assert item["body"] == "莲华古城 13:9"
    assert item["link"] == "/report/fixture-match-001"
    assert item["read"] is False
    assert item["created_at"]

    resp = client.post(f"/api/notifications/{n.id}/read")
    assert resp.status_code == 200
    data = client.get("/api/notifications").json()
    assert data["unread"] == 0
    assert data["items"][0]["read"] is True

    # unread_only 过滤
    assert client.get("/api/notifications",
                      params={"unread_only": True}).json()["items"] == []

    # read-all 一键清空未读
    create_notification("retest_reminder", "复测提醒", "该复测了", "/plan")
    create_notification("retest_reminder", "复测提醒", "又该复测了", "/plan")
    assert client.get("/api/notifications").json()["unread"] == 2
    resp = client.post("/api/notifications/read-all")
    assert resp.status_code == 200
    assert client.get("/api/notifications").json()["unread"] == 0

    # 不存在的通知
    assert client.post("/api/notifications/9999/read").status_code == 404


# ---- 玩家档案聚合（基于 5 场 fixture 的已知值）----

def test_profile_aggregation(client):
    resp = client.get("/api/profile", params={"name": PLAYER})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == PLAYER
    # 对局数据中没有段位信息，档案表无记录时为 None
    assert data["rank_tier"] is None
    assert data["rr"] is None
    # 捷风出场 2 次，其余英雄各 1 次
    assert data["main_agents"][0] == "捷风"
    assert len(data["main_agents"]) == 3
    recent = data["recent"]
    assert recent["games"] == 5
    assert recent["wins"] == 3  # 001/002/004 胜
    assert recent["avg_acs"] == pytest.approx((245 + 312 + 188 + 225 + 98) / 5)
    # 汇总口径爆头率：29 / 86 次命中
    assert recent["avg_hs"] == pytest.approx(29 / 86, abs=1e-3)


def test_profile_unknown_player(client):
    resp = client.get("/api/profile", params={"name": "不存在#9999"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["recent"]["games"] == 0
    assert data["main_agents"] == []


# ---- 自动化链路：发现新对局 → 深度分析 → 写通知 ----

def test_automation_chain_via_simulate(client):
    # 基线：直接同步调用核心函数，处理已有 5 场
    baseline = process_new_matches(client.app, PLAYER)
    assert len(baseline) == 5
    assert all(n.type == "analysis_done" for n in baseline)

    # dev 端点模拟一场新对局到达，走同一条自动化链路
    resp = client.post("/api/dev/simulate-new-match", params={"name": PLAYER})
    assert resp.status_code == 200
    data = resp.json()
    sim_id = data["match_id"]
    assert sim_id != "fixture-match-001"
    assert len(data["notifications"]) == 1
    note = data["notifications"][0]
    assert note["type"] == "analysis_done"
    assert note["link"] == f"/report/{sim_id}"

    # 通知已持久化，未读数随之增长
    notes = client.get("/api/notifications").json()
    assert notes["unread"] == 6
    assert notes["items"][0]["link"] == f"/report/{sim_id}"

    # 再次轮询不重复处理（match_id 幂等）
    assert process_new_matches(client.app, PLAYER) == []


# ---- 自动化开关（可取消）----

def test_automation_settings_toggle(client):
    resp = client.get("/api/settings/automation")
    assert resp.status_code == 200
    assert resp.json() == {"enabled": True, "poll_interval_min": 5}

    resp = client.put("/api/settings/automation",
                      json={"enabled": False, "poll_interval_min": 10})
    assert resp.status_code == 200
    assert resp.json() == {"enabled": False, "poll_interval_min": 10}
    # 关闭后引擎不持有任何轮询任务（已取消/未启动）
    assert client.app.state.automation._task is None
    assert client.get("/api/settings/automation").json()["enabled"] is False

    # 重新打开：fixture 采集器下不真正轮询
    resp = client.put("/api/settings/automation",
                      json={"enabled": True, "poll_interval_min": 5})
    assert resp.status_code == 200
    assert client.app.state.automation._task is None


def test_engine_start_stop_only_polls_non_fixture(client):
    engine = client.app.state.automation

    async def scenario():
        # fixture 采集器：不启动轮询
        engine.start(client.app)
        assert engine._task is None

        # 非 fixture（如 wegame）采集器：启动并可取消
        client.app.state.collector = object()
        try:
            engine.start(client.app)
            assert engine._task is not None and not engine._task.done()
            engine.stop()
            assert engine._task is None
        finally:
            from app.collector.fixture import FixtureCollector
            from app.config import FIXTURE_DIR
            client.app.state.collector = FixtureCollector(FIXTURE_DIR)

    asyncio.run(scenario())
