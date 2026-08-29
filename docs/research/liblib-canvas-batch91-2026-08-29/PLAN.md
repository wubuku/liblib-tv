# Batch 91 计划：Director 对象、相机与分组 command/history 收口

> 状态：`RECORDED_PASS`
>
> 日期：2026-08-29。

## 1. 背景

Batch 90 已将 scene mutation 提升为带 owner/session、persistence 和
Director-local history 的 semantic command，但 `updateObject`、
`updateCamera`、group rename/transform 和 character group creation 仍有
direct writer。它们可能让 React UI 短暂显示新值，却缺少统一的 stale、
invalid、no-op、persistence 和 history 结果。

## 2. 本批目标

- 为对象属性、相机设置、分组创建/重命名/变换建立统一 command 边界；
- 保证有效 mutation 最多一条 Director history；
- 保证 invalid/no-op/stale 不产生部分 mutation 或 history；
- 保持 `authoredObjects` 为 portable baseline，`objects` 为 runtime projection；
- 将对象名和分组名改为本地 draft，Enter/blur 才提交；
- 新增 pure/source 与 fresh-page Playwright verifier；
- 更新 current manifest、台账和项目导航，并 commit/push。

## 6. 结果

- [x] 实施统一 `commitDirectorMutation` boundary；
- [x] 迁移对象属性、相机设置、角色组创建/重命名/变换；
- [x] 对象名和分组名改为 draft + Enter/blur commit；
- [x] 运行 Batch 91 pure/source 与 fresh-page Playwright verifier；
- [x] 运行 Batch 88-90 changed-slice regression；
- [x] 更新 current manifest、台账和项目导航；
- [x] commit/push Batch 91 checkpoint。

## 3. 范围

| Slice | 本批处理 |
|---|---|
| 对象属性 | `name`、`color`、`visible`、`locked` |
| 相机 | FOV、target、look-at、follow target/offset/view |
| 分组 | character group create、label draft/commit、group transform |
| 不包含 | 普通 LibTV graph、FrameOS、remote provider、LibTV source-exact Director DOM |

## 4. 约束

- locked object/member 必须保持 zero document/history mutation；
- 相机不能引用自身、缺失对象或 camera 作为 target；
- 不把 StoryAI、Open Canvas 或 clone-only semantics 写成 LibTV 原站事实；
- 活动 TransformControls/Inspector gesture 中只更新 transient projection，
  由 gesture commit 产生一条 history；
- 不新增截图，优先使用已有结构化 evidence 与 DOM/state verifier。

## 5. 验收矩阵

| 场景 | 预期 |
|---|---|
| object name draft | 连续输入 zero history，Enter/blur 一条 `UPDATE_OBJECT` |
| object visibility | canonical authored/runtime、persistence、history 同步 |
| camera FOV | 一条 `UPDATE_CAMERA`，timeline keyframe 连续 |
| camera same value | `NOOP`，zero history |
| camera invalid reference | `DIRECTOR_REFERENCE_INVALID`，zero mutation |
| group create | 一条 `GROUP_CHARACTERS`，selection/registry/persistence 同步 |
| group name draft | 连续输入 zero history，Enter/blur 一条 `UPDATE_GROUP` |
| group transform | 一条 `UPDATE_GROUP_TRANSFORM`，invalid scale 被拒绝 |
| diagnostics | console/page/request error 均为 0 |
