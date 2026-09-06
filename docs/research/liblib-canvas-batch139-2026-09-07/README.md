# Batch 139：顶栏 积分超市 / 积分余额 拆分

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-07。
>
> 上一批 checkpoint：Batch 138。
>
> 源站证据：2026-09-06 按钮清单（分享 | 积分超市 | 开通会员 | 100 | Agent）。

源站顶栏的 积分超市 与 积分余额(100) 是两个独立入口；clone 此前把
aria-label 积分超市 错标在积分余额芯片上。拆分为：🏆积分超市 入口（展示，
点击不接商城）+ ⚡积分余额 100 芯片。

## 完成定义

1. `verify-liblib-batch139.py` 6 checks、`0/0/0` diagnostics 通过。
2. `npm run check`、`npm run docs:check` 通过。
3. master commit/push。
