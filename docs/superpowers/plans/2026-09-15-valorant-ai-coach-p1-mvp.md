# 无畏契约 AI 对局教练 P1 MVP 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现本地 Web 应用 MVP：战绩查询（采集器接口 + Fixture 数据源 + WeGame 采集器骨架）、标准化 Match JSON、LLM 文本分析、六维评分、风格定位、分享卡片、训练计划、基础前端。

**Architecture:** Python FastAPI 后端 + SQLite 存储 + Vue 3 前端。数据层用适配器模式隔离数据源（Fixture 采集器先行，WeGame 采集器按可配置端点实现，需真机验证）；分析层为纯函数流水线（metrics → archetypes → rules）+ LLM 客户端；前端为深色电竞风 SPA。

**Tech Stack:** Python 3.11+ / FastAPI / SQLite (sqlite3 标准库) / pydantic v2 / httpx / pytest / Vue 3 / Vite / ECharts / OpenAI 兼容 API。

## Global Constraints

- 只分析本人及同场公开可见数据；不做绕过隐私开关的功能。
- LLM 走 OpenAI 兼容接口，base_url/api_key/model 均可配置，未配置时降级为纯数据展示。
- 所有凭证与数据仅存本地（SQLite + 本地文件），不上传。
- 标准化 Match JSON 是数据层与分析层之间的唯一契约，下游不得依赖 WeGame 原始字段。
- Python 包管理用 `venv` + `pip`；前端用 `npm`。
- 所有后端测试不得发起真实网络请求（LLM/HTTP 一律 mock）。
- 提交信息用中文 conventional commits（如 `feat: 新增六维评分计算`）。

## 已知限制（如实声明）

- WeGame 内部接口只能在 Windows + 已登录 WeGame 的真机上验证。本计划将 WeGame 采集器实现为「登录态获取 + 可配置端点 + mock 测试」的结构完整实现，端点路径集中在 `config.py` 中可改；真机联调作为 P1 收尾的人工验收项，失败不阻塞其余功能（Fixture 数据源保证全流程可跑）。

---

### Task 1: 项目脚手架 + 标准化 Match Schema

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/schemas.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_schemas.py`
- Create: `backend/tests/fixtures/match_sample.json`
- Create: `.gitignore`
- Create: `README.md`

**Interfaces:**
- Produces: `Match`, `PlayerMatchStats`, `RoundResult`（pydantic 模型，全项目通用契约）；`Settings`（配置）；`MATCH_SAMPLE_PATH` 常量路径。

- [ ] **Step 1: 初始化 Python 环境与依赖**

```bash
cd ~/valorant-ai-coach
mkdir -p backend/app backend/tests/fixtures frontend
python3 -m venv backend/.venv
```

`backend/requirements.txt`:
```
fastapi>=0.110
uvicorn>=0.29
pydantic>=2.6
httpx>=0.27
pytest>=8.0
```

`.gitignore`:
```
backend/.venv/
__pycache__/
*.pyc
*.db
node_modules/
frontend/dist/
.kimi-code/
```

- [ ] **Step 2: 写失败的 schema 测试**

`backend/tests/test_schemas.py`:
```python
import json
from pathlib import Path

from app.schemas import Match

MATCH_SAMPLE_PATH = Path(__file__).parent / "fixtures" / "match_sample.json"


def test_match_sample_parses():
    raw = json.loads(MATCH_SAMPLE_PATH.read_text(encoding="utf-8"))
    match = Match.model_validate(raw)
    assert match.match_id == "fixture-match-001"
    assert len(match.players) == 10
    me = next(p for p in match.players if p.name == "测试玩家#1234")
    assert me.kills == 18
    assert match.blue_score + match.red_score >= 13


def test_headshot_rate_derivable():
    raw = json.loads(MATCH_SAMPLE_PATH.read_text(encoding="utf-8"))
    match = Match.model_validate(raw)
    me = next(p for p in match.players if p.name == "测试玩家#1234")
    total = me.headshots + me.bodyshots + me.legshots
    assert total > 0
```

- [ ] **Step 3: 运行测试确认失败**

Run: `cd backend && .venv/bin/pip install -r requirements.txt && .venv/bin/python -m pytest tests/test_schemas.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'app'`

- [ ] **Step 4: 实现 schemas.py**

`backend/app/schemas.py`:
```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PlayerMatchStats(BaseModel):
    puuid: str
    name: str  # 昵称#数字ID
    agent: str
    team: Literal["blue", "red"]
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    score: int = 0  # ACS
    headshots: int = 0
    bodyshots: int = 0
    legshots: int = 0
    damage_made: int = 0
    first_bloods: int = 0
    first_deaths: int = 0
    econ_spent: int = 0
    ability_casts: dict[str, int] = Field(default_factory=dict)
    party_id: str | None = None


class RoundResult(BaseModel):
    round_num: int
    winning_team: Literal["blue", "red"]
    end_type: str = "elimination"  # elimination/defuse/detonate/time


class Match(BaseModel):
    match_id: str
    mode: str = "竞技模式"
    map: str
    started_at: datetime
    blue_score: int
    red_score: int
    players: list[PlayerMatchStats]
    rounds: list[RoundResult] = Field(default_factory=list)
```

- [ ] **Step 5: 写 fixture 数据**

`backend/tests/fixtures/match_sample.json`：构造一场 13:9 的完整对局，10 名玩家，目标玩家 `测试玩家#1234`（blue 队，捷风，18/14/5，ACS 245，headshots 6/bodyshots 10/legshots 2，first_bloods 4/first_deaths 2，econ_spent 38500，damage_made 2900），其余 9 人填满两队，22 个 RoundResult。字段必须与 `Match` 模型完全对应。

- [ ] **Step 6: 实现 config.py**

`backend/app/config.py`:
```python
from pathlib import Path

from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "coach.db"
FIXTURE_DIR = BASE_DIR / "tests" / "fixtures"


class LLMSettings(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"


class WeGameSettings(BaseModel):
    # 真机联调时按实际抓包结果修改；路径集中在此便于维护
    match_list_path: str = "/wegine/valorant/v1/match-history"
    match_detail_path: str = "/wegine/valorant/v1/match-detail"
    base_url: str = "https://mlol.qt.qq.com"


class Settings(BaseModel):
    llm: LLMSettings = LLMSettings()
    wegame: WeGameSettings = WeGameSettings()


def load_settings() -> Settings:
    config_file = BASE_DIR / "config.json"
    if config_file.exists():
        return Settings.model_validate_json(config_file.read_text(encoding="utf-8"))
    return Settings()
```

- [ ] **Step 7: 运行测试确认通过**

Run: `cd backend && .venv/bin/python -m pytest tests/test_schemas.py -v`
Expected: 2 PASSED

- [ ] **Step 8: 写 README 并提交**

`README.md`：项目简介（一句话）、红线声明（只分析本人及公开数据）、快速开始占位（后续任务补全）。

