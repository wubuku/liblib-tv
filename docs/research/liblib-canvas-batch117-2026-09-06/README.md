# Batch 117：导演台入口与节点卡文案对齐 2026-09-06 采样

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 116。
>
> 源站证据：[`../liblib-canvas-sampling-2026-09-06/README.md`](../liblib-canvas-sampling-2026-09-06/README.md) §4。

节点卡文案对齐丢弃式采样：标题 `3D导演台` → `导演台`、说明
`搭建3D场景，截图作为构图参考` → `在3D空间中搭建场景并进行多视角截图`、
CTA `进入导演台` → `打开导演台`；资产面板节点标签同步。入口行为（建节点卡
→ 卡上按钮进工作区）与 clone 现状一致，verifier 锁定。

## 完成定义

1. `verify-liblib-batch117.py` 11 checks、`0/0/0` diagnostics 通过。
2. 相邻 batch50 通过（工作区 aria 不变）。
3. `npm run check`、`npm run docs:check` 通过。
4. master commit/push。

工作区内部结构与默认场景（机位1+角色A）经采样确认与 clone 一致，已在
采样文档记录，不属于本批代码变更。
