# Batch 27 Implementation Log

> 状态：核心实现与浏览器 smoke check 完成，专项验证待开始。

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

## 4. Planned Protection Points

1. source evidence、plan 和 specs；
2. core UI/store implementation；
3. focused Playwright + screenshot ledger；
4. cross-batch regression + final handoff。

## 5. Verification Pending

- focused Batch 27 Playwright
- Batch 9、21、23、25、26、27 regression
- `npm run check`
- `npm run docs:check`
- `git diff --check`

完成后必须把实际结果、修复过程、截图结论和 commit IDs 写回本文件。