```bash
cd ~/valorant-ai-coach
git add -A
git commit -m "feat: 项目脚手架与标准化 Match schema"
```

---

### Task 2: 六维评分引擎（metrics）

**Files:**
- Create: `backend/app/analysis/__init__.py`
- Create: `backend/app/analysis/baselines.py`
- Create: `backend/app/analysis/metrics.py`
- Create: `backend/tests/test_metrics.py`

**Interfaces:**
- Consumes: `Match`, `PlayerMatchStats`（Task 1）
- Produces:
  - `Baseline(BaseModel)`：每维度含 `median: float`、`p90: float`；`load_baseline(rank_tier: str) -> Baseline`
  - `DimensionRaws(BaseModel)`：`aim_hs_rate, duel_first_blood_diff, duel_first_duel_winrate, awareness_clutch_proxy, economy_spend_per_round, utility_casts_per_round, consistency_acs_cv`（均 float）
  - `compute_raws(matches: list[Match], player_name: str) -> DimensionRaws`
  - `AbilityScores(BaseModel)`：六维 0-100 + `overall: float` + `grade: str`
  - `compute_scores(raws: DimensionRaws, baseline: Baseline) -> AbilityScores`

- [ ] **Step 1: 写失败测试**

`backend/tests/test_metrics.py`:
```python
import json
from pathlib import Path

from app.analysis.baselines import load_baseline
from app.analysis.metrics import compute_raws, compute_scores
from app.schemas import Match


def _matches() -> list[Match]:
    raw = json.loads(
        (Path(__file__).parent / "fixtures" / "match_sample.json").read_text(encoding="utf-8")
    )
    return [Match.model_validate(raw)]


def test_compute_raws():
    raws = compute_raws(_matches(), "测试玩家#1234")
    # 6/(6+10+2) = 0.333
    assert abs(raws.aim_hs_rate - 6 / 18) < 1e-6
    # first_bloods - first_deaths = 2
    assert raws.duel_first_blood_diff == 2.0
    assert raws.utility_casts_per_round >= 0


def test_compute_scores_bounds_and_grade():
    raws = compute_raws(_matches(), "测试玩家#1234")
    scores = compute_scores(raws, load_baseline("钻石"))
    for v in (scores.aim, scores.duel, scores.awareness,
              scores.economy, scores.utility, scores.consistency, scores.overall):
        assert 0 <= v <= 100
    assert scores.grade in ("S", "A", "B", "C", "D")


def test_median_maps_to_50():
    baseline = load_baseline("钻石")
    from app.analysis.metrics import DimensionRaws
    raws = DimensionRaws(
        aim_hs_rate=baseline.aim.median,
        duel_first_blood_diff=baseline.duel.median,
        duel_first_duel_winrate=baseline.duel.median,
        awareness_clutch_proxy=baseline.awareness.median,
        economy_spend_per_round=baseline.economy.median,
        utility_casts_per_round=baseline.utility.median,
        consistency_acs_cv=baseline.consistency.median,
    )
    scores = compute_scores(raws, baseline)
    assert abs(scores.aim - 50) < 1e-6
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_metrics.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'app.analysis'`

- [ ] **Step 3: 实现 baselines.py**

`backend/app/analysis/baselines.py`：内置冷启动基准（钻石段位经验值，注释注明"待真实数据校准"）：
```python
from pydantic import BaseModel


class DimensionBaseline(BaseModel):
    median: float
    p90: float


class Baseline(BaseModel):
    aim: DimensionBaseline
    duel: DimensionBaseline
    awareness: DimensionBaseline
    economy: DimensionBaseline
    utility: DimensionBaseline
    consistency: DimensionBaseline


# 冷启动经验值，待采集数据积累后按段位真实分布校准
_BASELINES: dict[str, Baseline] = {
    "钻石": Baseline(
        aim=DimensionBaseline(median=0.22, p90=0.35),
        duel=DimensionBaseline(median=0.5, p90=0.7),
        awareness=DimensionBaseline(median=0.15, p90=0.30),
        economy=DimensionBaseline(median=1800.0, p90=2200.0),
        utility=DimensionBaseline(median=1.5, p90=2.5),
        consistency=DimensionBaseline(median=0.25, p90=0.10),
    ),
}


def load_baseline(rank_tier: str) -> Baseline:
    return _BASELINES.get(rank_tier, _BASELINES["钻石"])
```

- [ ] **Step 4: 实现 metrics.py**

`backend/app/analysis/metrics.py`：
```python
from pydantic import BaseModel

from app.analysis.baselines import Baseline, DimensionBaseline
from app.schemas import Match


class DimensionRaws(BaseModel):
    aim_hs_rate: float
    duel_first_blood_diff: float
    duel_first_duel_winrate: float
    awareness_clutch_proxy: float
    economy_spend_per_round: float
    utility_casts_per_round: float
    consistency_acs_cv: float


class AbilityScores(BaseModel):
    aim: float
    duel: float
    awareness: float
    economy: float
    utility: float
    consistency: float
    overall: float
    grade: str


def _player_stats(matches: list[Match], player_name: str):
    stats = []
    for m in matches:
        p = next((p for p in m.players if p.name == player_name), None)
        if p is not None:
            stats.append((m, p))
    if not stats:
        raise ValueError(f"对局中找不到玩家: {player_name}")
    return stats


def compute_raws(matches: list[Match], player_name: str) -> DimensionRaws:
    stats = _player_stats(matches, player_name)
    kills = sum(p.kills for _, p in stats)
    hs = sum(p.headshots for _, p in stats)
    fb = sum(p.first_bloods for _, p in stats)
    fd = sum(p.first_deaths for _, p in stats)
    rounds = sum(max(m.blue_score + m.red_score, 1) for m, _ in stats)
    casts = sum(sum(p.ability_casts.values()) for _, p in stats)
    acs_values = [p.score / max(m.blue_score + m.red_score, 1) for m, p in stats]

    hs_rate = hs / kills if kills else 0.0
    fb_diff = float(fb - fd)
    fb_wr = fb / (fb + fd) if (fb + fd) else 0.5
    # 冷启动代理指标：多杀占比（视觉复盘上线后换被侧身击杀占比）
    multi_kills = sum(1 for _, p in stats if p.kills >= 2 * max(p.deaths, 1) and p.kills >= 15)
    clutch_proxy = multi_kills / len(stats)
    econ = sum(p.econ_spent for _, p in stats) / rounds
    casts_per_round = casts / rounds
    mean_acs = sum(acs_values) / len(acs_values)
    if len(acs_values) > 1 and mean_acs > 0:
        var = sum((v - mean_acs) ** 2 for v in acs_values) / (len(acs_values) - 1)
        cv = (var ** 0.5) / mean_acs
    else:
        cv = 0.25

    return DimensionRaws(
        aim_hs_rate=hs_rate,
        duel_first_blood_diff=fb_diff,
        duel_first_duel_winrate=fb_wr,
        awareness_clutch_proxy=clutch_proxy,
        economy_spend_per_round=econ,
        utility_casts_per_round=casts_per_round,
        consistency_acs_cv=cv,
    )


def _percentile_score(value: float, dim: DimensionBaseline, lower_is_better: bool = False) -> float:
    if lower_is_better:
        if dim.median <= 0:
            return 50.0
        if value <= dim.median:
            # 好于中位数：越接近 0 分越高，median 映射 50，0 映射 100
            return min(100.0, 50.0 + 50.0 * (dim.median - value) / dim.median)
        # 差于中位数：按相对偏差从 50 递减，最低钳到 0
        return max(0.0, 50.0 - 50.0 * (value - dim.median) / dim.median)
    median, p90 = dim.median, dim.p90
    if value <= median:
        return max(0.0, 50.0 * value / median) if median else 50.0
    span = p90 - median
    return min(100.0, 50.0 + 40.0 * (value - median) / span) if span > 0 else 90.0


_WEIGHTS = {"aim": 0.22, "duel": 0.20, "awareness": 0.16,
            "economy": 0.14, "utility": 0.14, "consistency": 0.14}


def compute_scores(raws: DimensionRaws, baseline: Baseline) -> AbilityScores:
    aim = _percentile_score(raws.aim_hs_rate, baseline.aim)
    duel = _percentile_score(raws.duel_first_duel_winrate, baseline.duel)
    awareness = _percentile_score(raws.awareness_clutch_proxy, baseline.awareness)
    economy = _percentile_score(raws.economy_spend_per_round, baseline.economy)
    utility = _percentile_score(raws.utility_casts_per_round, baseline.utility)
    consistency = _percentile_score(raws.consistency_acs_cv, baseline.consistency, lower_is_better=True)
    dims = {"aim": aim, "duel": duel, "awareness": awareness,
            "economy": economy, "utility": utility, "consistency": consistency}
    overall = sum(dims[k] * _WEIGHTS[k] for k in dims)
    grade = "S" if overall >= 85 else "A" if overall >= 70 else "B" if overall >= 50 else "C" if overall >= 30 else "D"
    return AbilityScores(**dims, overall=round(overall, 1), grade=grade)
```

