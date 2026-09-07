# Batch 203 — 资产抽屉「所有评级」筛选菜单实装

## 源站事实（窗口 rAF ~31fps；`source-ratings-menu.json` / 截图已存档）

- 点击「所有评级」打开 **180×225 菜单，6 项**：所有评级 / 1 / 2 / 3 /
  4 / 5（选项文本为裸数字，推测配星级图形——星形未采到，clone 用裸
  数字逐字标签）。
- Batch 102 记录的「菜单语义未采样」由此补齐。

## 实施

- `AssetManagerPanel`：所有评级按钮改为 toggle
  `data-asset-manager-rating-menu`（180 宽、6 项、圆角菜单、选中白 10%）；
  选择后触发器文案更新为所选值（所有评级 / 数字），`minRating` 状态
  本地保存（列表过滤逻辑未实装——源站过滤行为未采样）。

## 验证器迁移

- `verify-liblib-batch102.py`：旧「本地原型：评级未接入」hint 断言 →
  菜单打开断言（其余 hint/文案合同不变）。

## 验收

- `verify-liblib-batch203.py`：8 checks（菜单打开/180 宽/六项顺序/
  逐字标签/选 3 后触发器更新/重置所有评级/0 page error）。
- 回归绿：102（迁移后 13 checks）/ 114 / 121 / 172。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：星形图形（选项文本裸数字）；minRating 对节点列表的实际过滤
  行为（源站过滤效果未采样）；「展示设置」菜单（维持 hint 占位）。
- 源站测试残留清理：0 残留（本批无源站节点操作）。
