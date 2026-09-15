# 无畏契约 AI 对局教练

分析本人《无畏契约》（国服）对局数据的本地工具：拉取战绩 → 六维能力评分 → 风格定位 → AI 复盘点评 → 生成针对性训练计划并打卡追踪。所有数据保存在本地 SQLite，不对外上传。

## 红线声明（合规）

- 仅分析**本人账号**的对局数据及公开数据；
- 所有凭证（LLM API Key、WeGame Cookie 等）只保存在本地 `backend/config.json`，不上传、不分享；
- 不注入、不修改游戏客户端，不读取游戏内存，仅通过战绩接口获取事后数据；
- 不用于任何违反游戏规则与平台条款的用途（代练、演员行为分析他人等）。

## 功能列表（P1.5 专业化版）

- **战绩查询**：对局列表与单场详情（Fixture 演示数据 / WeGame 数据源可切换）；
- **六维能力评分**：瞄准、对枪、意识、经济、道具、稳定性六个维度打分并给出总评与等级（S/A/B/C/D）；
- **扩展数据指标**：ADR、KAST、首杀参与率、手枪局胜率、Clutch 胜率等职业级指标，逐场与多场聚合；
- **风格定位**：基于数据匹配风格原型（如"爆头机器""敢死队"），含副标签；
- **分享卡片**：总览页生成风格分享卡片，可一键保存为图片；
- **AI 深度复盘**：五段结构化输出——总览、逐维诊断、关键时刻、改进处方、风格锐评；未配置 key 或 LLM 异常时自动降级为内置 Mock 分析，功能不中断；
- **周报聚合**：近 10 场叙事总结、进步/退步维度对比；
- **训练计划**：根据检测到的问题生成针对性训练任务（如爆头率偏低 → Aim Lab 专项），支持打卡持久化与复测趋势；
- **设置页**：页面上直接配置 LLM（base_url / api_key / model），保存即热更新，无需手写配置文件。

## 页面结构

- **总览**（`/`）：风格卡片、六维雷达、近期趋势与周报摘要；
- **战绩**（`/matches`）：对局列表，含扩展指标带与记分板入口；
- **单场报告**（`/report/:matchId`）：五个 Tab——战况总览 / 记分板与对位 / 回合分解 / AI 复盘 / 训练建议；
- **训练中心**（`/plan`）：训练任务打卡与复测趋势；
- **设置**（`/settings`）：LLM 配置与数据源状态。

## 技术栈

- 后端：FastAPI + SQLite（`backend/`，39 个 pytest 测试）
- 前端：Vue 3 SPA（`frontend/`，Vite 构建，产物由后端托管）

## 快速开始

```bash
# 1. 构建前端
cd frontend && npm install && npm run build && cd ..

# 2. 一键启动（自动建 venv、装依赖、起 uvicorn，托管前端 dist）
./start-local.sh

# 3. 浏览器打开
open http://127.0.0.1:8787
```

默认使用 Fixture 演示数据源（内置玩家 `测试玩家#1234`，5 场完整对局），开箱即可走通全流程：
总览 Dashboard → 战绩列表 → 单场报告五 Tab → 训练中心打卡 → 设置页配置 LLM。

### Mock 演示通道

未配置 LLM key 时，所有 AI 输出由内置 Mock Provider 生成（结构完整、内容确定，响应中带 `mock: true` 标记），便于演示与前端联调；配置真实 key 后自动切换为真实 LLM 输出。

<!-- 截图占位：首页 / 报告页 / 训练计划页 -->

## 配置说明

**推荐方式：打开应用后进入"设置"页**，直接填写 LLM 的 `base_url` / `api_key` / `model`，保存即写入 `backend/config.json` 并热更新生效，无需重启服务。设置接口不会回显 api_key 明文。

**默认内置 DeepSeek**：`base_url` 默认指向 `https://api.deepseek.com/v1`，模型默认 `deepseek-chat`（DeepSeek 快速模型，价格便宜适合高频分析）。只需提供一个 DeepSeek API key 即可开箱使用，提供方式三选一：

1. 设置页填写（推荐）；
2. 环境变量 `DEEPSEEK_API_KEY`（优先级高于空配置）；
3. 手动编辑 `backend/config.json`（不存在时使用默认值），参考 `backend/config.example.json`：

```json
{
  "llm": {
    "base_url": "https://api.deepseek.com/v1",
    "api_key": "在这里填你的 DeepSeek key",
    "model": "deepseek-chat"
  }
}
```

- **LLM**：兼容 OpenAI Chat Completions 协议的任意服务均可（改 `base_url` 与 `model` 即可换其他模型）。不填 `api_key` 时文本分析自动使用内置 Mock 降级，结构保持一致。
- **数据源**：环境变量 `COLLECTOR` 控制采集器——
  - `COLLECTOR=fixture`（默认）：读取 `backend/tests/fixtures/` 演示数据；
  - `COLLECTOR=wegame`：走 WeGame 战绩接口（需先完成下方真机联调校准）。

## WeGame 真机联调清单（人工验收）

WeGame 端点结构与字段映射已实现并有 mock 测试覆盖，但真实端点**需要抓包校准**后方可使用：

1. Windows 本机登录 WeGame，进入无畏契约战绩页；
2. 抓包确认战绩列表 / 对局详情的真实请求 URL、参数与鉴权方式（Cookie / token）；
3. 校准 `backend/app/config.py` 中 `WeGameSettings` 的 `base_url` / `match_list_path` / `match_detail_path`；
4. 校准 `backend/app/collector/wegame.py` 中 `map_wegame_detail` 的字段映射，使其与真实响应一致；
5. `COLLECTOR=wegame ./start-local.sh` 启动，用本人账号验证战绩拉取与分析链路。

## 测试

```bash
cd backend && .venv/bin/python -m pytest tests/ -v   # 预期 39 passed
cd frontend && npm run build                          # 预期构建成功
```

## 路线图

- **P2**：视觉复盘（回合时间线、站位热力图）、历史趋势分析、多赛季对比；
- **P3**：更多风格原型与精细化标签、训练计划自适应调整、移动端适配。

## 目录结构

```
backend/            FastAPI 后端
  app/analysis/     LLM 客户端、Mock Provider、五段深度复盘引擎、扩展指标
  app/coaching/     评分引擎、风格原型、规则库、训练计划
  app/collector/    Fixture / WeGame 采集器
  app/routes/       matches / analysis / coaching / settings API
  tests/            39 个 pytest 测试 + fixtures
frontend/           Vue 3 SPA（构建产物由后端托管）
  src/pages/        总览 / 战绩 / 报告（五 Tab）/ 训练中心 / 设置
  src/components/   雷达图、记分板、回合时间线、分享卡片 + ui/ 组件库
start-local.sh      一键启动脚本
```
