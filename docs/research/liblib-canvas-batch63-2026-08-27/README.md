# Batch 63：Actual React Flow Host 中心定位

> 状态：`PLAN_RECORDED`。
>
> 建档日期：2026-08-27。
>
> 对应合同：[`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)
>
> 对应 verifier：`LIBTV-VR-020` 的 `LIBTV-GC-077` / `LIBTV-VGP-I-020` focused slice。

## 目标

修复普通 LibTV clone 中新增节点使用 `window.innerWidth/innerHeight` 推算中心的
空间缺口。新增节点应以当前实际 React Flow host 的屏幕中心为锚点，经当前
React Flow 实例的 `screenToFlowPosition` 转换为 `FLOW_WORLD`，再由 store 按
节点 graph dimensions 计算 top-left。

本批覆盖：

- Add Node 面板创建普通节点；
- Character Library “应用至画布”创建图片节点；
- 资产抽屉打开后 host 变窄/偏移时的中心定位；
- desktop/mobile host center；
- one graph history step、created-node selection 和 no-overflow；
- pure placement helper 的 host/viewport/domain 结果。

本批不覆盖：

- Open Canvas Quick Add、drop、pending connection 或菜单坐标；
- derived output、duplicate、organize、clipboard/paste 的既有策略；
- live/stable viewport phase、gesture generation、resize anchor preservation；
- source exact add auto-pan/selection policy；
- FrameOS、Director、图片双浮层和任何视觉皮肤重构。

## 接力入口

- [`PLAN.md`](PLAN.md)：证据边界、实现切片、fixture、验证与停止条件；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：截图复用和视觉变化闸门；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：完成后的代码、验证和 checkpoint；
- [`../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)：
  actual host、坐标域和 placement authority；
- [`../../components/CharacterLibraryPanel.tsx`](../../components/CharacterLibraryPanel.tsx)：
  当前角色库创建入口。
