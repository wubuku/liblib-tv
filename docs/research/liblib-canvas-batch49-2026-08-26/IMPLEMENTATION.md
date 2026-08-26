# Batch 49 实施记录

> 状态：已完成（2026-08-26）。本批是 clone-owned 的有界 Director
> 视口合同，不是当前 LibTV authenticated source 的 renderer/CSS 证明。

## 保护上下文

- 计划：[`PLAN.md`](PLAN.md)
- 证据：[`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)
- 上游考古：[`UPSTREAM_ARCHAEOLOGY.md`](UPSTREAM_ARCHAEOLOGY.md)
- 行为契约：[`DIRECTOR_VIEWPORT_GIZMO.spec.md`](DIRECTOR_VIEWPORT_GIZMO.spec.md)
- 上一批收口：[`../liblib-canvas-batch48-2026-08-26/IMPLEMENTATION.md`](../liblib-canvas-batch48-2026-08-26/IMPLEMENTATION.md)

## 进度

- [x] 回顾 Batch 48 成熟度和 Director 现有缺口
- [x] 固定上游坐标控件代码考古
- [x] Batch 49 计划、证据和契约
- [x] 主视口相机 snapshot bridge
- [x] 独立 R3F gizmo overlay 和六方向命中层
- [x] focused Playwright 与一次截图视觉分析
- [x] 成熟度、覆盖矩阵、验证台账和研究导航
- [x] 跨批回归、`docs:check`、`npm run check`
- [x] 精确 commit/push

## 尚未实施的明确决策

- 不引入真实模型 loader；
- 不把 gizmo 作为 timeline/camera-object mutation；
- 不把 `docs/design-references/` 整体加入 ignore；
- 不改变普通 LibTV 画布和 FrameOS 路由。

## 实施内容

### 视口同步与方向命令

- `DirectorCameraSnapshotBridge` 以低频快照把 R3F 主相机的
  `position/target/fov` 投影到 clone-local 纯数据；
- 方向命中使用 `target + normalize(axis) * radius` 生成新的 Director
  视角，不写入 `directorStore.objects`、选中态、timeline 或 active
  camera；
- Camera mode 点击方向后先回到 Director mode，再应用方向快照；
- `OrbitControls` 以方向命令重新初始化，确保旧 spherical state 不会把
  相机拉回旧位置；
- `maxPolarAngle` 放开到 `Math.PI`，因此 Y 反向视角不会被极角限制吞掉。

### Overlay 与命中层

- 视觉层使用独立的 `Canvas`、`GizmoHelper` 和 `GizmoViewport`；
- 语义层使用六个稳定的 15×15px DOM button，按钮位置由 gizmo camera
  投影计算，深度由 projected z 转换为 `z-index`；
- 命中层只覆盖 80×80px gizmo 区域，不拦截主视口空白点击和场景 pointer；
- overlay 在视口内做边界约束，保持 desktop/mobile 不溢出；
- capture/export 时卸载；path drawing 和 phone recording 时保留视觉反馈但
  禁用六个命中按钮。

## 实施中发现并修复的问题

| 问题 | 原因 | 修复 |
|---|---|---|
| 点击轴向后相机短暂跳转又回到旧姿态 | `OrbitControls` 保留旧 spherical state | 方向命令改变时用稳定 key 重新挂载 controls，并同步主 PerspectiveCamera |
| 正反轴按钮在重合投影处互相遮挡 | 命中区固定顺序渲染 | 按 gizmo-local projected z 计算动态 `z-index` |
| Y 反向视角无法到达 | `maxPolarAngle` 小于 `Math.PI` | 放开到完整极角范围 |
| mobile/窄视口边缘可能裁切 overlay | 只设置固定 top/right | 保持 80px 尺寸并对 viewport 内边界做约束 |

## Focused Verification

已运行：

```bash
python3 scripts/verify-liblib-batch49.py
```

结果：

```text
Batch 49 director viewport gizmo verification passed.
```

专项脚本覆盖：

- 六个方向的 aria label、命中区和方向快照；
- 真实鼠标点击 `X 正向` 后的主 R3F 画面变化；
- Camera mode 回切 Director mode；
- 对象树选中态、对象、timeline、active camera 不被方向命令修改；
- path drawing、phone recording 禁用命中按钮；
- capture 时隐藏 gizmo，且 capture 结果仍有可解码像素；
- desktop/mobile bounds、无水平溢出；
- main/gizmo 双 WebGL canvas 非空；
- console error、page error 和 request failure 为零。

`npx tsc --noEmit` 和 Batch 49 代码/脚本的 `git diff --check` 已通过。
仓库级门禁和 Batch 35-49 serial regression 在本记录的
[`Repository Gates`](#repository-gates) 中补写最终结果。

## 截图记录

本批只进行一次 contact sheet 视觉识别。详细识图结果、capture metadata、
几何读数、行为读数和不声明项见 [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)；
后续 agent 在提出新问题前不要重复识别同一批截图。

## Repository Gates

最终结果：

```text
Batch 49 focused Playwright: passed
Batch 35-49 serial regression: passed
npm run docs:check: passed (412 Markdown files, 1589 local targets)
npm run check: passed
  - lint: passed, 9 pre-existing warnings, 0 errors
  - typecheck: passed
  - build: passed
git diff --check: passed for Batch 49 source/docs/script paths
```

`npm run build` 仍报告仓库上级存在多个 lockfile 的 Next.js workspace-root
warning；它没有影响编译、TypeScript 或静态页面生成结果。

## Commit / Push

本批使用精确路径提交，避免吸收历史
`docs/design-references/` 修改；push 结果和 commit id 在 closeout 后追加。

## 接力说明

如果会话在代码编辑前中断，下一 agent 应从 `PLAN.md` 和本文件继续；
如果截图已经生成，先读取 `SCREENSHOT_ANALYSIS.md`，不要重复识别同一张图。
