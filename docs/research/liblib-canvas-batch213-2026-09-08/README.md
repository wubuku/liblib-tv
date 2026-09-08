# Batch 213 — 运镜菜单重采：23 运动卡片画廊实装

## 源站事实（窗口 rAF ~31fps；1500 视口覆盖下采样；`source-yunjing-cards.json` / `source-yunjing-names.json` / 截图存档）

- 成对内容（text+script-v2）创建后，运镜 pill 打开**卡片画廊**：
  - 容器 ~799×1319（滚动网格，~4 列），卡片 189×208；
  - **23 枚运动卡片**，名称逐字：固定镜头 / 跟随拍摄 / 盘旋抬升 /
    盘旋下降 / 镜头上摇 / 镜头下摇 / 镜头左摇 / 镜头右摇 / 镜头上升 /
    镜头下降 / 镜头左移 / 镜头右移 / 镜头前推 / 镜头后移 / 变焦推进 /
    变焦拉远 / 柯克变焦 / 环绕拍摄 / 滚筒旋转 / 第一视角 / 无人机 /
    高空航拍 / 手持拍摄；
  - 卡片：aspect-square 远端 webp 缩略图（顺序
    `tool/movement/1..23.webp`）+ 悬停收藏钮（爱心 path）+ 居中名称
    17px。
- 与 clone 的 12 项文本菜单（推镜/拉镜/…/固定）完全不同——旧菜单为
  Batch 116 时代 clone-shaped 占位。

## 实施

- `VideoGenerationPanel` 运镜菜单重构：280px 文本列表 → 799px 四列
  卡片画廊（23 枚运动，`movement-01..23` id、远端 webp 缩略图、
  `border-current` 名称居中）；选中态保留（点击卡片选中并关菜单）。
- `<img>` 加 eslint-disable 注释（远端缩略图保持原生 img）。
- batch146 迁移：12 项文本占位断言 → 23 卡画廊断言（movement-01/
  movement-23 存在、卡片总数 23、缩略图、选中/关菜单合同）。

## 验收

- `verify-liblib-batch213.py`：8 checks（23 卡/前四运动/缩略图/选中后
  关菜单/0 console error）。
- batch146 迁移后 13 checks 全绿；回归 151 / 172 / 22 / 191。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：卡片点击选用后的会话注入格式（选中 ✓ 机制 clone 保留）；
  卡片悬停收藏的完整语义；缩略图远端加载失败态。
- 源站测试残留清理：采样节点已删（0 残留）。
