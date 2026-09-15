# P1.5 专业化升级实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 P1 管线验证版升级为专业级应用：设计系统 + 五页信息架构 + 多段 AI 分析引擎 + 深度报告数据模型。

**Architecture:** 沿用 FastAPI+SQLite / Vue3 栈。后端扩展 schema 与指标、新增多段分析引擎与 Mock provider；前端新建 design tokens 与 UI 组件库后逐页重构。

**Tech Stack:** 不变（Python 3.11+/FastAPI/pydantic v2/pytest；Vue 3/Vite/ECharts）。

**规格附录:** docs/superpowers/specs/2026-09-15-p15-professional-upgrade-design.md

## Global Constraints

- 沿用 P1 全局约束（中文 conventional commits、凭证本地、红线不变）
- 后端所有新指标必须有单元测试；不得发起真实网络请求
- 前端所有页面必须使用 design tokens 与 UI 组件库，禁止散写裸样式
- 既有 24 个后端测试必须保持绿色（schema 扩展用默认值保证向后兼容）
- 每任务收尾跑全量后端测试或前端 build

---

### Task 1: 数据模型扩展 + 指标扩充 + 多场 fixture

**Files:**
- Modify: `backend/app/schemas.py`（PlayerMatchStats/RoundResult 扩展，全部带默认值向后兼容）
- Modify: `backend/app/analysis/metrics.py`（新增指标计算函数）
- Create: `backend/tests/fixtures/match_002.json` 至 `match_005.json`（4 场新 fixture，13:7 胜、11:13 负、13:13 加时胜、5:13 负，含回合级数据）
- Modify: `backend/tests/fixtures/match_sample.json`（补齐新字段）
- Create: `backend/tests/test_extended_metrics.py`

**Interfaces:**
- Produces:
  - `PlayerMatchStats` 新增：`weapon_kills: dict[str,int] = {}`、`ability_damage: int = 0`、`ability_assists: int = 0`、`survival_rounds: int = 0`、`clutch_wins: int = 0`、`clutch_attempts: int = 0`
  - `RoundResult` 新增：`player_kills: int = 0`（目标玩家该回合击杀）、`player_first_blood: bool = False`、`player_first_death: bool = False`、`pistol: bool = False`
  - `extended_stats(matches: list[Match], player_name: str) -> ExtendedStats`（metrics.py），`ExtendedStats(BaseModel)`：`adr: float`（damage_made 总和/总回合）、`kast: float`（(击杀或助攻或存活回合数)/总回合）、`fb_participation: float`（first_bloods/总回合）、`pistol_wr: float`、`clutch_wr: float`（clutch_wins/clutch_attempts，0 场次时为 None）
  - 5 场 fixture 玩家名统一为 `测试玩家#1234`，指标各不相同以支撑趋势演示

**Steps:**
- [ ] 扩展 schemas.py（新字段全部带默认值，保证旧 fixture/测试兼容）
- [ ] 写 test_extended_metrics.py：adr/kast/fb_participation/pistol_wr/clutch_wr 各至少一个断言（基于 match_sample.json 补齐字段后的已知值）
- [ ] 确认失败 → 实现 extended_stats → 全绿
- [ ] 补齐 match_sample.json 新字段并编写 match_002~005（回合数与比分一致、字段完整、指标有区分度）
- [ ] 全量测试（原 24 + 新增）绿色后提交 `feat: 扩展数据模型与深度指标`

---

### Task 2: AI 分析引擎升级（多段流水线 + Mock provider + 运行时配置 + 周度聚合）

**Files:**
- Create: `backend/app/analysis/engine.py`
- Create: `backend/app/analysis/mock_provider.py`
- Modify: `backend/app/analysis/prompts.py`（四段 prompt）
- Modify: `backend/app/config.py`（配置可写回）
- Modify: `backend/app/routes/analysis.py`（改用 engine；新增 weekly）
- Create: `backend/app/routes/settings.py`（GET/PUT /api/settings/llm）
- Create: `backend/tests/test_engine.py`

