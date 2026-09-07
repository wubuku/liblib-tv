# Batch 167 — /project 次级表面逐类对齐（源站 2026-09-07 结构重审计）

## 源站事实（/project 页面 DOM 重审计）

- 回收站 / 新建文件夹为**实心次级按钮**（`bg-btn-secondary`、h-8、
  新建文件夹 108 宽带图标）。
- 创建卡为 **aspect-video 封面区（居中「开始创作」14px medium）+ 下方标题行
  （创建新的视频项目，py-2.5 text-sm font-medium）**——非虚线占位卡。
- 项目卡封面 aspect-video（267 宽 → 149 高，卡总高 208），标题
  `text-[14px] font-medium`。

## 实施

- 回收站/新建文件夹改实心按钮（bg-white/[0.08]、h-8、px-3、13px）。
- 创建卡重构为封面区 + 标题行结构（去虚线框）。
- 画布卡封面 `h-[92px]` → `aspect-video`（卡总高 ~208）；卡高改内容自适应；
  标题 `text-[14px] font-medium`。

## 角色库模态采样尝试（同期）

点源站工具行「角色库」pill → 模态不挂载（与菜单同因：遮挡限流 rAF），
角色库实时结构继续阻塞（clone 仍基于 2026-09-06 采样）。

## 验收

- `verify-liblib-batch167.py`：14 checks（实心按钮/创建卡结构/封面比例/标题字重）。
- 相邻回归绿：119 / 136 / 148 / 150 / 152。
- `npm run check`：0 errors、8 warnings（既有基线）。
