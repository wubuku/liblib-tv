# 任务优先级与内容结构

## 目录

1. 候选任务来源
2. 用户确认表
3. 优先级和文档厚度
4. `task-inventory.yml`
5. 深度档位

## 1. 候选任务来源

快速扫描时交叉使用以下证据，不以任何单一来源代替用户确认：

- 一级/二级导航、首页快捷入口、空状态 CTA；
- React 路由和权限守卫；
- 现有 Playwright 用例、Mock handlers 和前端 API；
- 产品规划、培训资料、FAQ、客服反馈；
- 用户提供的使用频率、失败案例和角色职责；
- 若用户授权，匿名化产品分析数据。

把多个页面串成一个用户目标。例：

- ✅ “从剧本创建分镜并检查生成结果”
- ❌ “项目页、剧本页、分镜页”

## 2. 用户确认表

在会话中提交，不要在确认前写入手册目录：

```markdown
| 候选任务 | 角色 | 证据与置信度 | 推测频率 | 影响/失败代价 | 建议覆盖 | 请用户确认 |
|---|---|---|---|---|---|---|
| 创建项目并导入剧本 | 创作者 | 首页主 CTA；高 | 核心日常 | 高 | 旗舰流程 | 是/调整 |
```

同时列出三个短问题：

1. 哪些操作是用户每天/每周最常做的？
2. 哪些操作即使低频，做错也会造成费用、数据、发布或权限风险？
3. 哪些功能不应出现在当前手册？

用户可以直接确认提案，也可以明确委托 Agent 定级。没有这两者之一，不进入正式成稿。

## 3. 优先级和文档厚度

### 频率

| 等级 | 含义 |
|---|---|
| 核心日常 | 目标角色反复使用，决定产品主要价值 |
| 常用 | 周期性使用或多数用户必经 |
| 偶发 | 特定阶段、特定角色使用 |
| 罕见 | 配置、迁移、特殊处置 |

### 业务影响

| 等级 | 含义 |
|---|---|
| 关键 | 错误会造成明显费用、数据损失、发布错误、权限风险或不可恢复状态 |
| 高 | 直接阻塞主要业务结果或造成长时间返工 |
| 中 | 可恢复，但会影响效率或理解 |
| 低 | 便利性、偏好或辅助信息 |

### 覆盖决策

| 条件 | 文档厚度 |
|---|---|
| 核心日常 + 任意影响 | 旗舰流程：完整截图、前置条件、成功判据、常见恢复 |
| 常用或高影响 | 完整 how-to：关键步骤截图、明确恢复 |
| 低频 + 关键影响 | 救援路径：不必长，但必须准确、显眼、可恢复 |
| 偶发 + 中低影响 | 简明 how-to 或 reference |
| 罕见 + 低影响 | reference；必要时不进入首版 |

不要按页面平均分配篇幅。低频但关键的恢复/权限/费用任务优先于低价值装饰设置。

## 4. `task-inventory.yml`

确认后创建：

```yaml
manual_version: 1
target:
  app: frameos
  url: 'https://www.frameos.cn/#/canvas/...'
  audience:
    - creator
  depth: standard
tasks:
  - id: create-project
    title: 创建文本节点并接入画布
    role: creator
    frequency: core
    impact: high
    coverage: flagship
    evidence:
      - type: user-confirmed
        note: 新用户和日常创作入口
    preconditions:
      - 已登录
    routes:
      - '#/canvas/:workspaceId/:canvasId'
    status: pending
    manual_pages:
      - 10-tasks/create-project.md
```

`status` 只使用：

- `pending`：尚未开始；
- `in_progress`：正在探索或编写；
- `documented`：正文与截图已完成，尚未完成 Gate B；
- `verified`：已通过真实浏览器回走；
- `excluded`：经用户确认不纳入，并填写 `exclusion_reason`。

机器字段固定使用以下值，中文名称只用于正文展示：

- `frequency`：`core` / `common` / `occasional` / `rare`；
- `impact`：`critical` / `high` / `medium` / `low`；
- `coverage`：`flagship` / `full` / `rescue` / `concise` / `reference`。

Gate A 时所有纳入任务至少为 `documented`；最终交付时只能为 `verified` 或 `excluded`。`documented` /
`verified` 必须填写并实际存在 `manual_pages`；截图的 `task_id` 必须引用这里的任务 ID。`core` 或
`flagship` 任务至少有一张登记在 Manifest 中的正式截图。

每次增量更新只重做受影响任务，保留未变化任务的截图和验证记录。

## 5. 深度档位

深度决定总覆盖，不改变优先级：

| 深度 | 建议范围 |
|---|---|
| quick | 5–10 个已确认核心任务；单份快速上手 |
| standard | 全部一级业务域、核心/常用任务、关键参考 |
| thorough | 所有主要角色、CRUD、空/错/恢复状态、关键移动端 |
| exhaustive | 可发布文档套件，含管理员、权限差异、完整参考、FAQ 和可选 HTML/PDF |

默认 `standard`。若用户没有说明受众、权限或环境，先问清楚，不凭路由数量推断。
