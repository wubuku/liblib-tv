# Batch 196 — 顶栏/左下工具条图标原字形对齐

## 源站事实（窗口 rAF ~31fps；`source-chrome-icons.json` 存档）

- **顶栏**：x54/x220 两枚 12×12 同形图标为**下拉箭头**（logo 下拉与画布
  下拉的 ChevronDown，133 字形）；x257/x289 两枚 16×16 为工作流/布局面板
  图标（path 687/656 字）。
- **左下工具条**：x34 面板开关（`0 0 20 20`）、x127 网格（16）、x160 地图
  （`0 0 21.8 21.8`）、x191 链接（16）、x223 磁吸（24——源站亦为 lucide
  形状）。
- 工作区/画布 pill 的 Globe/Link 图标**不是 iconify**（源站未采到），
  clone 的 lucide Globe2/Link2 保持不变。

## 实施与纠错

- 新增 `src/components/ChromeIcons.tsx`：七枚原字形组件
  （WorkflowGlyph/LayoutPanelGlyph/PanelToggleGlyph/GridGlyph/MapGlyph/
  LinkGlyph/MagnetGlyph），path 逐字直采。
- TopNavBar：工作流/布局面板两枚换原字形（Globe2/Link2 保留——初版曾
  误将下拉箭头当作 pill 图标替换，已回滚）；BottomToolbar：五枚全部换
  原字形；未用 lucide import 清理。

## 验收

- `verify-liblib-batch196.py`：16 checks（DOM 中 0 0 20 20 面板开关存在 +
  七枚组件定义与 viewBox 静态合同 + 0 page error）。
- 回归绿：22 / 121（顶栏合同）/ 172 / 188 / 191。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：顶栏下拉箭头与 logo 区的字形（源站有 iconify 箭头，clone 用
  lucide ChevronDown——映射到具体按钮的证据不足，未动）；x223 磁吸图标
  的准确集归属。
- 源站测试残留清理：0 残留（本批无源站节点操作）。
