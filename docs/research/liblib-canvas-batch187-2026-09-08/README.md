# Batch 187 — footer doc-sparkle/settings2 点击语义采样（点击惰性证实）

## 源站事实（窗口 rAF ~31fps；`source-settings2-click-state.json` / 截图已存档）

- 空白新建节点的面板上点击 settings2（`0 0 24 24`）：无弹层、无 toggle
  （点击前后类名差异仅为 hover 噪声——JS click 不移动鼠标）、无新挂载
  fixed 层。
- doc-sparkle（`0 0 20 20`）早前同法点击同样无任何可见响应。
- 结论：两枚按钮在已采样状态下**点击惰性**，与 clone 的无 onClick 占位
  实现一致。真实语义（是否需提示词/引用等前置条件）仍未采样。

## 实施

- 零代码改动（clone 已是惰性占位）。
- 新增 `verify-liblib-batch187.py`（9 checks）：点击两枚按钮后无任何
  菜单/弹层打开、面板完好、参数与 credits 不变、0 console error——把
  「点击惰性」固化为回归合同。

## 验收

- `verify-liblib-batch187.py`：9 checks 一次通过。
- 回归绿：186 / 21 / 22 / 125 / 172 / 178；`npm run check` 0 errors；
  docs check 通过。
- 不证明：两枚按钮的前置条件语义（非空节点/有引用时是否开弹层）。
- 源站测试残留清理：采样节点已删（0 残留）。
