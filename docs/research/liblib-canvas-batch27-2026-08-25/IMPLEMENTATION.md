# Batch 27 Implementation Log

> 状态：已完成；实现、专项 Playwright、截图分析、跨批回归和工程门禁均已落档。

## 1. Core Implementation

### Toolbar Handoff

- subtitle dropdown 保留 `智能去字幕` / `框选去字幕` 两项。
- entry 增加 source tooltip。
- 两项不再写入 `lastAction`，而是进入独立 subtitle mode。
- subtitle mode 打开时隐藏顶部处理工具条和普通生成 panel。

### `SubtitleErasePanel`

- 新增 source-shaped `48px` compact lower bar。
- 使用 node-relative inverse scale 与 `-bottom-[17px]` border compensation。
- smart 模式包含 close、模式名、积分占位和 `28x28` submit。
- region 模式增加 help、选择区域、undo、redo、reset。
- close / capture-phase Escape 清理当前 session。

### Region Session

- region 进入时按原站把 source 聚焦到至少 `zoom:1`，动画 `220ms`。
- overlay 使用相对画面坐标，支持多矩形。
- 选中矩形支持移动和四角 resize。
- create / move / resize / reset 写入组件内 history。
- undo / redo 由单一 history state 原子更新。
- region 为空时 submit disabled。

### Graph Transaction

- `canvasStore.createSubtitleErase` 一次创建：
  - 右侧 pending video；
  - source-to-target edge；
  - source/mode/region/model/request-mode metadata；
  - target single selection；
  - 一条 graph history snapshot。
- smart request mode 为 `Subtitle`，region 为 `Text`。
- target 标题为 `视频一键去字幕-{sourceLabel}`。
- pending body 使用模式对应文案。

## 2. Browser Smoke Check

本地 `929x874` headless Chromium 已走通：

- entry tooltip 和两项 dropdown；
- smart/region mode handoff；
- panel：`48px` 高，centered，source gap `16 * zoom`；
- region entry 后 source `512px` screen width；
- 两个 region 创建，selected state 正确；
- undo `2 -> 1`、redo `1 -> 2`；
- reset `2 -> 0`、undo reset `0 -> 2`；
- region 空态 submit disabled；
- confirm 后 node `1 -> 2`、edge `0 -> 1`；
- target 单选、名称和 region pending copy 正确；
- console/page errors：`0`。

首轮实现曾使用三个独立 state 保存 past/present/future，浏览器检查发现 redo 依赖嵌套 state update 时序。随后改为单一 `RegionHistory` state，复测通过。

React 19 ESLint 还拒绝了失焦时同步 `setState` 的 effect；该非源站必要重置已删除，session 由 close、Escape 和 submit 显式结束。

## 3. Static Gate

- `npm run typecheck`：通过。
- 定向 ESLint：通过。
- `git diff --check`：通过。

## 4. Focused Playwright

新增 `scripts/verify-liblib-batch27.py`，实际覆盖并通过：

- subtitle tooltip、dropdown 与 smart / region handoff；
- smart panel 的 `48px` 高度、控制尺寸和 node-relative inverse-scale anchor；
- close、capture-phase Escape、zoom、drag、pan 和 multi-selection hiding；
- region 进入时从 `50%` 聚焦到节点宽 `512px` 并居中；
- 多矩形 create / select / move / four-corner resize；
- atomic undo / redo / reset 和空区域 submit guard；
- smart / region target、edge、copy、model 与 request-mode metadata；
- graph undo / redo；
- `929x874` 桌面和 `390x844` 移动端自然裁切；
- 页面级横向 overflow、console error 和 page error 均为 `0`。

专项脚本生成四张状态截图和一张 contact sheet。一次性视觉识别结论已写入 [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：桌面上下层锚定正确，region overlay 与 help 层级清楚，pending graph 无重叠，移动端保留画布内自然裁切且不产生页面横向滚动。

## 5. Protection Points

1. source evidence、plan 和 specs；
2. core UI/store implementation；
3. focused Playwright + screenshot ledger；
4. cross-batch regression + final handoff。

四个保护点均已完成。

## 6. Commits

- `281f6e8 docs: plan subtitle erase workflow`
- `c2fdd9a feat(liblib): add subtitle erase workflow`
- `445e703 test(liblib): verify subtitle erase workflow`
- final documentation and regression record: this commit

## 7. Cross-Batch Regression

串行运行：

```bash
for script in \
  scripts/verify-liblib-batch9.py \
  scripts/verify-liblib-batch21.py \
  scripts/verify-liblib-batch23.py \
  scripts/verify-liblib-batch25.py \
  scripts/verify-liblib-batch26.py \
  scripts/verify-liblib-batch27.py
do
  python3 "$script" || exit 1
done
```

结果：全部通过。

- Batch 9：image/video floating anchor、parent/child follow、pan/zoom、多选。
- Batch 21：normal/long parameters、mode matrix、`300s / 14700`。
- Batch 23：reshoot layers、五段上限、tokens、whole rerun。
- Batch 25：video-clip editor、zoom/drag/pan、多选、mobile。
- Batch 26：continuation range、target/edge、clear 和 undo/redo。
- Batch 27：subtitle 两模式、region history、target/edge 和 metadata。

## 8. Engineering Gates

- `npm run check`：通过。
  - ESLint：`0 error`，保留 9 条既有 FrameOS warnings。
  - TypeScript：通过。
  - Next.js production build：通过。
- `npm run docs:check`：通过，205 个 Markdown、485 个本地目标。
- `git diff --check`：通过。

跨批脚本重写的既有/已提交 PNG 有非确定性压缩或动画采样差异；这些测试产物已恢复到审核过的提交版本，没有把无关二进制 churn 带入最终文档提交。

## 9. Final State

Batch 27 已完成：

- source evidence；
- implementation plan；
- code implementation；
- focused Playwright and screenshots；
- screenshot recognition ledger；
- cross-batch regression；
- production/docs gates；
- agent-facing behavior、component、harness 和 Big Picture updates。

最终文档提交后，Batch 27 可以独立由 `README.md -> IMPLEMENTATION.md -> component specs -> verify script` 接力。
