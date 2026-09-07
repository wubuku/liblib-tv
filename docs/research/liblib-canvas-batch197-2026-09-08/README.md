# Batch 197 — 画布下拉箭头原字形对齐

## 源站事实（`source-chrome-icons.json`，Batch 196 采集）

- 顶栏下拉箭头：12×12 libtv 图标（viewBox `0 0 16 16`，
  `g transform="translate(4.345 5.825)"`，133 字 path）；
  源类含 `group-data-open/logo:rotate-180`（展开时旋转 180°，200ms 过渡）。

## 实施

- `ChromeIcons.tsx` 新增 `ChevronDownGlyph`（path/g transform 逐字直采）。
- TopNavBar 画布下拉的 lucide `ChevronDown` → `ChevronDownGlyph`
  （ChevronDown import 移除；`data-open` 旋转语义记为不证明——clone 的
  展开态机制不同）。
- logo 下拉在 clone 无箭头按钮（x54 箭头的对应物），保持不动。

## 验收

- `verify-liblib-batch197.py`：7 checks（DOM 中 g transform 定位 + viewBox
  + 顶栏位置尺寸/组件定义/transform 合同/TopNavBar 使用 + 0 page error）。
- 回归绿：22 / 121（顶栏合同）/ 172 / 196。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：展开时 rotate-180 的 clone 对应实现（clone 下拉无 data-open
  机制）；logo 下拉箭头（clone 无对应按钮）。
- 源站测试残留清理：0 残留（本批无源站节点操作）。
