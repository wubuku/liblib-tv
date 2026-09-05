# Batch 121：顶栏新鲜度对齐（2026-09-06 源站）

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 120。

全站新鲜度扫描发现顶栏漂移并落地：

- 积分显示 `20` → `100`（源站当日值）。
- 新增 `开通会员 限时 45 折` 入口按钮（视觉近似，无会员服务）。
- 新增 `积分超市` 显示入口（源站仍有该按钮；此前「已移除」的判断系选择器
  误差，本批更正——`SOURCE_FACT` 修正）。
- `教程与帮助` 入口更名为 `教程`（源站命名），batch11/106 断言迁移。

## 完成定义

1. `verify-liblib-batch121.py` 9 checks、`0/0/0` diagnostics 通过。
2. 相邻 batch11/14/106 通过（断言迁移后）。
3. `npm run check`、`npm run docs:check` 通过。
4. master commit/push。

顶部按钮的存在性对齐限当日采样；会员/商城服务、按钮精确视觉仍为
`SOURCE_UNKNOWN`。漂移方法论：以「按钮清单 diff」做新鲜度扫描可程序化复用。
