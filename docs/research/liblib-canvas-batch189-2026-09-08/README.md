# Batch 189 — 比例瓦片字形结构对齐（源站 2026-09-08 直采）

## 源站事实（窗口 rAF ~31fps；`source-ratio-tiles.json` / 截图已存档）

- 每枚比例瓦片的图形 = **17px 居中盒**（`flex size-[17px] items-center
  justify-center`）内套 `flex-none rounded-[2px] border-[1.5px]
  border-current` 内框，逐比例精确 px：
  Auto 12×9 / 16:9 16×9 / 4:3 12×9 / 1:1 12×12 / 3:4 9×12 / 9:16 9×16 /
  21:9 16×7。
- 颜色走 `border-current`（随瓦片文字色——选中白、未选 #777）。

## 开放问题（两日直采矛盾，未证实）

- 今日普通模式菜单为 **7 格含 Auto**（新建 2.5 节点）；Batch 175 昨日
  直采为 6 格无 Auto（当日默认模型 2.0 VIP）。
- 假设：比例格随**模型**而非模式变化（Auto = 模型自决，2.5 才提供）；
  模型切换复测因模型菜单 JS click 无法打开（状态漂移）未能完成。
- 处置：clone 维持 Batch 175/176 合同（普通 6 格 / 长 7 格含 Auto），
  矛盾观察记录在案，待模型依赖证实后再立迁移批。

## 实施

- `AspectRatioGlyph` 重写为源站结构：删 tailwind 尺寸类与
  active 描边色 hack，改 17px 盒 + 1.5px border-current 内框 +
  `GLYPH_DIMENSIONS` 精确 px；`active` prop 移除（颜色由瓦片文字色承载）。

## 验收

- `verify-liblib-batch189.py`：20 checks（六枚瓦片逐一：17px 盒类/
  内框精确 px/1.5px 边框类；0 console error）。
- 回归绿：21 / 22 / 155 / 160 / 175 / 176 / 185 / 186 / 188。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：比例格的模型依赖假设；长模式瓦片字形（假定同一结构，
  本批未单独采样）。
- 源站测试残留清理：采样节点已删（0 残留）。