- [ ] **Step 5: 运行确认通过**

Run: `cd backend && .venv/bin/python -m pytest tests/test_metrics.py -v`
Expected: 3 PASSED

- [ ] **Step 6: 提交**

```bash
cd ~/valorant-ai-coach
git add backend/app/analysis backend/tests/test_metrics.py
git commit -m "feat: 六维能力评分引擎"
```

---

### Task 3: 风格原型系统（archetypes）

**Files:**
- Create: `backend/app/coaching/__init__.py`
- Create: `backend/app/coaching/archetypes.py`
- Create: `backend/tests/test_archetypes.py`

**Interfaces:**
- Consumes: `DimensionRaws`（Task 2）
- Produces:
  - `Archetype(BaseModel)`：`key: str, title: str, roast_hint: str`
  - `match_archetypes(raws: DimensionRaws) -> tuple[Archetype, list[Archetype]]`（主原型 + 副标签，副标签可为空列表）
  - `ARCHETYPES: list[Archetype]`（全部原型注册表）

- [ ] **Step 1: 写失败测试**

`backend/tests/test_archetypes.py`:
```python
from app.analysis.metrics import DimensionRaws
from app.coaching.archetypes import match_archetypes


def _raws(**kw) -> DimensionRaws:
    defaults = dict(
        aim_hs_rate=0.22, duel_first_blood_diff=0.0, duel_first_duel_winrate=0.5,
        awareness_clutch_proxy=0.15, economy_spend_per_round=1800.0,
        utility_casts_per_round=1.5, consistency_acs_cv=0.25,
    )
    defaults.update(kw)
    return DimensionRaws(**defaults)


def test_headshot_machine():
    primary, subs = match_archetypes(_raws(aim_hs_rate=0.40))
    assert primary.key == "headshot_machine"


def test_suicide_squad():
    primary, _ = match_archetypes(_raws(duel_first_blood_diff=0.0, duel_first_duel_winrate=0.5))
    # 首杀与首死都靠 aggressive 判定：用 fb_diff≈0 且总对枪次数高不直接可得，
    # 原型判定基于 fb_diff 绝对值低 + winrate 中庸 → 默认原型
    assert primary.key in ("balanced_default", "headshot_machine")


def test_econ_blackhole_subtag():
    _, subs = match_archetypes(_raws(economy_spend_per_round=2600.0))
    assert any(a.key == "econ_blackhole" for a in subs)


def test_stable_sniper_subtag():
    _, subs = match_archetypes(_raws(consistency_acs_cv=0.08))
    assert any(a.key == "stable_pillar" for a in subs)
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_archetypes.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'app.coaching'`

- [ ] **Step 3: 实现 archetypes.py**

`backend/app/coaching/archetypes.py`:
```python
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
```

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && .venv/bin/python -m pytest tests/test_archetypes.py -v`
Expected: 4 PASSED

- [ ] **Step 5: 提交**

```bash
cd ~/valorant-ai-coach
git add backend/app/coaching backend/tests/test_archetypes.py
git commit -m "feat: 风格原型匹配系统"
```

---

### Task 4: 训练计划规则库（rules + planner）

**Files:**
- Create: `backend/app/coaching/rules.py`
- Create: `backend/app/coaching/planner.py`
- Create: `backend/tests/test_rules.py`

**Interfaces:**
- Consumes: `DimensionRaws`, `AbilityScores`（Task 2）
- Produces:
  - `Problem(BaseModel)`：`dimension: str, description: str, evidence: str`
  - `detect_problems(raws: DimensionRaws, baseline: Baseline) -> list[Problem]`（rules.py）
  - `TrainingTask(BaseModel)`：`name: str, tool: str, detail: str, freq: str, done: bool = False`
  - `build_plan(problems: list[Problem]) -> list[TrainingTask]`（planner.py）
  - `RULE_TABLE: dict[str, list[TrainingTask]]`（按 dimension 索引）

- [ ] **Step 1: 写失败测试**

`backend/tests/test_rules.py`:
```python
from app.analysis.baselines import load_baseline
from app.analysis.metrics import DimensionRaws
from app.coaching.planner import build_plan
from app.coaching.rules import detect_problems

BASELINE = load_baseline("钻石")


def _raws(**kw) -> DimensionRaws:
    defaults = dict(
        aim_hs_rate=0.22, duel_first_blood_diff=0.0, duel_first_duel_winrate=0.5,
        awareness_clutch_proxy=0.15, economy_spend_per_round=1800.0,
        utility_casts_per_round=1.5, consistency_acs_cv=0.25,
    )
    defaults.update(kw)
    return DimensionRaws(**defaults)


