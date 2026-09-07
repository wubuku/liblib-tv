# Batch 168 — /project 左侧边栏落地（源站 2026-09-07 结构重审计）

## 源站事实（Batch 167 同轮 /project DOM 重审计）

左侧 240px sticky 侧边栏：
- 顶部「新建项目」按钮（207×36，图标 + text-sm）。
- 导航行 首页 / 项目（激活态 bg-nt-bg-overlay-active）/ LibTV Agent /
  创作者挑战赛，各 h-9 w-full rounded、图标 + 文字 gap-2。
- 底部：SD2.5畅享卡上线/积分超市限时抢购 双行促销卡（207×62）+ 帮助按钮。

## 实施

- /project 主结构改为 flex：左侧 `aside[data-project-sidebar]`（sticky、
  h-screen、240px、右侧 hairline 分隔）+ 右侧内容列。
- 新建项目 → addCanvas + 新标签页打开（与创建卡一致）。
- 导航行数据驱动渲染；「项目」aria-current="page" 激活态；
  首页/LibTV Agent/创作者挑战赛为本地占位提示（setStatus）。
- 底部促销卡与帮助按钮（本地占位）。

## 验收

- `verify-liblib-batch168.py`：13 checks（宽度/新建项目/4 导航行顺序与激活态/
  行高/促销文案/帮助/内容区位置）。
- 相邻回归绿：119 / 136 / 148 / 150 / 152 / 167。
- `npm run check`：0 errors、8 warnings（既有基线）。
