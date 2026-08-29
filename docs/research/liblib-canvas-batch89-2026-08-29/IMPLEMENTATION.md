# Batch 89 实施与验证记录

> 状态：`RECORDED_PASS`
>
> 日期：2026-08-29。

## 1. 实施内容

### 1.1 新增机位 command

`directorStore` 新增 `addDirectorCamera`：

- 从当前 active camera 的运行时构图复制 transform、target 和 FOV；
- 用确定性偏移避免新机位与源机位完全重合，并清空 follow/look-at object
  关系；
- 创建唯一 camera object、当前 playhead 的 camera track 和首个 keyframe；
- 更新 `activeCameraId`、唯一对象 selection 和 Timeline selected track；
- 通过 `updateActiveDirectorDocument` 写入 registry/persistence；
- 成功动作只产生一个 `ADD_CAMERA` Director history entry；
- capture、phone recording、motion-path draft、active gesture 和失效 session
  会拒绝或冲突返回，不创建半成品。

selection、playhead、TransformControls 引用仍不进入 portable document；undo/redo
恢复 document 后继续由既有 preserve-and-repair 规则修复 UI selection。

### 1.2 UI 可发现性

- `DirectorObjectTree` 顶部搜索区旁新增图标入口；
- 无对象选择时的 `DirectorInspector` 增加明确的“场景设置”区域；
- 场景设置整理了现有场景名称、ground/grid 显隐、背景颜色和地面颜色；
- 场景属性区域同时提供文字版“新增机位”入口；
- `data-director-*` selector 作为 agent/verifier 稳定入口；
- 没有新增截图，移动端检查区分 panel overflow 与允许横向滚动的 timeline。

### 1.3 证据与边界

| 内容 | 证据等级 |
|---|---|
| 当前 clone 已有 scene/camera/timeline fields | `CLONE_STATIC_FACT` |
| StoryAI scene/camera/add-camera 结构 | `UPSTREAM_INSPIRATION` |
| 新增机位的默认偏移、自动 active、自动 track | `CLONE_DECISION` |
| LibTV 原站 Director 的 exact DOM/CSS/default add-camera policy | `SOURCE_UNKNOWN` |

本批没有重新识别 `docs/design-references` 截图，也没有把 StoryAI 或 clone
结果写成 LibTV source-exact 结论。

## 2. 验证

### 2.1 Pure/source

```bash
node --experimental-strip-types scripts/verify-liblib-batch89.mjs
```

结果：通过，12 项源码/边界断言。

### 2.2 Fresh-page Playwright

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch89.py
```

结果：通过。覆盖：

- scene Inspector settings region；
- object tree / scene Inspector 双入口；
- scene settings field updates；
- ground color updates；
- camera 数量、active camera、object selection、camera track/keyframe；
- 新机位 transform 不重合、关系为空；
- Director undo/redo；
- portable export identity/reference/runtime exclusion；
- mobile tree/Inspector panel overflow；
- console/page/request diagnostics `0 / 0 / 0`。

首次运行发现未限定的双入口 selector 触发 Playwright strict-mode error，随后
按 panel owner 修正 verifier；另确认 workspace 总宽度包含可横向滚动的 timeline，
因此移动端溢出断言限定到 tree/Inspector panel。这两项是 verifier 修正，不是
产品 runtime failure。

### 2.3 其他检查

current-gate 串行结果见 [`current-gate-regression.json`](current-gate-regression.json)。
全量 `npm run check`、`npm run docs:check`、文档验证和 `git diff --check` 的结果
在提交前更新。

## 3. 结果和下一批

Batch 89 完成了 clone-owned scene settings/add-camera 可发现性 slice，但不代表
Director 整体成熟，也不证明 LibTV source parity。下一批优先处理：

- Director project/session authority 的用户可见 project lifecycle；
- scene/object/camera 编辑的 typed command/history 边界；
- scene text/color/toggle 编辑避免逐字符产生语义 history；
- add-camera 后的 active camera、delete fallback 和 multi-shot continuity。