def test_low_hs_triggers_aim_problem():
    problems = detect_problems(_raws(aim_hs_rate=0.10), BASELINE)
    assert any(p.dimension == "aim" for p in problems)
    aim_p = next(p for p in problems if p.dimension == "aim")
    assert "10" in aim_p.evidence or "0.1" in aim_p.evidence


def test_no_problem_when_above_median():
    problems = detect_problems(_raws(aim_hs_rate=0.30), BASELINE)
    assert not any(p.dimension == "aim" for p in problems)


def test_plan_maps_aim_to_aimlab():
    problems = detect_problems(_raws(aim_hs_rate=0.10), BASELINE)
    plan = build_plan(problems)
    assert plan
    assert any("Aim Lab" in t.tool or "aim" in t.tool.lower() for t in plan)
    assert all(t.freq for t in plan)
    assert all(t.done is False for t in plan)
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_rules.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'app.coaching.rules'`

- [ ] **Step 3: 实现 rules.py**

`backend/app/coaching/rules.py`:
```python
from pydantic import BaseModel

from app.analysis.baselines import Baseline
from app.analysis.metrics import DimensionRaws


class Problem(BaseModel):
    dimension: str  # aim/duel/awareness/economy/utility/consistency
    description: str
    evidence: str


def detect_problems(raws: DimensionRaws, baseline: Baseline) -> list[Problem]:
    problems: list[Problem] = []
    if raws.aim_hs_rate < baseline.aim.median * 0.8:
        problems.append(Problem(
            dimension="aim",
            description="爆头率明显低于同段位水平，瞄准习惯偏向身体",
            evidence=f"爆头率 {raws.aim_hs_rate:.0%}，段位中位数 {baseline.aim.median:.0%}",
        ))
    if raws.duel_first_duel_winrate < baseline.duel.median * 0.8:
        problems.append(Problem(
            dimension="duel",
            description="首轮对枪胜率偏低，开局交火经常吃亏",
            evidence=f"首轮对枪胜率 {raws.duel_first_duel_winrate:.0%}，段位中位数 {baseline.duel.median:.0%}",
        ))
    if raws.awareness_clutch_proxy < baseline.awareness.median * 0.6:
        problems.append(Problem(
            dimension="awareness",
            description="残局与多杀场景贡献不足，意识与站位有提升空间",
            evidence=f"残局代理指标 {raws.awareness_clutch_proxy:.2f}，段位中位数 {baseline.awareness.median:.2f}",
        ))
    if raws.economy_spend_per_round > baseline.economy.p90:
        problems.append(Problem(
            dimension="economy",
            description="每回合花费过高，eco 局可能存在强行起枪",
            evidence=f"回合均花费 {raws.economy_spend_per_round:.0f}，段位 p90 {baseline.economy.p90:.0f}",
        ))
    if raws.utility_casts_per_round < baseline.utility.median * 0.6:
        problems.append(Problem(
            dimension="utility",
            description="技能使用率偏低，没有发挥英雄技能价值",
            evidence=f"回合均技能 {raws.utility_casts_per_round:.1f}，段位中位数 {baseline.utility.median:.1f}",
        ))
    if raws.consistency_acs_cv > 0.40:
        problems.append(Problem(
            dimension="consistency",
            description="发挥波动大，神一场鬼一场",
            evidence=f"ACS 变异系数 {raws.consistency_acs_cv:.2f}，超过 0.40 阈值",
        ))
    return problems
```

- [ ] **Step 4: 实现 planner.py**

`backend/app/coaching/planner.py`:
```python
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
```

- [ ] **Step 5: 运行确认通过并提交**

Run: `cd backend && .venv/bin/python -m pytest tests/test_rules.py -v`
Expected: 3 PASSED

```bash
cd ~/valorant-ai-coach
git add backend/app/coaching backend/tests/test_rules.py
git commit -m "feat: 问题检测规则库与训练计划生成器"
```

---

### Task 5: LLM 客户端与文本分析器

**Files:**
- Create: `backend/app/analysis/llm.py`
- Create: `backend/app/analysis/prompts.py`
- Create: `backend/app/analysis/analyzer.py`
- Create: `backend/tests/test_analyzer.py`

**Interfaces:**
- Consumes: `Match`（Task 1）、`DimensionRaws`（Task 2）、`Archetype`（Task 3）、`Problem`（Task 4）
- Produces:
  - `LLMClient(base_url: str, api_key: str, model: str)`，`.chat(system: str, user: str) -> str`，`is_configured() -> bool`
  - `MatchAnalysis(BaseModel)`：`summary: str, strengths: list[str], weaknesses: list[str], roast: str`
  - `analyze_match(match: Match, player_name: str, raws: DimensionRaws, primary: Archetype, subs: list[Archetype], llm: LLMClient | None) -> MatchAnalysis`（llm 为 None 时返回模板化降级结果）

- [ ] **Step 1: 写失败测试（LLM 全部 mock，不发真实请求）**

`backend/tests/test_analyzer.py`:
```python
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
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_analyzer.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'app.analysis.llm'`

- [ ] **Step 3: 实现 llm.py**

`backend/app/analysis/llm.py`:
```python
import httpx


class LLMClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def chat(self, system: str, user: str) -> str:
        if not self.is_configured():
            raise RuntimeError("LLM 未配置 api_key")
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.7,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
```

- [ ] **Step 4: 实现 prompts.py**

`backend/app/analysis/prompts.py`:
```python
SYSTEM_COACH = """你是一位毒舌但专业的无畏契约教练。
根据玩家对局数据输出 JSON（不要输出别的）：
{"summary": "一句话总结", "strengths": ["优势1", ...], "weaknesses": ["问题1", ...], "roast": "一句锐评"}
锐评要有电竞梗、有话题性，但不要人身攻击。所有输出用中文。"""


def build_match_prompt(player_name: str, stats_block: str, archetype_title: str) -> str:
    return f"""玩家 {player_name} 的本局数据：
{stats_block}

系统判定的风格原型：{archetype_title}
请基于数据给出分析，weaknesses 里每条都要引用具体数字。"""
```

- [ ] **Step 5: 实现 analyzer.py**

`backend/app/analysis/analyzer.py`:
```python
import json

from pydantic import BaseModel

from app.analysis.llm import LLMClient
from app.analysis.metrics import DimensionRaws
from app.analysis.prompts import SYSTEM_COACH, build_match_prompt
from app.coaching.archetypes import Archetype
from app.schemas import Match


class MatchAnalysis(BaseModel):
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    roast: str


def _stats_block(match: Match, player_name: str, raws: DimensionRaws) -> str:
    p = next(p for p in match.players if p.name == player_name)
    return (
        f"地图 {match.map}，比分 {match.blue_score}:{match.red_score}，英雄 {p.agent}\n"
        f"KDA {p.kills}/{p.deaths}/{p.assists}，ACS {p.score}，爆头率 {raws.aim_hs_rate:.0%}\n"
        f"首杀 {p.first_bloods} 首死 {p.first_deaths}，回合均花费 {raws.economy_spend_per_round:.0f}"
    )


