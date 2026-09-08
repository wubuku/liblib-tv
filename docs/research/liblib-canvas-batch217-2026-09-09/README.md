# Batch 217 — 标记 pill 元素选择模式横幅（源站 JS 点击直采 + 实装）

## 源站事实（窗口 rAF ~31fps；`source-mark-js-click.json` / 截图存档）

- JS 点击标记 pill → 顶部居中横幅 **316×56**：
  「元素选择模式 点击图片选择局部元素 返回节点」——与参考 pill 同构的
  选择模式引导横幅（标记=元素选择模式，点图片选局部）。
- 横幅出现于顶部居中（y≈12），验证了「选择模式横幅」家族：参考横幅 +
  标记横幅两兄弟。

## 实施

- `VideoGenerationPanel`：新增 `markSelectMode` 状态；标记 pill
  （`data-mark-select-trigger`）点击渲染顶部居中横幅
  （`data-mark-select-banner`，316 宽，portal 到 body）。
- 参考 pill 的选择模式横幅（Batch 216）保持不变——两兄弟横幅并存。

## 验收

- `verify-liblib-batch217.py`：6 checks（横幅出现/316 宽/顶部居中/
  逐字文案/0 page error）。
- 回归绿：216 / 215 / 213 / 22 / 172。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：选择模式点图片选局部后的实际标注行为；横幅退出条件。
- 源站测试残留清理：0 残留（本批仅横幅交互）。
