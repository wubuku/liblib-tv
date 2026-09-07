# Batch 198 — 顶栏右侧集群图标原字形对齐

## 源站事实（窗口 rAF ~31fps；`source-topnav-right.json` 存档）

- 顶栏右侧 4 枚按钮字形（均无 aria/title）：
  1. 分享节点图（`0 0 14 14`，三圆连线形）；
  2. 会员商店图标（`0 0 16 16`，内联色 `--nt-cyan-400` 青色）；
  3. 积分闪电（`0 0 16 16`，`g transform="translate(2.935 1.665)"`，
     100 积分旁）；
  4. Agent 机器人脸（`0 0 17.5777 14`，描边双眼）。
- 头像（img）不在 button 内，未采。

## 实施

- `ChromeIcons.tsx` 新增四枚组件：ShareNodesGlyph / MemberShopGlyph /
  BoltGlyph / AgentFaceGlyph（viewBox + inner path 逐字直采，内联 style
  剥离、属性转 camelCase）。
- TopNavBar 替换：lucide Share2 → ShareNodesGlyph；Zap（fill-white）→
  BoltGlyph；Bot → AgentFaceGlyph；会员入口的 ♦ 占位符 → MemberShopGlyph
  （青色 #4de1f4）。首次采集截断（500 字符 slice）导致两枚组件生成失败，
  全量重采后修复。

## 验收

- `verify-liblib-batch198.py`：12 checks（DOM 闪电 g transform 定位 +
  四枚组件定义/viewBox + TopNavBar 使用 + 0 page error）。
- 回归绿：22 / 121（顶栏合同）/ 172 / 196 / 197。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：头像 img；各按钮 hover 色值；会员入口点击后的落地页。
- 源站测试残留清理：0 残留（本批无源站节点操作）。