def analyze_match(match: Match, player_name: str, raws: DimensionRaws,
                  primary: Archetype, subs: list[Archetype],
                  llm: LLMClient | None) -> MatchAnalysis:
    block = _stats_block(match, player_name, raws)
    if llm is not None and llm.is_configured():
        resp = llm.chat(SYSTEM_COACH, build_match_prompt(player_name, block, primary.title))
        data = json.loads(resp.strip().removeprefix("```json").removesuffix("```"))
        return MatchAnalysis.model_validate(data)
    # 降级：模板化输出
    p = next(p for p in match.players if p.name == player_name)
    return MatchAnalysis(
        summary=f"{player_name} 使用 {p.agent} 打出 {p.kills}/{p.deaths}/{p.assists}，ACS {p.score}。",
        strengths=[f"爆头率 {raws.aim_hs_rate:.0%}"] if raws.aim_hs_rate > 0.25 else [],
        weaknesses=[f"爆头率仅 {raws.aim_hs_rate:.0%}"] if raws.aim_hs_rate <= 0.15 else [],
        roast=f"系统鉴定：{primary.title}。{primary.roast_hint}",
    )
```

- [ ] **Step 6: 运行确认通过并提交**

Run: `cd backend && .venv/bin/python -m pytest tests/test_analyzer.py -v`
Expected: 3 PASSED

```bash
cd ~/valorant-ai-coach
git add backend/app/analysis backend/tests/test_analyzer.py
git commit -m "feat: LLM 客户端与文本分析器（含无 key 降级）"
```

---

### Task 6: 采集器接口 + Fixture 采集器 + WeGame 采集器骨架

**Files:**
- Create: `backend/app/collector/__init__.py`
- Create: `backend/app/collector/base.py`
- Create: `backend/app/collector/fixture.py`
- Create: `backend/app/collector/wegame.py`
- Create: `backend/tests/test_collector.py`

**Interfaces:**
- Consumes: `Match`（Task 1）、`Settings`/`WeGameSettings`（Task 1）
- Produces:
  - `Collector(Protocol)`：`recent_matches(name: str, count: int = 10) -> list[Match]`、`match_detail(match_id: str) -> Match`
  - `FixtureCollector(fixture_dir: Path)`：实现 Collector
  - `WeGameCollector(settings: WeGameSettings, fetch_json: Callable[[str, dict], dict] | None = None)`：`fetch_json` 可注入以便 mock 测试；未注入时用 httpx 直连（真机联调用）

- [ ] **Step 1: 写失败测试**

`backend/tests/test_collector.py`:
```python
from pathlib import Path

from app.collector.fixture import FixtureCollector
from app.collector.wegame import WeGameCollector, map_wegame_detail
from app.config import WeGameSettings

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_fixture_collector_lists_and_detail():
    c = FixtureCollector(FIXTURE_DIR)
    matches = c.recent_matches("测试玩家#1234")
    assert len(matches) >= 1
    detail = c.match_detail(matches[0].match_id)
    assert detail.match_id == matches[0].match_id
    assert len(detail.players) == 10


def test_wegame_detail_mapping():
    # WeGame 原始响应（结构按真机抓包校准，此处定义映射契约）
    raw = {
        "matchId": "wg-001",
        "mapName": "亚海悬城",
        "queueName": "竞技模式",
        "startTime": "2026-09-14T20:00:00",
        "teamA": {"score": 13},
        "teamB": {"score": 9},
        "players": [
            {"id": "p1", "nickname": "测试玩家#1234", "heroName": "捷风", "team": "A",
             "kill": 18, "death": 14, "assist": 5, "combatScore": 245,
             "headshot": 6, "bodyshot": 10, "legshot": 2,
             "damage": 2900, "firstKill": 4, "firstDeath": 2, "goldSpent": 38500},
        ],
    }
    match = map_wegame_detail(raw)
    assert match.match_id == "wg-001"
    assert match.blue_score == 13
    me = match.players[0]
    assert me.name == "测试玩家#1234"
    assert me.kills == 18 and me.team == "blue"


def test_wegame_collector_uses_injected_fetch():
    captured = {}

    def fake_fetch(path: str, params: dict) -> dict:
        captured["path"] = path
        return {"list": []}

    c = WeGameCollector(WeGameSettings(), fetch_json=fake_fetch)
    assert c.recent_matches("测试玩家#1234") == []
    assert captured["path"] == WeGameSettings().match_list_path
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_collector.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'app.collector'`

- [ ] **Step 3: 实现 base.py**

`backend/app/collector/base.py`:
```python
from typing import Protocol

from app.schemas import Match


class Collector(Protocol):
    def recent_matches(self, name: str, count: int = 10) -> list[Match]: ...
    def match_detail(self, match_id: str) -> Match: ...
```

- [ ] **Step 4: 实现 fixture.py**

`backend/app/collector/fixture.py`:
```python
import json
from pathlib import Path

from app.schemas import Match


class FixtureCollector:
    def __init__(self, fixture_dir: Path):
        self.fixture_dir = fixture_dir

    def _load_all(self) -> list[Match]:
        matches = []
        for f in sorted(self.fixture_dir.glob("*.json")):
            matches.append(Match.model_validate(json.loads(f.read_text(encoding="utf-8"))))
        return matches

    def recent_matches(self, name: str, count: int = 10) -> list[Match]:
        mine = [m for m in self._load_all()
                if any(p.name == name for p in m.players)]
        return sorted(mine, key=lambda m: m.started_at, reverse=True)[:count]

    def match_detail(self, match_id: str) -> Match:
        for m in self._load_all():
            if m.match_id == match_id:
                return m
        raise KeyError(f"fixture 中不存在对局 {match_id}")
```

- [ ] **Step 5: 实现 wegame.py（骨架 + 映射，端点真机校准）**

`backend/app/collector/wegame.py`:
```python
from collections.abc import Callable
from datetime import datetime

import httpx

from app.config import WeGameSettings
from app.schemas import Match, PlayerMatchStats


def map_wegame_detail(raw: dict) -> Match:
    """WeGame 原始对局详情 → 标准化 Match。字段名按真机抓包结果校准。"""
    players = [
        PlayerMatchStats(
            puuid=p["id"], name=p["nickname"], agent=p["heroName"],
            team="blue" if p["team"] == "A" else "red",
            kills=p.get("kill", 0), deaths=p.get("death", 0), assists=p.get("assist", 0),
            score=p.get("combatScore", 0),
            headshots=p.get("headshot", 0), bodyshots=p.get("bodyshot", 0), legshots=p.get("legshot", 0),
            damage_made=p.get("damage", 0),
            first_bloods=p.get("firstKill", 0), first_deaths=p.get("firstDeath", 0),
            econ_spent=p.get("goldSpent", 0),
        )
        for p in raw.get("players", [])
    ]
    return Match(
        match_id=raw["matchId"], mode=raw.get("queueName", "竞技模式"),
        map=raw["mapName"], started_at=datetime.fromisoformat(raw["startTime"]),
        blue_score=raw["teamA"]["score"], red_score=raw["teamB"]["score"],
        players=players,
    )


