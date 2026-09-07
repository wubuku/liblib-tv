# Batch 192 — 特效卡点击选用行为（源站直证 + clone 实装）

## 源站事实（2026-09-08 截图 `source-effect-clicked.png` + DOM）

- 点击特效卡（试妆特写）：库关闭，**画布生成新节点
  「素材 - 特效 - 试妆特写」**（带效果缩略图，位于视频节点左下方），
  并以连线**指入视频节点**（素材 → 视频）；积分不变（135）。
- 卡片外层类名含 `hover:bg-canvas-controls-hover … cursor-pointer`。

## 实施

- `VideoGenerationPanel` 新增 `onSelectEffect` prop；特效卡 onClick →
  `onSelectEffect(name)` + 关闭特效库；卡片类名补源站的
  `cursor-pointer` 与 `hover:bg-canvas-controls-hover`。
- `VideoNode` 实装 `onSelectEffect`：`addNodeAtPosition("image",
  视频节点左下, { filename: 素材 - 特效 - <名> })` + `addEdge`
  （素材 → 视频，显式 `sourceHandle: "source"` / `targetHandle: "target"`
  ——校验器要求显式 handle 方向，缺失即 INVALID_HANDLE_DIRECTION）。

## 验收

- `verify-liblib-batch192.py`：5 checks（库关闭/节点 +1/边 +1/
  「素材 - 特效 - 试妆特写」文本出现/0 console error）。
- 回归绿：33 / 125 / 172 / 178 / 185 / 186 / 187 / 191。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：缩略图（clone 用默认占位图，源站为效果 webp）；积分扣除
  （选择不扣，生成时才扣的推断未采样）；重复选同一特效的行为。
- 源站测试残留清理：采样节点已删（0 残留）。
