# P1.5 专业化升级设计附录

日期：2026-09-15
状态：已定稿
基线：2026-09-15-valorant-ai-coach-design.md（P1 已实现并推送）

## 背景

P1 验证了管线可行性，但呈现层与 AI 深度不达产品级。本附录定义专业化升级：设计系统、信息架构、AI 分析引擎、报告深度四个方面，目标是对标 tracker.gg / OP.GG 级别的专业应用体验。

## 1. 设计系统

- design tokens：完整色板（含语义色：胜/负/首杀/警告）、字阶（display/h1-h3/body/caption/mono 数据字）、8px 间距体系、圆角/阴影/动效曲线
- 视觉语言：Valorant 风——暗底 #0f1923、战术红 #ff4655、棱角切割装饰（clip-path 斜切）、数据用等宽数字
- 组件库（frontend/src/components/ui/）：UiCard、UiButton、UiTag、UiTable、UiTabs、UiSkeleton、UiEmpty、UiToast
- 布局：左侧导航栏（logo、四个一级模块入口、设置）+ 顶栏（全局玩家搜索 + 数据源/LLM 状态徽标）+ 内容区（最大宽度居中、栅格）

## 2. 信息架构

五个一级页面：

1. **总览 /**：玩家档案卡（段位、RR、主英雄、近 10 场 W/L）、综合评分 + 评级、风格卡（主原型 + 职业哥定位 + 锐评 + 分享）、六维雷达、评分趋势摘要、今日训练待办
2. **战绩 /matches**：筛选栏（地图/英雄/胜负）、按日期分组的对局列表、每场行内展示关键指标（KDA/ACS/HS%/ADR）、批量分析入口
   - 注记：批量分析入口降级至 P2（P1.5 交付时未实现）
3. **单场报告 /report/:matchId**：Tab 结构
   - 战况总览：比分演进、半场对比、关键时刻
   - 记分板与对位：10 人详表（含 ADR/KAST/HS%）、同英雄对位对比
   - 回合分解：回合时间线（每回合胜负/结束方式/目标玩家表现）
   - AI 复盘：多段叙事（总评、逐维度诊断、关键时刻点评）
   - 训练建议：针对本场的问题点与处方
4. **训练中心 /plan**：本周计划卡片、打卡、复测对比、历史趋势图
5. **设置 /settings**：LLM 配置（base_url/key/model 前端可改、运行时生效、保存到本地 config.json）、数据源状态（fixture/wegame）、关于

## 3. AI 分析引擎升级

多段流水线（backend/app/analysis/engine.py）：

1. 数据统计层：从 Match 计算全量指标（含新增 ADR/KAST/手枪局/残局）
2. 基准对比层：与段位基准的分位数对比，生成数据事实清单
3. LLM 叙事层：四段独立 prompt，各自产出结构化 JSON：
   - overview：全局复盘叙事（2-3 段）
   - dimensions：逐维度诊断（六维各一段，引用数字）
   - moments：关键时刻点评（引用具体回合）
   - prescription：训练处方（结合规则库 RULE_TABLE 动态生成，LLM 润色细节与频次）
4. 输出校验：pydantic 校验 + 失败重试一次 + 全链路降级到 Mock provider

**Mock provider 高质量化**（backend/app/analysis/mock_provider.py）：内置贴近真实教练口吻的多段演示输出，基于真实计算指标填充数字（不是硬编码模板），本地无 key 时呈现完整产品形态。

**运行时配置**：设置页保存 LLM 配置写回 backend/config.json，后端立即生效，无需重启。

**周度聚合**（GET /api/analysis/weekly?name=）：近 10 场聚合 → 趋势叙事 + 主要进步/退步维度。

## 4. 数据模型与报告深度

- PlayerMatchStats 扩展：武器击杀分布 weapon_kills: dict[str,int]、技能伤害/辅助 ability_damage/ability_assists、每回合存活 survival_rounds
- RoundResult 扩展：目标玩家该回合击杀数、是否首杀/首死、结束方式
- 新增指标：ADR（场均回合伤害）、KAST（击杀/助攻/存活/交换率）、首杀参与率、手枪局胜率、残局胜率
- fixture 扩充：5 场完整对局（含回合级数据），覆盖胜负不同走势，支撑趋势与聚合演示

## 5. 边界（不变）

- 红线不变：只分析本人及公开数据、凭证本地
- WeGame 真机联调仍是独立人工验收项
- 视觉复盘仍属 P2，不在本次范围