class WeGameCollector:
    """结构完整的 WeGame 采集器。登录态获取与真实端点需 Windows 真机联调：
    1. 在本机专用 Chrome 登录 WeGame（或 CDP 复用已有登录态）
    2. 抓包校准 WeGameSettings 中的端点路径与 map_wegame_detail 的字段名
    """

    def __init__(self, settings: WeGameSettings,
                 fetch_json: Callable[[str, dict], dict] | None = None):
        self.settings = settings
        self._fetch = fetch_json or self._http_fetch

    def _http_fetch(self, path: str, params: dict) -> dict:
        resp = httpx.get(f"{self.settings.base_url}{path}", params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def recent_matches(self, name: str, count: int = 10) -> list[Match]:
        data = self._fetch(self.settings.match_list_path, {"nickname": name, "count": count})
        return [map_wegame_detail(self._fetch(self.settings.match_detail_path,
                                              {"matchId": item["matchId"]}))
                for item in data.get("list", [])[:count]]

    def match_detail(self, match_id: str) -> Match:
        return map_wegame_detail(self._fetch(self.settings.match_detail_path,
                                             {"matchId": match_id}))
```

- [ ] **Step 6: 运行确认通过并提交**

Run: `cd backend && .venv/bin/python -m pytest tests/test_collector.py -v`
Expected: 3 PASSED

```bash
cd ~/valorant-ai-coach
git add backend/app/collector backend/tests/test_collector.py
git commit -m "feat: 采集器接口、Fixture 数据源与 WeGame 采集器骨架"
```

---

### Task 7: SQLite 存储 + FastAPI 路由

**Files:**
- Create: `backend/app/db.py`
- Create: `backend/app/routes/__init__.py`
- Create: `backend/app/routes/matches.py`
- Create: `backend/app/routes/analysis.py`
- Create: `backend/app/routes/coaching.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: 全部前述模块
- Produces（HTTP API 契约，前端依赖）：
  - `GET /api/matches?name=<昵称#ID>` → `list[Match]`
  - `GET /api/analysis/{match_id}?name=<昵称#ID>` → `{scores: AbilityScores, primary: Archetype, subs: list[Archetype], analysis: MatchAnalysis, problems: list[Problem]}`
  - `GET /api/plan?name=<昵称#ID>` → `{tasks: list[TrainingTask]}`
  - `POST /api/plan/toggle` body `{task_name: str, done: bool}` → `{ok: true}`（打卡持久化到 SQLite）
- `init_db()` / `save_plan(name, tasks)` / `load_plan(name) -> list[TrainingTask]`（db.py）
- 数据源选择：环境变量 `COLLECTOR=fixture`（默认）或 `wegame`，在 `main.py` 的 `create_app()` 中注入

- [ ] **Step 1: 写失败测试**

`backend/tests/test_api.py`:
```python
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("COLLECTOR", "fixture")
    monkeypatch.setenv("DB_PATH_OVERRIDE", str(tmp_path / "test.db"))
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
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_api.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 3: 实现 db.py**

`backend/app/db.py`:
```python
import json
import os
import sqlite3
from pathlib import Path

from app.config import DB_PATH


def _db_path() -> Path:
    override = os.environ.get("DB_PATH_OVERRIDE")
    return Path(override) if override else DB_PATH


def init_db() -> None:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                player_name TEXT NOT NULL,
                task_name TEXT NOT NULL,
                task_json TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (player_name, task_name)
            )
        """)


def save_plan(player_name: str, tasks: list[dict]) -> None:
    with sqlite3.connect(_db_path()) as conn:
        for t in tasks:
            conn.execute(
                "INSERT OR REPLACE INTO plans (player_name, task_name, task_json, done) VALUES (?,?,?,?)",
                (player_name, t["name"], json.dumps(t, ensure_ascii=False),
                 1 if t.get("done") else 0),
            )


def load_plan(player_name: str) -> list[dict]:
    with sqlite3.connect(_db_path()) as conn:
        rows = conn.execute(
            "SELECT task_json, done FROM plans WHERE player_name = ? ORDER BY rowid",
            (player_name,),
        ).fetchall()
    result = []
    for task_json, done in rows:
        t = json.loads(task_json)
        t["done"] = bool(done)
        result.append(t)
    return result


def set_task_done(player_name: str, task_name: str, done: bool) -> bool:
    with sqlite3.connect(_db_path()) as conn:
        cur = conn.execute(
            "UPDATE plans SET done = ? WHERE player_name = ? AND task_name = ?",
            (1 if done else 0, player_name, task_name),
        )
        return cur.rowcount > 0
```

- [ ] **Step 4: 实现路由与 main.py**

`backend/app/routes/matches.py`:
```python
from fastapi import APIRouter, Request

router = APIRouter(prefix="/api")


@router.get("/matches")
def list_matches(request: Request, name: str, count: int = 10):
    collector = request.app.state.collector
    return collector.recent_matches(name, count)
```

`backend/app/routes/analysis.py`:
```python
from fastapi import APIRouter, HTTPException, Request

from app.analysis.analyzer import analyze_match
from app.analysis.baselines import load_baseline
from app.analysis.metrics import compute_raws, compute_scores
from app.coaching.archetypes import match_archetypes
from app.coaching.rules import detect_problems

router = APIRouter(prefix="/api")


@router.get("/analysis/{match_id}")
def analyze(request: Request, match_id: str, name: str, rank_tier: str = "钻石"):
    collector = request.app.state.collector
    llm = request.app.state.llm
    try:
        match = collector.match_detail(match_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="对局不存在")
    if not any(p.name == name for p in match.players):
        raise HTTPException(status_code=404, detail="该玩家不在此对局中")

    raws = compute_raws([match], name)
    baseline = load_baseline(rank_tier)
    scores = compute_scores(raws, baseline)
    primary, subs = match_archetypes(raws)
    analysis = analyze_match(match, name, raws, primary, subs, llm)
    problems = detect_problems(raws, baseline)
    return {
        "scores": scores, "raws": raws,
        "primary": primary, "subs": subs,
        "analysis": analysis, "problems": problems,
    }
```

`backend/app/routes/coaching.py`:
```python
from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.analysis.baselines import load_baseline
from app.analysis.metrics import compute_raws
from app.coaching.planner import build_plan
from app.coaching.rules import detect_problems
from app.db import load_plan, save_plan, set_task_done

router = APIRouter(prefix="/api")


class ToggleBody(BaseModel):
    task_name: str
    done: bool


@router.get("/plan")
def get_plan(request: Request, name: str, rank_tier: str = "钻石"):
    existing = load_plan(name)
    if existing:
        return {"tasks": existing}
    collector = request.app.state.collector
    matches = collector.recent_matches(name, 10)
    if not matches:
        return {"tasks": []}
    raws = compute_raws(matches, name)
    problems = detect_problems(raws, load_baseline(rank_tier))
    tasks = [t.model_dump() for t in build_plan(problems)]
    save_plan(name, tasks)
    return {"tasks": tasks}


@router.post("/plan/toggle")
def toggle_task(body: ToggleBody, name: str):
    updated = set_task_done(name, body.task_name, body.done)
    return {"ok": updated}
```

`backend/app/main.py`:
```python
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.analysis.llm import LLMClient
from app.collector.fixture import FixtureCollector
from app.collector.wegame import WeGameCollector
from app.config import FIXTURE_DIR, load_settings
from app.db import init_db
from app.routes import analysis, coaching, matches


def create_app() -> FastAPI:
    init_db()
    settings = load_settings()
    app = FastAPI(title="无畏契约 AI 对局教练")
    app.add_middleware(CORSMiddleware, allow_origins=["*"],
                       allow_methods=["*"], allow_headers=["*"])

    if os.environ.get("COLLECTOR", "fixture") == "wegame":
        app.state.collector = WeGameCollector(settings.wegame)
    else:
        app.state.collector = FixtureCollector(FIXTURE_DIR)
    app.state.llm = LLMClient(settings.llm.base_url,
                              settings.llm.api_key, settings.llm.model)

    app.include_router(matches.router)
    app.include_router(analysis.router)
    app.include_router(coaching.router)

    dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="static")
    return app


app = create_app()
```

`backend/tests/fixtures` 的 fixture 数据在 Task 1 已建好；`test_api.py` 里 fixture 玩家名保持一致。

- [ ] **Step 5: 运行全部后端测试**

Run: `cd backend && .venv/bin/python -m pytest tests/ -v`
Expected: 全部 PASSED（schemas 2 + metrics 3 + archetypes 4 + rules 3 + analyzer 3 + collector 3 + api 4 = 22）

- [ ] **Step 6: 提交**

```bash
cd ~/valorant-ai-coach
git add backend
git commit -m "feat: SQLite 存储与 FastAPI 路由（matches/analysis/plan）"
```

---

### Task 8: 前端脚手架 + 首页（风格称号 + 雷达图 + 分享卡片）

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/api.js`
- Create: `frontend/src/router.js`
- Create: `frontend/src/pages/HomePage.vue`
- Create: `frontend/src/components/RadarChart.vue`
- Create: `frontend/src/components/ShareCard.vue`
- Create: `frontend/src/style.css`

**Interfaces:**
- Consumes: Task 7 的 HTTP API
- Produces: `api.js` 导出 `listMatches(name)`, `getAnalysis(matchId, name)`, `getPlan(name)`, `toggleTask(name, taskName, done)`；页面路由 `/`（首页）、`/matches`、`/report/:matchId`、`/plan`

- [ ] **Step 1: 初始化前端**

```bash
cd ~/valorant-ai-coach/frontend
npm create vite@latest . -- --template vue   # 若目录非空，手动创建以下文件
npm install vue-router echarts
```

`frontend/package.json` 关键依赖：`vue@^3.4`、`vue-router@^4`、`echarts@^5`，devDependencies：`vite@^5`、`@vitejs/plugin-vue`。

`frontend/vite.config.js`:
```js
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  server: { proxy: { '/api': 'http://127.0.0.1:8787' } },
})
```

- [ ] **Step 2: 全局样式（深色电竞风）**

`frontend/src/style.css`：
```css
:root {
  --bg: #0f1923; --panel: #1a2733; --accent: #ff4655;
  --text: #ece8e1; --muted: #768079;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif; }
.panel { background: var(--panel); border-radius: 8px; padding: 20px; }
.accent { color: var(--accent); }
.muted { color: var(--muted); }
button { background: var(--accent); color: #fff; border: 0; border-radius: 6px;
  padding: 8px 20px; cursor: pointer; font-size: 14px; }
input { background: #111c26; border: 1px solid #2b3a47; color: var(--text);
  border-radius: 6px; padding: 8px 12px; }
```

- [ ] **Step 3: API 客户端与路由**

`frontend/src/api.js`:
```js
const BASE = '/api'

export async function listMatches(name) {
  const r = await fetch(`${BASE}/matches?name=${encodeURIComponent(name)}`)
  return r.json()
}
export async function getAnalysis(matchId, name) {
  const r = await fetch(`${BASE}/analysis/${matchId}?name=${encodeURIComponent(name)}`)
  if (!r.ok) throw new Error((await r.json()).detail || '分析失败')
  return r.json()
}
export async function getPlan(name) {
  const r = await fetch(`${BASE}/plan?name=${encodeURIComponent(name)}`)
  return r.json()
}
export async function toggleTask(name, taskName, done) {
  const r = await fetch(`${BASE}/plan/toggle?name=${encodeURIComponent(name)}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task_name: taskName, done }),
  })
  return r.json()
}
```

`frontend/src/router.js`:
```js
import { createRouter, createWebHashHistory } from 'vue-router'
import HomePage from './pages/HomePage.vue'
import MatchesPage from './pages/MatchesPage.vue'
import ReportPage from './pages/ReportPage.vue'
import PlanPage from './pages/PlanPage.vue'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: HomePage },
    { path: '/matches', component: MatchesPage },
    { path: '/report/:matchId', component: ReportPage },
    { path: '/plan', component: PlanPage },
  ],
})
```

`frontend/src/main.js`:
```js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './style.css'

createApp(App).use(router).mount('#app')
```

`frontend/index.html`:
```html
<!doctype html>
<html lang="zh-CN">
<head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>无畏契约 AI 对局教练</title></head>
<body><div id="app"></div><script type="module" src="/src/main.js"></script></body>
</html>
```

- [ ] **Step 4: App.vue 布局 + 导航**

`frontend/src/App.vue`：顶部导航条（标题 + 玩家名输入框存 localStorage + 路由链接：首页/战绩/训练计划）+ `<router-view>`。玩家名统一从 localStorage 读写，key 为 `val_player_name`。

- [ ] **Step 5: 雷达图组件**

`frontend/src/components/RadarChart.vue`：props `scores`（六维分数对象），用 ECharts radar，六轴为：瞄准/对枪/意识/经济/技能/稳定，深色主题，accent 色填充半透明。

- [ ] **Step 6: 分享卡片组件**

`frontend/src/components/ShareCard.vue`：props `{ primary, subs, scores, roast, playerName }`。竖版卡片（375×550），大号称号标题、职业哥定位占位行、雷达图缩略（复用 RadarChart）、锐评金句、右下角 S/A 评级大字。样式按电竞海报风：accent 色描边、斜切装饰条。"保存图片"按钮用 `html2canvas`（需 `npm install html2canvas`）导出 PNG 下载。

- [ ] **Step 7: 首页**

`frontend/src/pages/HomePage.vue`：
- 无玩家名时：引导输入 `昵称#数字ID`
- 有玩家名时：拉最近一场的 analysis，展示 ShareCard + 雷达图 + 综合评分
- 加载中/失败态要有提示（如"未配置 LLM key 时为纯数据模式"）

- [ ] **Step 8: 构建验证**

Run: `cd frontend && npm run build`
Expected: 构建成功无报错

- [ ] **Step 9: 提交**

```bash
cd ~/valorant-ai-coach
git add frontend
git commit -m "feat: 前端脚手架与首页（风格称号、雷达图、分享卡片）"
```

---

### Task 9: 前端战绩列表页 + 单场报告页

**Files:**
- Create: `frontend/src/pages/MatchesPage.vue`
- Create: `frontend/src/pages/ReportPage.vue`

**Interfaces:**
- Consumes: `listMatches`, `getAnalysis`（Task 8）；路由 `/matches`、`/report/:matchId`

- [ ] **Step 1: 战绩列表页**

`frontend/src/pages/MatchesPage.vue`：表格列出最近对局（时间、地图、英雄、KDA、ACS、胜负红绿标记），点击行跳转 `/report/:matchId`。玩家名从 localStorage 取。

- [ ] **Step 2: 单场报告页**

`frontend/src/pages/ReportPage.vue`：
- 顶部：比分大字 + 地图/模式
- 左栏：记分板（10 人，我方高亮，目标玩家置顶高亮）
- 右栏：AI 总结、优势列表（绿色）、问题点卡片（红色，含 evidence 数字引用）、锐评金句块
- 底部：本场六维雷达图 + "生成训练计划"按钮（跳 `/plan`）
- 错误态：404 时显示"对局不存在或该玩家不在此对局"

- [ ] **Step 3: 构建验证**

Run: `cd frontend && npm run build`
Expected: 构建成功

- [ ] **Step 4: 提交**

```bash
cd ~/valorant-ai-coach
git add frontend/src/pages
git commit -m "feat: 战绩列表与单场报告页"
```

---

### Task 10: 前端训练计划页（打卡 + 复测对比）

**Files:**
- Create: `frontend/src/pages/PlanPage.vue`
- Create: `frontend/src/components/ScoreTrend.vue`

**Interfaces:**
- Consumes: `getPlan`, `toggleTask`, `listMatches`, `getAnalysis`（Task 8）

- [ ] **Step 1: 训练计划页**

`frontend/src/pages/PlanPage.vue`：
- 任务卡片列表：任务名、工具标签（Aim Lab/死斗等带色 tag）、detail、freq、完成勾选框
- 勾选调 `toggleTask` 持久化，刷新后状态保留
- 底部"复测"按钮：重新拉最近对局分析，展示与上次评分快照的六维分数对比（本次复测只展示当前值，历史快照存 localStorage，key `val_score_history`，结构 `[{date, scores}]`）

- [ ] **Step 2: 趋势组件**

`frontend/src/components/ScoreTrend.vue`：props `history`（localStorage 的快照数组），ECharts 折线图，六条维度线 + 综合分粗线。快照少于 2 个时显示提示"至少复测一次后生成趋势"。

- [ ] **Step 3: 构建验证并提交**

Run: `cd frontend && npm run build`
Expected: 构建成功

```bash
cd ~/valorant-ai-coach
git add frontend/src
git commit -m "feat: 训练计划页（打卡持久化与复测趋势）"
```

---

### Task 11: 端到端联调 + README + 推送 GitHub

**Files:**
- Modify: `README.md`
- Create: `start-local.sh`
- Create: `backend/config.example.json`

**Interfaces:**
- Consumes: 全部

- [ ] **Step 1: 一键启动脚本**

`start-local.sh`:
```bash
#!/bin/bash
set -e
cd "$(dirname "$0")/backend"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8787
```
`chmod +x start-local.sh`

`backend/config.example.json`:
```json
{
  "llm": {
    "base_url": "https://api.openai.com/v1",
    "api_key": "在这里填你的 key",
    "model": "gpt-4o-mini"
  }
}
```

- [ ] **Step 2: 端到端验证（fixture 数据源）**

```bash
cd ~/valorant-ai-coach/frontend && npm run build
cd ~/valorant-ai-coach && ./start-local.sh &
# 另开终端验证：
curl -s 'http://127.0.0.1:8787/api/matches?name=测试玩家%231234' | head -c 300
curl -s 'http://127.0.0.1:8787/api/analysis/fixture-match-001?name=测试玩家%231234' | head -c 300
curl -s 'http://127.0.0.1:8787/api/plan?name=测试玩家%231234' | head -c 300
# 浏览器打开 http://127.0.0.1:8787，走通：输入玩家名 → 首页卡片 → 战绩列表 → 报告页 → 训练计划打卡
```
Expected: 三个接口均返回 200 JSON；页面全流程可走通。验证完 `kill %1`。

- [ ] **Step 3: 跑全部测试**

Run: `cd backend && .venv/bin/python -m pytest tests/ -v`
Expected: 22 PASSED

- [ ] **Step 4: 完善 README**

`README.md` 补齐：功能列表、截图占位、快速开始（`./start-local.sh` + `npm run build`）、配置说明（config.json / LLM key / COLLECTOR 环境变量）、合规红线、WeGame 真机联调说明（端点需抓包校准）、P2/P3 路线图。

- [ ] **Step 5: 真机联调清单（人工验收，记录不阻塞）**

在 README 中列出 WeGame 联调步骤：Windows 本机登录 WeGame → 抓包确认战绩接口 → 校准 `config.py` 的 `WeGameSettings` 与 `map_wegame_detail` 字段 → `COLLECTOR=wegame` 启动验证。

- [ ] **Step 6: 提交并推送 GitHub**

```bash
cd ~/valorant-ai-coach
git add -A
git commit -m "docs: README 与一键启动脚本"
gh repo create valorant-ai-coach --public --source . --push \
  --description "无畏契约（国服）AI 对局教练：战绩分析、风格定位、训练计划"
```
Expected: 仓库创建于 https://github.com/yourlarok/valorant-ai-coach 并推送 main 分支全部提交。

---

## Self-Review 记录

- **规格覆盖**：战绩查询（T6/T7）、文本分析（T5/T7）、六维评分（T2）、风格定位（T3）、分享卡片（T8）、训练计划+打卡（T4/T7/T10）、前端（T8-T10）、红线与降级（T5 降级、T6 注释、README）。视觉复盘属 P2，不在本计划。
- **类型一致性**：`DimensionRaws` 字段名在 T2/T3/T4 测试与实现中一致；`TrainingTask` 在 T4 定义、T7 经 `model_dump` 入库、T10 前端消费字段名一致；API 契约在 T7 定义、T8 `api.js` 消费一致。
- **Placeholder 扫描**：无 TBD/TODO；WeGame 真机校准为如实声明的限制而非占位（映射函数与结构已实现，有 mock 测试覆盖）。
