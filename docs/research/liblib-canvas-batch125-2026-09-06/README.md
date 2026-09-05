# Batch 125：视频生成面板对齐（尝试行/新功能条/提示词）

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 124。
>
> 源站证据：[`../liblib-video-panel-2026-09-06/README.md`](../liblib-video-panel-2026-09-06/README.md)。

视频节点生成面板按 2026-09-06 采样对齐：新增「尝试：」行（5分钟超长视频/
首尾帧生成视频/首帧生成视频，可选中/取消）、`新功能：支持真人` 条、主提示词
placeholder 更新为「描述你想要生成的画面内容，@引用素材」。工具行
（参考/标记/特效/角色库/运镜）与生成流程保持不变（batch21/22 复归通过）。

## 完成定义

1. `verify-liblib-batch125.py` 17 checks、`0/0/0` diagnostics 通过。
2. 相邻 batch21/22 通过（生成流程无回归）。
3. `npm run check`、`npm run docs:check` 通过。
4. master commit/push。

尝试模式的真实子界面、模型菜单内容（2.0）、积分 135 值为 `SOURCE_UNKNOWN`
（后续批次需补采样）。
