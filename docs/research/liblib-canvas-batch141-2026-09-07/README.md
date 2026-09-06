# Batch 141：视频模型菜单全量目录落地（35 项）

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-07。
>
> 上一批 checkpoint：Batch 140。
>
> 源站证据：[`../liblib-video-panel-2026-09-06/README.md`](../liblib-video-panel-2026-09-06/README.md) 模型菜单全量采样（35 项,2026-09-06 晚间至 09-07 会话恢复后收集）。

clone 视频模型菜单从旧 7 项更新为源站全量 35 项目录（名称/生成时长/描述/
premium 子集），菜单容器改为内部滚动（几何 380x410 不变）。batch22 的
EXPECTED_MODELS 矩阵与 premium 计数（5）、Kling O3 负断言随采样更新；
batch125/126/128/21 复跑通过。

## 完成定义

1. `verify-liblib-batch22.py`（矩阵迁移后）、`verify-liblib-batch125/126/128/21.py` 通过。
2. `npm run check`、`npm run docs:check` 通过。
3. master commit/push。

premium 完整分布与未采样模型定价仍为 `SOURCE_UNKNOWN`。
