# Batch 33 Source Evidence

> 采样整理日期：2026-08-26  
> 原站页面：`https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd`

## 1. Evidence Set

### 登录态当前事实

复用：

- [`../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)
- [`../liblib-seedance-2.5-2026-08-25/live-audit.json`](../liblib-seedance-2.5-2026-08-25/live-audit.json)

已确认：

```text
模式：超长视频 Beta
时长：30-300s
300s 预计积分：14700
参数行：2.5 · 超长视频 · 16:9 · 720P · 300s · 1个 · 14700
```

这些是 2026-08-25 当前登录态采样事实。它们不证明真实任务协议、处理阶段
或未来版本仍保持同一数值。

### Article screenshot

文件：

[`long-video-generation-graph.png`](../liblib-seedance-2.5-2026-08-25/evidence/long-video-generation-graph.png)

```text
size: 1080x1504
sha256: 70cb23486fd369852c02e21ca744cbf2d483b6890d4e3eeb0a8f589042af30af
classification: article-screenshot
```

该截图直接支持画布过程的视觉层级，但不是 2026-08-26 登录态 DOM 截图。

## 2. Confirmed Visual Semantics

- 过程发生在深灰大画布上，不是 modal 或 Prompt 面板内部；
- 左侧存在多列输入素材和带 `Sxx` 标识的镜头卡；
- 素材与镜头卡之间存在大量多对多连线；
- 中部有小型配置/处理节点；
- 中右部有两组横向候选生成结果，每组可见上下两张画面；
- 候选继续汇聚到右侧处理节点；
- 最右侧是横向最终成片卡；
- 整体语义是“素材 -> 镜头 -> 批次候选 -> 拼接/成片”。

详细的一次性识图记录见 [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)。

## 3. Evidence Limits

当前不能确认：

- 截图中的具体中文标签；
- 精确节点数量、尺寸、位置、端口和 edge 路由；
- 一个镜头对应多少候选；
- 后端是否按固定时长拆段；
- 真实任务、模型调用、拼接、进度或完成资源协议；
- 当前线上项目是否仍能触发与文章截图完全相同的结果图。

因此本批实现的 node count、copy、geometry、mock images、busy timer 和 metadata
字段是 clone calibration / request-shaped prototype，不是 source fact。

## 4. Current Clone Gap

`src/components/VideoGenerationPanel.tsx` 当前的 `LongVideoProcess`：

- 只在 `660x274` 生成面板内显示四张横向阶段卡；
- 没有 source-linked graph；
- 没有中间素材、镜头、候选或最终成片节点；
- “生成视频”只切换本地勾选状态；
- 没有可撤销的整批过程、重复提交避让或过程 metadata。

这与文章截图的画布级交互模型不一致，是本批要修正的核心缺口。
