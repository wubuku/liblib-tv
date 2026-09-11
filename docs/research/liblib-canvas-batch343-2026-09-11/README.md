# Batch 343 — 顶栏 chrome 修正落地（`IMPLEMENTED_VERIFIED`）

> 状态：执行 batch 342 留档的实施清单；`verify-liblib-batch343.py`
> 13 checks 全绿。源站证据：2026-09-11 截图 + 三次独立按钮文本转储
> （batch 342 README 所载）。

## Clone 变更

- **移除 积分超市 按钮**：源站 2026-09-11 顶栏已无该入口
  （batch 139 时代双入口废止，batch 139 注释同步改写）；
- **开通会员 与 积分余额 换序**：会员在前（源站顺序）；
- 蓝色小图标与圆形头像维持 SOURCE_UNKNOWN，不在 clone 伪造。

## 验证器迁移

- batch 121：顶栏按钮清单 积分超市 → 积分余额；
- batch 139：双入口断言改为 积分超市缺席 + 开通会员 在 积分余额
  之前（`order:membership-before-balance`）；
- batch 168 不受影响（其「积分超市限时抢购」为 /project 列表页侧栏
  促销文案，与顶栏无关，复跑全绿）。

## 验收

- `verify-liblib-batch343.py` 13 checks：积分超市缺席、右侧三入口
  存在性与顺序（分享→会员→余额）、会员/余额文案、Agent 最右、
  顶栏左簇不受影响，全绿；
- 回归：121/139/168/198/341/334/100 全绿；
- `npm run check` 0 errors（8 warnings 基线）；docs check 通过
  （902 Markdown）。

## 后续候选

- 源站恢复后：BLOCKED_SOURCE 补采（三项）+ 蓝色图标/头像身份采样
  + 故事板 CLONE_DECISION 替换；
- 图片栏 对话/展开 行为采样（待源站恢复）；
- 新表面随源站更新巡检。
