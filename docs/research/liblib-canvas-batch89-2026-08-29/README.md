# Batch 89：Director 场景设置与新增机位

> 状态：`PLANNED`
>
> 日期：2026-08-29。
>
> 本批是连续五批实施中的第 1 批，目标是补齐 Director 当前最明显的
> scene settings / add-camera 可发现性缺口。

## 入口

- [`PLAN.md`](PLAN.md)：范围、clone-owned 决策和验收标准；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：完成后记录代码、验证和边界；
- [`runtime-audit.json`](runtime-audit.json)：fresh-page Playwright 结构化结果；
- [`current-gate-regression.json`](current-gate-regression.json)：本批 current-gate
  串行结果；
- [`../../storyai-3d-director-desk-2026-08-27/PROGRESS_AUDIT_2026-08-27.md`](../storyai-3d-director-desk-2026-08-27/PROGRESS_AUDIT_2026-08-27.md)：
  上游借鉴评估，不是 LibTV Director 的 source-exact 视觉证据；
- [`../../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)：
  Director project/session/document 边界；
- [`../../../src/store/directorStore.ts`](../../../src/store/directorStore.ts)：
  Director domain state 和 camera/timeline actions；
- [`../../../src/components/director/DirectorObjectTree.tsx`](../../../src/components/director/DirectorObjectTree.tsx)：
  对象树和新增机位入口；
- [`../../../src/components/director/DirectorInspector.tsx`](../../../src/components/director/DirectorInspector.tsx)：
  场景属性和 camera Inspector。

## 证据边界

- `CLONE_STATIC_FACT`：当前 clone 已有 `DirectorScene` 的名称、背景色、地面色、
  ground/grid 显隐，并已有 camera object、camera Inspector、camera track 和
  active camera state。
- `UPSTREAM_INSPIRATION`：StoryAI 的 scene/object/camera 分层和 add-camera
  工作流可用于发现性参考。
- `SOURCE_UNKNOWN`：LibTV 原站 Director 的 authenticated DOM/CSS、默认新增机位
  位置、是否自动切 active camera、是否自动创建 track，当前没有足够证据。
- `CLONE_DECISION`：本批新行为必须标为 clone-owned，不得写成 LibTV 原站事实。

本批不新增截图。执行截图识别前必须先查已有 `SCREENSHOT_ANALYSIS.md`，只有出现
无法用 DOM、状态快照或结构化审计回答的问题时才获取新截图。
