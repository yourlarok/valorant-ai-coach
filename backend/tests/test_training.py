import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("COLLECTOR", "fixture")
    monkeypatch.setenv("DB_PATH_OVERRIDE", str(tmp_path / "test.db"))
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    return TestClient(create_app())


PLAYER = "测试玩家#1234"


def _post(client, drill, score, extra=None):
    return client.post("/api/training/scores", json={
        "player": PLAYER, "drill": drill, "score": score,
        "extra": extra if extra is not None else {},
    })


def test_post_score_first_is_record(client):
    resp = _post(client, "headline_flick", 75.0)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["is_record"] is True
    assert data["best"] == 75.0


def test_post_score_tracks_record_high_is_better(client):
    _post(client, "headline_flick", 70.0)
    worse = _post(client, "headline_flick", 65.0).json()
    assert worse["is_record"] is False
    assert worse["best"] == 70.0
    better = _post(client, "headline_flick", 80.0).json()
    assert better["is_record"] is True
    assert better["best"] == 80.0


def test_post_score_reaction_low_is_better(client):
    # reaction 科目单位是毫秒，越低越好
    _post(client, "reaction", 250.0)
    worse = _post(client, "reaction", 300.0).json()
    assert worse["is_record"] is False
    assert worse["best"] == 250.0
    better = _post(client, "reaction", 220.0).json()
    assert better["is_record"] is True
    assert better["best"] == 220.0


def test_scores_grouped_by_player_and_drill(client):
    _post(client, "headline_flick", 70.0)
    _post(client, "tracking", 0.42)
    client.post("/api/training/scores", json={
        "player": "其他玩家#0001", "drill": "headline_flick", "score": 99.0,
    })

    resp = client.get("/api/training/scores", params={"player": PLAYER})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["scores"]) == 2
    assert all(s["player"] == PLAYER if "player" in s else True for s in data["scores"])
    assert data["bests"] == {"headline_flick": 70.0, "tracking": 0.42}


def test_scores_filter_by_drill(client):
    _post(client, "headline_flick", 70.0)
    _post(client, "tracking", 0.42, extra={"shots": 30})
    resp = client.get("/api/training/scores",
                      params={"player": PLAYER, "drill": "tracking"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["scores"]) == 1
    row = data["scores"][0]
    assert row["drill"] == "tracking"
    assert row["score"] == 0.42
    assert row["extra"] == {"shots": 30}
    assert row["created_at"]
    assert data["bests"] == {"tracking": 0.42}


def test_scores_empty(client):
    resp = client.get("/api/training/scores", params={"player": "不存在#9999"})
    assert resp.status_code == 200
    assert resp.json() == {"scores": [], "bests": {}}


def test_invalid_drill_rejected(client):
    resp = _post(client, "wallbang", 100.0)
    assert resp.status_code in (400, 422)
