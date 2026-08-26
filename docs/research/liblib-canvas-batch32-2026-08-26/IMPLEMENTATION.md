# Batch 32 Implementation Log

> 状态：实现、专项浏览器验证、跨批回归、工程门禁和提交推送均已完成。

## Planned Protection Points

1. source evidence、缺口排序、工作流规格和组件规格；
2. depth metadata、panel、VideoNode 接线和 graph transaction；
3. focused Playwright、clone screenshot ledger 和浏览器错误检查；
4. 跨批回归、工程/文档门禁、最终 handoff 和 commit/push。

## Core Implementation

- 新增 `DepthMotionCaptureResolution`、`DepthMotionCaptureMetadata` 和
  `canvasStore.createDepthMotionCapture`。
- 新增 `DepthMotionCapturePanel`，以节点下方 `NodeToolbar` 表达 source
  summary、source-backed intro、`720P / 1080P` 本地选项、取消、确认和 busy。
- `VideoProcessingToolbar` 增加独立 `深度动作捕捉` 入口，没有改变 Batch 30
  已确认的四项主体编辑菜单。
- `VideoNode` 新增 pending depth reference renderer；默认 30 秒 guard 使用
  独立 `[data-video-depth-motion-feedback]` 状态和 timer，不再复用主体编辑
  feedback。
- 输出命名为 `深度动作捕捉-{sourceLabel}`，不复用 source poster；metadata
  保存 source、resolution、duration、model、request mode 和 edge。
- 重复输出使用 `findAvailableRightSlot`；source selection 保留；undo/redo
  以单次 graph transaction 回滚/恢复。

## Browser Smoke

2026-08-26 headless Chromium `929x874` / `390x844`：

- 默认 30 秒视频显示独立时长反馈，graph 保持 `1 node / 0 edge`；
- `?duration=10` 打开节点下方 panel，顶部 processing toolbar 继续保留；
- 标题、用途说明、source summary、720P/1080P、确认和 spinner 可通过稳定
  selector 观察；
- 1080P 提交创建 pending depth reference，并记录 `DepthMap`、
  `depth-motion-reference`、source/edge/resolution/effective-duration
  metadata；
- 重复提交使用右侧第二槽位；source 保持 selected；graph undo/redo 正确；
- 多选隐藏单节点浮层；390px viewport 自然裁切且无 document 横向 overflow；
- 专项脚本捕获到零 console/page errors。

## Focused Playwright

新增 [`scripts/verify-liblib-batch32.py`](../../../scripts/verify-liblib-batch32.py)，
覆盖 guard、双浮层、参数、busy、pending graph、direct edge、重复槽位、
history、多选、移动端和浏览器错误。

一次性视觉识别已写入
[`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)。截图是 clone 验证产物，
不是新增原站事实；后续接力先读台账，不重复识别 contact sheet。

## Cross-Batch Regression

新增深度入口后，ready-video toolbar 从历史 `1009px` 扩展到当前内容宽度。
旧 Batch 29/30 不再锁定总宽度，而是严格验证：

- toolbar 高度仍为 `49px`；
- toolbar 与 source video 水平中心一致；
- 新深度入口存在；
- frame / subject 菜单仍保持 `160px`、trigger-relative center/gap 和原有顺序；
- 移动端仍自然裁切且不产生 document overflow。

Batch 30 的移动端 `NodeToolbar` 在首次挂载后等待 `120ms` 再读取 rect，验证
panel/source 中心关系。Batch 26 的移动端续写入口因工具条自然裁切而使用
DOM click 进入 selector-only 响应式测试；桌面仍保留真实用户点击覆盖。

跨批脚本会刷新同名 clone screenshot。它们是当前实现验证产物，不是新的
原站证据；本批只对 Batch 32 contact sheet 做了一次视觉识别。

## Verification Results

2026-08-26，在 `http://localhost:3000` 上实际通过：

```text
python3 scripts/verify-liblib-batch9.py                          PASS
python3 scripts/verify-liblib-batch15.py                         PASS
python3 scripts/verify-liblib-batch26.py                         PASS
python3 scripts/verify-liblib-batch27.py                         PASS
python3 scripts/verify-liblib-batch28.py                         PASS
python3 scripts/verify-liblib-batch29.py                         PASS
python3 scripts/verify-liblib-batch30.py                         PASS
python3 scripts/verify-liblib-batch31.py                         PASS
python3 scripts/verify-liblib-batch32.py                         PASS
npm run docs:check                                               PASS
npm run check                                                    PASS
git diff --check                                                 PASS
```

`npm run check` 为 `0 error`；保留 9 条既有 FrameOS/共享代码 warning。
Next build 仍提示上级目录存在另一个 lockfile，未影响 production build。

## Commit Protection

```text
0f3344c feat(liblib): add depth motion capture workflow
```

已推送到 `origin/master`。该提交包含实现、专项脚本、Batch 32 截图、当前
跨批 clone 截图刷新、回归脚本结构断言和文档收口。

## Interruption Handoff

下一步先阅读本目录的 `README.md`、`SOURCE_EVIDENCE.md`、`PLAN.md`、
`DEPTH_MOTION_WORKFLOW.spec.md`、`SCREENSHOT_ANALYSIS.md` 和本文件。继续回归
时不要把具体 `{maxMin}` / `{maxSec}`、原站 dialog geometry 或真实深度媒体
写成已确认事实。下一批研究可从当前 `origin/master` 继续。
