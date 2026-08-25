# Batch 26 计划：智能续写两阶段工作流

## 1. 缺口与价值

| 缺口 | 当前 clone | 源证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 交互模型 | 与片段重拍共用完整 editor | 独立“选择 range → 创建目标”两阶段 | 5 | 拆分 |
| range | 默认单选 `24-28s` tile | 连续 `4-30s` 可拖选区 | 5 | 新增 selector |
| 初始值 | 预选尾部 4 秒 | `0-min(duration,30)` | 4 | 对齐 |
| selector 几何 | `660x316` | `660px`、48px timeline、整体约 56px | 5 | 对齐 |
| 节点间距 | `16 * zoom` | source margin `8` | 4 | 独立锚定合同 |
| 确认结果 | 同一节点 submit 状态 | 右侧新 video + edge | 5 | graph transaction |
| 目标节点 | 不存在 | `续写 {nodeLabel}` 视频生成节点 | 5 | 新增 empty state |
| Prompt 语义 | 普通 textarea | 来源/range visible prefix + 专用 placeholder | 5 | 扩展生成 panel |
| 退出续写 | 不存在 | 清 extension 和声明 edge，保留节点 | 4 | 单事务实现 |
| 后端能力 | 本地 UI | 真实裁剪/合规/生成依赖服务 | 5 | 明确 mock 边界 |

该批次修复的是交互模型和画布拓扑，不是低价值视觉装饰。证据来自当前线上运行代码，置信度高于尚未展开的字幕/音频后处理菜单。

## 2. 实施步骤

1. 新增 `VideoContinuationSelector`：
   - `660px` screen width；
   - 约 `56px` screen height；
   - source `8 * zoom` 下方间距；
   - 12 个本地连续缩略帧；
   - cyan `16px` start/end handles；
   - range 区域拖动；
   - `4-30s` 限制、两位小数 duration；
   - close / Escape / confirm。
2. 重构 `VideoNode`：
   - `reshoot` 继续使用 `SegmentReshootPanel`；
   - `continue` 只挂载 selector；
   - 确认后调用 store 创建续写目标并切回 generator；
   - 新增 `empty` 视频生成状态，不冒充 ready/failed 媒体。
3. 扩展 `canvasStore`：
   - 新增 `createVideoContinuation` 单事务；
   - 创建 target video、edge、continuation metadata；
   - 新 target 自动单选；
   - 新增 `clearVideoContinuation` 单事务，保留 target、删除 edge/metadata。
4. 扩展 `VideoGenerationPanel`：
   - continuation visible prefix；
   - placeholder `请输入需要续写的内容`；
   - 固定 `2.5 / 全能参考`；
   - `退出续写模式`；
   - submit 仍为本地反馈。
5. 收窄 `SegmentReshootPanel`：
   - 删除 `mode` prop；
   - 删除续写预选、文案和 submit 分支；
   - 只承担 Batch 23 已验证的片段重拍合同。
6. 新增 `scripts/verify-liblib-batch26.py`：
   - selector 结构、几何、range 初始值；
   - start/end/region drag 与 `4-30s` 限制；
   - cancel / Escape；
   - confirm 后 target + edge + single selection；
   - target prefix、placeholder、固定 model/mode；
   - exit 后 target 保留、edge 清除；
   - create/clear 的 undo/redo；
   - zoom、node drag、multi-selection、390px clipping；
   - screenshot、console/page error。

## 3. 事实边界

### Source fact

- 当前原站 selector 是独立的 `660px` timeline bar。
- wrapper `top:100%`、`marginTop:8`、centered。
- timeline 高 `48px`，handles 宽 `16px`。
- 合法 duration 为 `4-30s`，默认 `0-min(sourceDuration,30)`。
- 选择区支持 start/end/region 三种 pointer drag。
- confirm 创建新的 video node 和 source-to-target edge。
- 退出续写只清 extension/edge，不删除 target。

### Inference

- clone 使用 `-bottom-[9px]` 加 inverse scale 复现 source 的 `8 * zoom` 外间距。
- target empty body 使用 source pending branch 的中心 Play glyph。
- visible prefix 放在 Prompt 主体上方；本批没有 source DOM rect 支持更细的垂直像素定位。

### Clone-only decision

- 12 张缩略帧来自本地已有图片。
- graph 节点/边是内存状态，不调用上传、裁剪、合规或模型服务。
- target Prompt submit 和 exit 只改变本地 UI/store。

## 4. 验收标准

- `SegmentReshootPanel` 不再包含 `continue` 分支。
- 点击 `智能续写` 时只显示 `[data-video-continuation-selector]`，不显示重拍 panel 或生成 panel。
- selector screen box 为 `660x56`，中心对齐源节点，gap 为 `8 * zoom`。
- 初始 range 为 `0-30s`；duration 显示 `30.00 秒`。
- 拖动后 range 始终满足 `4 <= duration <= 30` 且位于源视频内。
- confirm 一次增加一个 video node 和一条 edge，且 target 被单选。
- target 标题为 `续写 {sourceLabel}`，Prompt 显示来源/range 和专用 placeholder。
- target model/mode 固定为 `2.5 / 全能参考`。
- exit 后 target 保留，continuation edge 和 metadata 清除。
- create/clear 分别可由一次 undo/redo 完整回退/恢复。
- 50% zoom 后 selector 仍为 `660x56`；drag/pan 后继续随节点移动。
- 390px 下 selector 自然裁切，但 document 无横向 overflow。
- Batch 9、21、23、25、26 和完整工程/文档门禁通过。
