# Batch 71 实施与验证记录

> 状态：`COMPLETE / POINTER_LIFECYCLE_FOCUSED_PASS`。
>
> 日期：2026-08-27。
>
> 代码范围：Director Inspector、timeline、R3F viewport、DOM gesture helper
> 与 Batch 71 pure/browser verifier。普通 React Flow graph、FrameOS route、
> submodule 和登录态 LibTV 源站均未修改。

## 1. 实施目标

Batch 70 已有 project-local history kernel，但真实 UI adapter 只覆盖
object/group TransformControls 和 speed curve。Batch 71 把高频连续输入接到同一
事务边界：

```text
begin from current project baseline
  -> repeated DOM/R3F updates without intermediate history
  -> blur/pointerup/complete commits at most one entry
  -> Escape/pointercancel cancels and restores baseline
```

这仍是 clone-owned reliability contract，不是 LibTV source-exact undo/redo、
commit timing 或快捷键文案。

## 2. 代码变更

### 2.1 DOM gesture helper

新增
[`useDirectorGestureBoundary.ts`](../../../src/components/director/useDirectorGestureBoundary.ts)：

- typed focus、blur、pointerdown、pointerup、pointercancel 和 keydown handlers；
- number input 在 pointerup 时保持事务，避免点击字段后继续键入被提前提交；
- range pointerup、全部字段 blur 负责 commit；
- Escape cancel 并阻止事件继续触发 workspace close；
- range/number 的键盘修改会重新 begin；
- 订阅 store active gesture，外部 cancel/owner close 后清理组件本地 active ref。

### 2.2 Inspector adapter

修改
[`DirectorInspector.tsx`](../../../src/components/director/DirectorInspector.tsx)：

- object transform、group transform；
- camera FOV、manual target、follow offset；
- character pose range controls；
- path anchor position、Bezier in/out handle；
- path position/rotation/scale transform。

disabled derived axis 不启动 gesture。preset、toggle 和 select 等离散 command
仍使用现有单次 mutation，不机械套用连续输入 helper。

### 2.3 R3F path adapter

修改
[`DirectorViewport.tsx`](../../../src/components/director/DirectorViewport.tsx)：

- path anchor/Bezier TransformControls 在 mouse down begin、mouse up commit；
- handle 与 position 两个分支都明确 commit；
- local active ref 和 window `pointercancel` fallback 防止中断后 gesture 残留；
- pencil pointerup 在正式 path 构造后 commit；
- pen 完成按钮和 Enter 在正式 path 构造后 commit；
- Escape、取消按钮和 pointercancel 同时清 draft 与 cancel gesture。

修改
[`DirectorTimeline.tsx`](../../../src/components/director/DirectorTimeline.tsx)：

- pencil/pen draft 成功创建后，以 track/tool 为 scope 开始 `path-draw`
  gesture；
- 无有效 selected track、draft 未建立时不启动 history transaction。

## 3. 验证实现

新增：

- [`verify-liblib-batch71.mjs`](../../../scripts/verify-liblib-batch71.mjs)；
- [`verify-liblib-batch71.py`](../../../scripts/verify-liblib-batch71.py)；
- [`runtime-audit.json`](runtime-audit.json)。

pure verifier 覆盖 helper、Inspector、path/free-draw wiring 和 cancel fallback。
browser verifier 每个场景使用 fresh Page 和具名 Director source node fixture，
通过真实 DOM/R3F UI 驱动更新，只使用公开 store 读取结果和构造初始 path。

## 4. Fresh-page 结果

命令：

```bash
LIBLIB_BASE_URL=http://localhost:3001 \
  python3 scripts/verify-liblib-batch71.py
```

结果：`PASS`。

| 场景 | History delta | 结果 |
|---|---:|---|
| object position 连续 fill 后离开 | 1 | PASS |
| object position 修改后 Escape | 0 | baseline restore |
| pose 连续键盘调整后离开 | 1 | PASS |
| camera FOV 连续键盘调整后离开 | 1 | PASS |
| path anchor position | 1 | PASS |
| path transform position | 1 | PASS |
| pencil drag + pointerup | 1 | 17-anchor fixture committed |
| pen 三锚点 + 完成按钮 | 1 | 3-anchor fixture committed |
| pen draft + Escape | 0 | previous path preserved |
| pencil draft + window pointercancel | 0 | draft/gesture cleared |
| ordinary canvas graph/history | 0 delta | PASS |
| console/page/request errors | 0 | PASS |
| screenshot writes | 0 | PASS |

## 5. 失败与修正记录

| 现象 | 分类 | 修正 |
|---|---|---|
| 首次 typecheck 提示 drawing surface 未取出 `cancelMotionPathDrawing` | implementation omission | 增加 store selector，并将 cancel button/pointercancel 统一为 draft + gesture cancel |
| path handle TransformControls 更新后直接 return | implementation defect | handle 分支在 update 后显式 commit |
| number input pointerup 立即 commit | interaction design defect | number 保持到 blur；range 仍可在 pointerup 收口 |
| 外部 Escape/cancel 后 helper local ref 可能仍 active | lifecycle defect | helper 订阅 store active gesture，外部清理时同步 reset |
| 合成 `pointercancel` 派发到 WebGL canvas 未稳定命中 R3F mesh | event-layer limitation | 增加 window-level pointercancel fallback，并保留 mesh handler |
| pure verifier 对条件 command kind 使用过窄字面量正则 | verifier defect | 改为语义存在性断言 |

## 6. 当前边界与下一步

Batch 71 关闭了 `LIBTV-VR-024` 的高频 pointer lifecycle slice。仍未覆盖：

- reference-aware delete、last-camera、group/path/track/capture repair；
- capture/export async owner freshness；
- durable persistence、真实 mesh/panorama/resource lifecycle；
- 所有离散 action 的 typed command result；
- LibTV 登录态 Director 的 source-exact DOM/CSS/interaction calibration。

下一批优先进入 reference-aware delete planner；在 destructive mutation 前必须
先定义 closure、dangling-reference repair、zero-partial rejection、history
cardinality 和 resource effects。
