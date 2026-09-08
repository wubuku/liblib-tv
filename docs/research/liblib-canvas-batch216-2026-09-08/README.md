# Batch 216 — 参考 pill 选择模式横幅（源站直采 + clone 实装）

## 采样修正与方法学

- **重要更正**：此前多批的「参考/标记惰性」结论部分失效——面板 pill 行
  在视口下方（y≈1093 > 826）时，**鼠标坐标点击从未真正落在 pill 上**。
  改用 JS `b.click()`（DOM 可点，无视口限制）后参考 pill 有真实响应：
  打开「选择参考」模式并显示顶部引导横幅。

## 源站事实（`source-参考-js-click.json` / 截图存档）

- 参考 pill JS 点击 → 顶部居中横幅 **364×56 @ (778,12)**：
  「从画布或资产管理选择参考返回节点」——引导用户从画布/资产库选参考，
  选完返回节点。参考 pill 进入选择模式。

## 实施

- `VideoGenerationPanel`：新增 `refSelectMode` 状态；参考 pill 点击进入
  选择模式（`data-reference-select-trigger`）；顶部居中横幅
  （`data-reference-select-banner`，364 宽、createPortal 到 body——
  面板在流变换子树内，fixed 需 portal）渲染源站直采文案。
- 画布选参考的后续语义未采样（横幅常驻直至面板关闭/重选）。

## 验收

- `verify-liblib-batch216.py`：6 checks（横幅出现/364 宽/顶部居中/
  逐字文案/0 page error）。
- 回归绿：213 / 215 / 191 / 22 / 172。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：横幅常驻的退出条件（选完自动消失？Escape？）；画布点选参考
  后回填 slot 的行为。
- 源站测试残留清理：采样节点已删（0 残留）。
