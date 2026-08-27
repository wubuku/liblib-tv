# Batch 63 实施记录：Actual React Flow Host 中心定位

> 实施日期：2026-08-27  
> 计划 checkpoint：`c4379c6`  
> 实施与 focused verifier checkpoint：`e0e4f53`  
> 当前状态：`IMPLEMENTED_FOCUSED_PASS` / `RESULTS_RECORDED`

## 1. 实施范围

本批关闭普通 LibTV clone 的 default add 空间缺口：Add Node 和 Character Library
不再由组件或 store 使用 browser window center，而是由 page 测量当前实际 React
Flow host，经当前实例的 `screenToFlowPosition()` 转成 `FLOW_WORLD` center，再由
store 按声明的 graph dimensions 计算 node top-left。

没有修改 derived output、duplicate、organize、drop、pending connection、
live/stable viewport、FrameOS、Director 或图片双浮层公式。

## 2. 代码变更

| 文件 | 结果 |
|---|---|
| `src/lib/libtvViewportPlacement.ts` | 新增 finite host/dimensions 校验、client host center、flow-center node top-left 与组合 placement plan；暴露 dev verifier helper。 |
| `src/store/canvasStore.ts` | 新增 `addNodeAtFlowCenter()`；store 保留 node graph dimensions、selection 和 one-step history authority，旧 `addNode()` 保持兼容。 |
| `src/app/page.tsx` | 为 React Flow root 增加稳定 host selector；page-owned callback 量测 host、调用 `screenToFlowPosition()`，host/instance/转换失效时 zero mutation。 |
| `AddNodePanel` / `CharacterLibraryPanel` / `LeftSidebar` | 移除组件对 `canvasStore.addNode()` 的直接依赖，统一接收 page-owned default add callback。 |
| `src/store/uiStore.ts` | Add Node 与 primary panel 的 transient 互斥保留当前 Asset drawer，避免创建前先恢复全宽 host。 |
| `BottomToolbar` / `LeftSidebar` | 资产抽屉打开时桌面主入口工具条跟随实际 host center；窄桌面压缩次级工具条，消除两个固定工具条的点击碰撞；移动端保持上下两行。 |
| `scripts/verify-liblib-batch63.py` | 新增 pure helper、desktop/mobile、drawer closed/open、普通节点、角色库、history/selection、invalid guard、兼容路径、overflow 与 diagnostics verifier。 |
| `runtime-audit.json` | 保存本批 focused runtime 原始结果；不新增截图。 |

## 3. 实施期发现

首轮 verifier 暴露两个与 asset-open default add 直接相关的 clone 问题：

1. `929x874` 时次级工具条 `x=256..527` 与主入口工具条
   `x=295.5..633.5` 重叠约 `231.5px`，“资产管理”层截获“添加节点”点击；
2. 即使强制触发 Add Node，统一 `closedOverlayState` 也会先关闭 Asset drawer，
   导致创建时 host 从 `x=240,width=689` 恢复为全宽。

本批把 Asset drawer 视为此工作流的 layout surface，只对 Add Node / primary panel
保留它；其他 transient overlay 的既有互斥没有被全局重写。完整 DOM 量测和证据
边界见 [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)。

## 4. 运行结果

Focused：

```bash
python3 scripts/verify-liblib-batch63.py
```

结果：`PASS`。

覆盖：

- pure helper identity、translated 和 invalid host/flow/dimensions；
- Add Node 的 text/image/video；
- Character Library 图片节点；
- desktop `929x874` 与 mobile `390x844`；
- Asset drawer closed/open actual host rect；
- 新节点 screen center 对 host center，容差 `1.5px`，实测记录为 `0px`；
- 每次 accepted add 一个 graph history entry；
- selection 精确指向 created node，edge selection 清空；
- Character media data `568x761` 与 graph frame `512x288` 分权；
- invalid flow center zero mutation；
- legacy `addNode()` 兼容调用；
- document/body no-overflow；
- console、page error 和 request failure 为零。

相邻回归：

```text
Batch 15, 17, 46, 59, 60, 61, 62
```

均通过。

项目门禁：

- `npm run check`：通过；保留 9 条既有 FrameOS lint warning，无 error；
- `npm run docs:check`：通过；
- `git diff --check`：通过。

## 5. 截图与测试副产物

本批没有重新识别源站截图，也没有增加新的截图。视觉问题由 DOM rect 与真实
hit-test 日志直接固定。相邻 verifier 覆盖写入的历史截图和 Batch 61 随机 runtime
audit 已恢复到 `HEAD`，避免把测试副产物作为本批证据提交。

`docs/design-references` 不能整体 ignore：其中包含源站证据和经文档引用的稳定
clone 基线。会覆盖固定文件的 verifier 应逐步迁移到临时输出或显式 opt-in 更新，
而不是让常规回归改写权威截图。

## 6. 边界与下一步

本批只关闭 `LIBTV-GC-077` / `LIBTV-VGP-I-020` 的 focused slice。以下仍保持
runtime partial 或 source-gated：

- live/stable/bootstrap/target viewport phase；
- host epoch、canvas generation 和 gesture/programmatic operation owner；
- host resize anchor preservation；
- derived/duplicate/organize placement composition；
- nested-node world projection、invalid parent geometry；
- source exact add anchor、selection、auto-pan、drawer coexistence、fit/zoom/resize；
- Open Canvas Quick Add、drop 和 pending connection。

下一批应继续从 `LIBTV-VR-020` 中选择一个高价值、可独立验证的空间 owner slice，
不把本批扩写成完整空间 authority 或 LibTV source parity pass。

## 7. 保护性 checkpoint

1. `c4379c6`：Batch 63 计划、证据边界和截图成本台账；
2. `e0e4f53`：host-center helper、store/page/component 实施、Asset drawer coexistence、
   responsive collision 修复、focused verifier 和 runtime audit；
3. 本收口提交：实施记录、稳定治理文档和回归结果。
