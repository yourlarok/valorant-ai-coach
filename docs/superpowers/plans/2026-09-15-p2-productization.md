# P2 产品化实施计划：Onboarding 自动化 + 内置训练场

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完整产品流程（首次引导 + 自动化分析 + 通知中心）与内置瞄准训练场（三个 Valorant 专项科目 + 成绩闭环）。

**Architecture:** 后端加 asyncio 轮询自动化引擎 + 通知/训练成绩存储（SQLite 新表）；前端加 Onboarding 向导、通知中心、Canvas 训练场框架。沿用既有设计系统与组件库。

**Tech Stack:** 不变（FastAPI/SQLite/pydantic；Vue 3/Canvas/ECharts），无新依赖。

**规格附录:** docs/superpowers/specs/2026-09-15-p2-productization-design.md

## Global Constraints

- 沿用全局约束：中文 conventional commits、凭证本地、无新依赖、后端测试无真实网络请求
- 全部走设计系统 tokens 与 UI 组件库
- 既有 39 后端测试保持绿；前端 build 必须过
- 自动化必须可取消（开关 + 单条通知可忽略）

---

### Task 1: 通知系统 + 玩家档案 API + 自动化引擎（后端）

**Files:**
- Modify: `backend/app/db.py`（notifications 表、profile 缓存表）
- Create: `backend/app/notifications.py`（通知模型与存取）
- Create: `backend/app/automation.py`（asyncio 轮询器）
- Create: `backend/app/routes/notifications.py`
- Modify: `backend/app/routes/matches.py`（新增 GET /api/profile?name=）
- Modify: `backend/app/main.py`（挂载路由、启停轮询器）
- Modify: `backend/app/config.py`（Settings 加 `automation: AutomationSettings`）
- Create: `backend/tests/test_automation.py`

**Interfaces:**
- Produces:
  - `Notification(BaseModel)`：`id: int, type: str, title: str, body: str, link: str, read: bool, created_at: datetime`
  - `GET /api/notifications?unread_only=false` → `{items: list[Notification], unread: int}`；`POST /api/notifications/{id}/read`；`POST /api/notifications/read-all`
  - `GET /api/profile?name=` → `{name, rank_tier, rr, main_agents: list[str], recent: {games, wins, avg_acs, avg_hs}}`（从已采集对局聚合）
  - `AutomationEngine`：`start(app)`/`stop()`；发现新对局 → 自动 analyze_deep → 写通知（link 到报告页）；对 FixtureCollector 不做轮询（数据静态），改用 dev 端点 `POST /api/dev/simulate-new-match`（随机复制一场 fixture 改 match_id 与时间）触发同一条自动化链路供演示
  - `AutomationSettings(BaseModel)`：`enabled: bool = True, poll_interval_min: int = 5`；设置页可读改

**Steps:**
- [ ] test_automation.py：通知 CRUD（写/读/标记已读/未读数）；profile 聚合基于 5 场 fixture 的已知值断言；自动化链路：模拟新对局 → 断言产生一条 type=analysis_done 的通知且 link 指向 /report/<id>
- [ ] 失败 → 实现 → 全绿（既有 39 + 新增）
- [ ] 提交 `feat: 通知系统、玩家档案与自动化分析引擎`

---

### Task 2: 训练成绩 API（后端）

**Files:**
- Modify: `backend/app/db.py`（training_scores 表）
- Create: `backend/app/routes/training.py`
- Create: `backend/tests/test_training.py`

**Interfaces:**
- Produces:
  - `POST /api/training/scores` body `{player: str, drill: str, score: float, extra: dict = {}}` → `{ok: true, best: float, is_record: bool}`
  - `GET /api/training/scores?player=&drill=` → `{scores: [{drill, score, extra, created_at}], bests: dict[str, float]}`
  - drill 枚举：`headline_flick / reaction / tracking`

**Steps:**
- [ ] test_training.py：写入成绩返回历史最佳与 is_record 标记；按科目分组查询
- [ ] 失败 → 实现 → 全绿
- [ ] 提交 `feat: 训练场成绩存储与 API`

---

### Task 3: Onboarding 向导 + 身份绑定改造（前端）

**Files:**
- Create: `frontend/src/pages/OnboardingPage.vue`
- Modify: `frontend/src/router.js`（/onboarding 路由 + 全局守卫）
- Modify: `frontend/src/player.js`（绑定状态走后端：新增 GET/POST /api/identity）
- Modify: `backend/app/routes/settings.py` 或新 `backend/app/routes/identity.py`（identity 存 config.json）
- Modify: `frontend/src/App.vue`（顶栏显示已绑定身份，向导外才显示导航）

**Interfaces:**
- Consumes: 组件库、profile API（Task 1）
- Produces: `GET /api/identity` → `{name: str | null, onboarded: bool}`；`POST /api/identity` body `{name}` → 校验玩家存在（collector 查得到对局）→ 保存。路由守卫：未 onboarded 一律重定向 /onboarding

