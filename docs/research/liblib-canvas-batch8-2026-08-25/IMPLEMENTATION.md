# LibTV 画布 Batch 8 实施记录

> 状态：实施中
> 最后更新：2026-08-25

## 已完成

- 复核原站视频组与图片组 class；
- 读取 xyflow v12 `NodeWrapper` 与 `parentLookup` 源码；
- 确认 `.parent` 只由真实 child 关系产生；
- 计算原站视频相对组位置为 `(62,62)`；
- 审计 duplicate canvas、selection duplicate、group/ungroup、delete、derived node 和 organize；
- 建立 Batch8 计划与父子关系规格。

## 待完成

- 写入初始 `parentId` 与相对坐标；
- 修正绝对位置辅助逻辑；
- 兼容 parented child 重新成组；
- 删除 group 时级联 descendants；
- 编写 Batch8 Playwright 验证；
- 跑 Batch4-Batch8 与完整工程检查；
- 更新全局接力文档、提交并推送。

