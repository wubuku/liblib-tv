# Batch 148：/project 页面项目卡封面占位图

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-07。
>
> 上一批 checkpoint：Batch 147。
>
> 依据：CLONE_DECISION——源站项目卡有封面图，clone 为纯文本卡。补齐封面占位提升视觉保真度。

/project 页面画布卡添加封面占位区：渐变色背景 + 播放图标 + 节点计数角标。
每张卡视觉上更接近源站项目卡设计。

## 完成定义

1. `verify-liblib-batch148.py` 通过、`0/0/0` diagnostics。
2. `npm run check`、`npm run docs:check` 通过。
3. master commit/push。

封面为渐变占位（CLONE_DECISION），源站实际封面图内容 `SOURCE_UNKNOWN`。