**Steps:**
- [ ] 后端 identity 端点 + 测试（绑定合法玩家成功、不存在玩家 404）
- [ ] OnboardingPage 三步向导（产品介绍 / 绑定身份 / 自动化授权说明与开关）
- [ ] router 守卫 + App.vue 顶栏身份显示
- [ ] build 通过 → 提交 `feat: 首次引导向导与身份绑定`

---

### Task 4: 通知中心 + 自动化开关（前端）

**Files:**
- Create: `frontend/src/components/NotificationBell.vue`
- Modify: `frontend/src/App.vue`（顶栏挂铃铛）
- Modify: `frontend/src/pages/SettingsPage.vue`（自动化开关区）
- Modify: `frontend/src/api.js`

**Interfaces:**
- Consumes: Task 1 通知 API、settings API
- Produces: 顶栏铃铛（未读红点、30s 轮询未读数、下拉面板列出通知、点击跳 link 并标记已读、"全部已读"按钮）；设置页自动化区（enabled 开关 + 轮询间隔 + fixture 模式下的"模拟新对局"演示按钮）

**Steps:**
- [ ] NotificationBell 组件（下拉面板、未读标记、跳转）
- [ ] SettingsPage 自动化区
- [ ] build 通过 → 提交 `feat: 通知中心与自动化开关`

---

### Task 5: 训练场框架 + 爆头线定位科目（前端）

**Files:**
- Create: `frontend/src/pages/RangePage.vue`（训练场主页）
- Create: `frontend/src/components/range/DrillShell.vue`（Canvas 游戏外壳：倒计时、开始/结束、成绩卡）
- Create: `frontend/src/components/range/HeadlineFlick.vue`
- Modify: `frontend/src/router.js`（/range 路由）、`frontend/src/App.vue`（导航加训练场）

**Interfaces:**
- Consumes: Task 2 成绩 API
- Produces: `DrillShell` props `{drill: string, title: string, duration: number}`，slot 为游戏画布区，emits `finish(result: {score: number, extra: object})`；内置成绩卡（本次/历史最佳/是否新纪录）与"再来一局"

**Steps:**
- [ ] DrillShell：Canvas 渲染循环、3-2-1 倒计时、结束成绩卡、成绩上报 POST /api/training/scores
- [ ] HeadlineFlick：目标只出现在画布上部爆头线高度带随机水平位置，点击命中即刷新下一个，60 秒计"命中数×命中率- miss 惩罚"为 score，extra 记平均反应 ms
- [ ] RangePage：三科目卡片入口（flick 可用，另两个"即将上线"占位）
- [ ] build 通过 → 提交 `feat: 训练场框架与爆头线定位科目`

---

### Task 6: 反应 + 跟枪科目 + 训练计划联动（前端）

**Files:**
- Create: `frontend/src/components/range/ReactionDrill.vue`、`TrackingDrill.vue`
- Modify: `frontend/src/pages/RangePage.vue`（三科目全开 + 各科最近/最佳成绩 + 迷你趋势）
- Modify: `frontend/src/pages/PlanPage.vue`（计划任务带"去训练场"跳转链接，按 dimension 映射科目）

**Interfaces:**
- Consumes: DrillShell（Task 5）、成绩 API（Task 2）
- Produces: ReactionDrill（变色即点，5 轮取平均 ms 为 score，越低越好）；TrackingDrill（目标正弦变速移动 45 秒，准星覆盖时间占比为 score）；dimension→drill 映射表（aim→headline_flick, duel→reaction, consistency→tracking）

**Steps:**
- [ ] 两个科目实现（注意 score 语义：reaction 低分为优，成绩卡与趋势要正确处理方向）
- [ ] RangePage 成绩区（每科目最近 5 次迷你趋势）
- [ ] PlanPage 任务卡跳转映射
- [ ] build 通过 → 提交 `feat: 反应与跟枪科目、训练计划联动`

---

### Task 7: 端到端联调 + README + 推送

**Steps:**
- [ ] 全量后端测试 + 前端 build
- [ ] fixture 通道联调：onboarding 全流程（清状态 → 向导 → 绑定"测试玩家#1234" → Dashboard）、模拟新对局 → 通知出现 → 点击进报告、训练场三科目各跑一局验证成绩入库与趋势
- [ ] README 更新（产品流程、训练场、自动化）
- [ ] 提交 `docs: P2 产品化文档` 并推送

---

## Self-Review 记录

- 规格附录覆盖：onboarding（T3）、自动化+通知（T1/T4）、训练场三科目（T2/T5/T6）、联调推送（T7）
- 类型一致性：Notification/TrainingScore 契约在 T1/T2 定义、T4/T5/T6 消费；identity API 在 T3 内自闭环
- Placeholder 扫描：无 TBD
