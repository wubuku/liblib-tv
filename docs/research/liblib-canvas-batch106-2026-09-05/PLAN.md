# Batch 106 Plan：项目菜单（logo 下拉）对齐 2026-09-05 源站

> 状态：`PLANNED`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 105（`batch/105-follow-banner`）。
>
> 源站证据：2026-09-05 补采样（logo chevron 下拉：回到主页/全部项目/创建新项目/删除项目，分组分隔线；Escape 不关闭——观察记录已归档审计 §11 交互备注）。

## 1. 范围

### 包含

1. **项目菜单**（`SOURCE_FACT` 结构 + `CLONE_DECISION` 行为）：顶栏 logo 旁 chevron 触发 `data-project-menu`，四项 `回到主页/全部项目/创建新项目/删除项目`（2/2 分组带分隔线）；各项点击写本地 status `本地原型：{item}未接入`，不接路由/项目服务。
2. 开合：chevron 切换；outside-click 关闭；Escape 不注册（与源站观察一致，避免动 batch62 契约）。
3. **保留** logo Link → FrameOS（clone 开发导航，非源站行为，标题明确标注）。

### 不包含

- 回到主页/全部项目路由、创建/删除项目服务；
- 教程 popover（clone 已是源站四项命名，本批仅以 verifier 锁定）。

## 2. 证据边界

| 标签 | 内容 |
|---|---|
| `SOURCE_FACT` | 菜单存在、四项命名与 2/2 分组、锚定 logo 下拉 |
| `CLONE_DECISION` | 各项本地 status、chevron 触发样式、保留 FrameOS Link |
| `SOURCE_UNKNOWN` | 四项真实跳转/确认流（删除项目确认等）、菜单精确几何 |

## 3. 验证

- 新增 `scripts/verify-liblib-batch106.py`：desktop `1440x900`，断言触发/四项/分组线、status 本地反馈、outside 关闭、教程 popover 四项、零诊断。
- 复跑 `verify-liblib-batch11.py`（overlay 互斥）。
- `npm run check`、`npm run docs:check`。

## 4. 完成定义

1. 项目菜单与源站命名/分组一致。
2. 相邻 verifier 与全量检查通过；特性分支 commit/push。