**Interfaces:**
- Consumes: `extended_stats`（Task 1）、既有 metrics/rules/planner
- Produces:
  - `DeepAnalysis(BaseModel)`：`overview: str`、`dimensions: dict[str, str]`（六维 key → 诊断段落）、`moments: list[str]`、`prescription: list[TrainingTask]`、`roast: str`
  - `analyze_deep(match, player_name, raws, ext: ExtendedStats, primary, subs, problems, llm) -> DeepAnalysis`（engine.py）
  - `MockProvider`：实现与 LLMClient 相同的 `chat(system, user) -> str` 与 `is_configured() -> bool`（恒 True）；chat 内根据 system prompt 类型返回基于真实指标填充的高质量演示 JSON
  - `GET /api/analysis/{match_id}` 响应新增 `deep: DeepAnalysis` 与 `ext: ExtendedStats` 字段（保留原字段兼容）
  - `GET /api/analysis/weekly?name=` → `{narrative: str, improved: list[str], regressed: list[str], games: int}`
  - `GET /api/settings/llm` → `{base_url, model, configured: bool}`（不返回 key 本体）；`PUT /api/settings/llm` body `{base_url, api_key, model}` → 写回 backend/config.json 并热更新 app.state.llm
  - LLM 选择逻辑：api_key 已配置 → LLMClient；否则 → MockProvider（is_configured 恒 True，产物标注 `"mock": true`）

**Steps:**
- [ ] test_engine.py：MockProvider 各段输出可被 DeepAnalysis 校验；analyze_deep 在 MockProvider 下产出完整结构；LLM 返回非法 JSON 时重试一次后回退 mock；weekly 端点聚合 5 场 fixture 返回 narrative
- [ ] 确认失败 → 实现 mock_provider.py / engine.py / prompts.py 四段 → settings 路由 → 全绿
- [ ] 全量测试绿色后提交 `feat: 多段 AI 分析引擎与高质量 Mock 通道`

---

### Task 3: 设计系统 + UI 组件库 + 布局重构

**Files:**
- Modify: `frontend/src/style.css`（完整 design tokens）
- Create: `frontend/src/components/ui/UiCard.vue`、`UiButton.vue`、`UiTag.vue`、`UiTable.vue`、`UiTabs.vue`、`UiSkeleton.vue`、`UiEmpty.vue`、`UiToast.vue`
- Create: `frontend/src/components/ui/index.js`
- Modify: `frontend/src/App.vue`（左侧导航 + 顶栏 + 内容区布局）
- Modify: `frontend/src/router.js`（新增 /settings 路由；占位 SettingsPage 由 Task 6 填充，先建占位）

**Interfaces:**
- Produces: tokens CSS 变量全集（语义色 `--c-win/--c-loss/--c-firstblood`、字阶 `--fs-display` 等、间距 `--sp-1..8`、动效 `--ease-out`）；UI 组件统一 `Ui*` 前缀；App 布局插槽；Toast 用 provide/inject（`useToast()`）

**Steps:**
- [ ] 重写 style.css tokens（Valorant 视觉语言：暗底、战术红、clip-path 斜切装饰类、等宽数字类 `.num`）
- [ ] 八个 UI 组件（props/slots 最小可用，样式只引用 tokens）
- [ ] App.vue 布局重构：左侧导航（总览/战绩/训练中心/设置）+ 顶栏（玩家搜索 + LLM 状态徽标）+ 内容区
- [ ] `npm run build` 通过后提交 `feat: 设计系统与 UI 组件库、应用布局重构`

---

### Task 4: 总览 Dashboard 重构

**Files:**
- Modify: `frontend/src/pages/HomePage.vue`（重写为 Dashboard）
- Create: `frontend/src/components/PlayerCard.vue`、`TrendMini.vue`
- Modify: `frontend/src/components/ShareCard.vue`（接入新 tokens，视觉升级）

