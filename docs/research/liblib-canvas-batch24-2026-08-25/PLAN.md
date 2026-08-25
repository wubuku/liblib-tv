# Batch 24 计划：逐帧拉片持久化结果组

## 1. 缺口与价值

| 缺口 | 当前 clone | 源证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 结果拓扑 | 选中分析节点后显示下方浮层 | 画布中出现多个持久化结果组 | 5 | 改为 React Flow 节点 |
| 分镜数量 | 只有 `S01-S04` | `S01-S08` | 5 | 补齐八张卡 |
| 分镜分组 | 单一 tab grid | 三个有剧情阶段标题的分镜组 | 5 | 生成三个组节点 |
| 动态结果 | tab 内三张可勾选卡 | 独立“动态｜运镜与动作参考”组 | 5 | 生成独立组节点 |
| 音乐结果 | tab 内简化波形 | 独立“音乐｜BGM参考片段”节点 | 4 | 生成独立音乐节点 |
| 结果操作 | tabs、check、`加入参考` footer | 每张卡右上只有单个复用/导出图标 | 4 | 移除无证据选择 footer |
| ready 素材 | 图片上覆盖源名称和时长 | section 右侧显示 `00:30 · 1280×720` | 4 | 对齐标签层级 |
| 完成事务 | 900ms 后挂载临时 UI | 结果属于画布产物 | 5 | 单次创建、整体 undo/redo |
| 后端能力 | 本地自动完成 | 当前无真实拉片服务 | 5 | 保持并声明 mock 边界 |

逐帧拉片是 Seedance 2.5 主推工作流中当前结构偏差最大、同时证据最完整的区域。纠正结果拓扑比继续装饰原浮层更有价值。

## 2. 实施步骤

1. 新增 `shot-breakdown-result` React Flow 节点 renderer：
   - `storyboard`、`motion`、`music` 三种类别；
   - 深灰组 surface、组标题和媒体卡；
   - 每张卡标题位于媒体上方，右上保留复用命令；
   - 不提供 tabs、check 或 footer。
2. 在 `canvasStore` 新增单事务完成动作：
   - 更新 source node 为 `complete`；
   - 按选中维度创建结果节点；
   - 从 source node 连接到每个结果节点；
   - 记录一次 history，undo/redo 整体回退/恢复；
   - 防止重复完成创建重复结果。
3. 重构 `ShotBreakdownNode`：
   - ready section 显示时长和分辨率；
   - 预览图片不再覆盖 clone-only 源名称 pill；
   - running 使用本地 component state；
   - 完成后不挂载下方浮层；
   - 完成按钮不再使用无源证据的“重新拉片”。
4. 移除 `ShotBreakdownResultsPanel` 和对应规格陈述。
5. 新增 Batch 24 Playwright：
   - 创建输入节点、选择画布视频；
   - 验证 ready 结构和三个维度；
   - 完成后验证五个持久化结果节点、五条派生边；
   - 验证 `S01-S08`、`M01-M03`、BGM；
   - 验证 deselect 后结果仍存在；
   - 验证 undo/redo 单事务；
   - 验证按维度创建、移动端无 document overflow；
   - 生成桌面、局部结果和移动截图。

## 3. 事实边界

### Source fact

- entry screenshot 显示独立逐帧拉片节点、ready 视频、`00:30 · 1280×720`、三个 active 维度和开始按钮。
- output screenshot 显示：
  - 三个分镜组，共 `S01-S08`；
  - 一个动态组，共 `M01-M03`；
  - 一个 BGM 波形节点；
  - 结果直接出现在画布深色节点/组 surface 中；
  - 媒体卡右上有单个复用/导出命令。
- 当前线上 bundle 明确上传、从画布选择、替换素材、三个维度、开始、running、failed 和上游视频未就绪等文案。

### Inference

- output screenshot 中每个深色结果 surface 视为独立画布结果组；截图没有保留 React Flow DOM type。
- 左侧可见的曲线/连接片段支持结果与上游画布关系，但不能证明精确 edge 数量或 handle id。
- `视频节点 9` 出现在第二个分镜组附近，但有自己的标题和 `1280 × 720`；本批将其视为截图中的其他画布节点，不克隆为逐帧拉片产物。
- 结果组 world 尺寸和间距按 `1053x2757` 截图比例及当前 `28%` 画布密度校准，不写成原站 DOM rect。

### Clone-only decision

- 使用本地静态图片替代真实视频逐帧和动态片段。
- 点击开始后用短暂本地 running 过渡，再一次性创建结果节点。
- 用一条 source-to-result edge 表达每个结果组的派生关系。
- 复用/导出图标只提供本地可访问命令反馈，不创建账户资产。
- 不实现真实上传、分析失败、会员限制、积分或跨会话保存。

## 4. 验收标准

- 完成结果不依赖 source node selected state。
- DOM 中不存在 `[data-shot-breakdown-results-panel]` 和结果 tabs/footer。
- 三个分镜组包含且仅包含 `S01-S08`。
- 动态组包含且仅包含 `M01-M03`。
- 音乐节点显示 `BGM`、`14.6s`、波形、播放命令和时间。
- 默认三个维度生成五个节点；关闭某维度时不生成对应节点。
- 完成动作增加五个节点和五条边，单次 undo 全部撤销，单次 redo 全部恢复。
- Batch 9、15、20-24 与完整工程门禁通过。