**Interfaces:**
- Consumes: Task 3 组件库、`/api/analysis/weekly`（Task 2）、既有 API
- Produces: Dashboard 区块：PlayerCard（段位/RR/主英雄/近10场W-L）、评分+评级大数字、ShareCard（风格称号+职业哥定位+锐评）、雷达图、TrendMini（近5场评分迷你折线）、今日训练待办（取 plan 前 3 项未完成）

**Steps:**
- [ ] PlayerCard / TrendMini 组件
- [ ] HomePage 重写为分区 Dashboard 栅格布局（骨架屏加载态、空态引导）
- [ ] ShareCard 视觉升级（斜切装饰、字阶、评级角标）
- [ ] build 通过后提交 `feat: 总览 Dashboard 重构`

---

### Task 5: 战绩中心 + 单场报告重构

**Files:**
- Modify: `frontend/src/pages/MatchesPage.vue`（筛选 + 分组 + 行内指标）
- Modify: `frontend/src/pages/ReportPage.vue`（Tab 结构重写）
- Create: `frontend/src/components/RoundTimeline.vue`、`MatchupBoard.vue`

**Interfaces:**
- Consumes: UI 组件库、Task 2 的 deep/ext 字段、Task 1 的回合级数据
- Produces:
  - MatchesPage：地图/英雄/胜负筛选、按日期分组、行内 KDA/ACS/HS%/ADR
  - ReportPage 五个 Tab：战况总览（比分演进条、半场对比、关键时刻列表）/ 记分板与对位（MatchupBoard：10 人详表 + 同英雄对位）/ 回合分解（RoundTimeline）/ AI 复盘（deep.overview + dimensions + moments 排版）/ 训练建议（deep.prescription + problems）

**Steps:**
- [ ] RoundTimeline / MatchupBoard 组件
- [ ] MatchesPage 重构（筛选、分组、指标列）
- [ ] ReportPage Tab 化重构（UiTabs，五个 Tab 内容齐整，骨架屏与错误态保留）
- [ ] build 通过后提交 `feat: 战绩中心与单场报告深度重构`

---

### Task 6: 训练中心 + 设置页

**Files:**
- Modify: `frontend/src/pages/PlanPage.vue`（视觉重构进组件库）
- Create: `frontend/src/pages/SettingsPage.vue`

**Interfaces:**
- Consumes: `/api/settings/llm` GET/PUT（Task 2）、UI 组件库
- Produces: PlanPage 分区（本周计划/复测对比/历史趋势）；SettingsPage（LLM 表单：base_url/key/model + 保存按钮 + configured 状态徽标；数据源状态展示；红线声明展示）

**Steps:**
- [ ] PlanPage 视觉重构（功能不变，打卡/复测/趋势接入新组件）
- [ ] SettingsPage：表单、保存（PUT）、状态展示；保存成功 Toast 提示
- [ ] build 通过后提交 `feat: 训练中心重构与设置页`

---

### Task 7: 端到端联调 + README + 推送

**Files:**
- Modify: `README.md`

**Steps:**
- [ ] 前端 build + 全量后端测试
- [ ] fixture 通道起服务，curl 验证新端点（analysis 含 deep/ext、weekly、settings GET/PUT 往返）
- [ ] README 更新（新页面结构、Mock 通道说明、设置页配置 LLM 方式）
- [ ] 提交 `docs: P1.5 专业化升级文档` 并 `git push`（已获授权）

---

## Self-Review 记录

- 规格附录覆盖：设计系统（T3）、信息架构五页（T4/T5/T6）、AI 引擎（T2）、数据深度（T1）、联调推送（T7）
- 类型一致性：ExtendedStats 字段在 T1 定义、T2/T5 消费；DeepAnalysis 在 T2 定义、T5 消费；设置 API 在 T2 定义、T6 消费
- Placeholder 扫描：无 TBD；回合级 fixture 数值由实现者构造但受"比分与回合一致"硬约束
