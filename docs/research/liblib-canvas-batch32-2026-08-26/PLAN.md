# Batch 32 计划：深度动作捕捉参考工作流

## 1. 缺口与价值排序

| 候选 | 当前 clone | 当前源站证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 深度动作捕捉入口 | 无入口、无状态 | `depthMapRefLabel` 已出现在当前 HTML/bundle 字符串；历史审计记录入口存在 | 4 | 本批实施 |
| 深度参数与校验 | 无 | 清晰度、时长限制文案和确认文案已确认；具体占位值未确认 | 4 | 本批实施，保留未知边界 |
| 深度参考派生节点 | 无 | `depthMapRefNodeName` 和 source-linked handoff 已记录 | 4 | 本批实施 pending graph |
| 真实深度媒体 | 无 | 只有产品语义，没有可复现服务资源 | 1 | 不实现 |
| 精确原站几何 | 无 | 没有保存完整登录态截图/DOM rect | 2 | 只做 clone calibration |

本批选择深度动作捕捉，是因为它是 Batch 28/29 连续记录的唯一未实现、且
仍有 source-backed 参数和 graph 语义的高价值视频后处理能力。它比继续
扩展已有主体编辑器更能补齐“视频结果可继续作为参考”的产品链路。

## 2. Source Fact / Inference / Clone Decision

### Source fact

- 当前页面 HTML 和已保存的线上字符串包含：
  - `深度动作捕捉`
  - `深度动作捕捉-{nodeLabel}`
  - `清晰度`
  - `视频超过 {maxMin}min 处理上限`
  - `720P 仅支持处理 {maxSec}s 以内的视频`
  - `确认提取`
  - `提取视频深度信息，为镜头运动、人物动作和空间关系提供参考，减少原视频细节对生成结果的干扰。`
- Batch 28/29 的历史研究将该能力记录为“dialog、校验与派生节点可确认”
  /“入口、intro、参数和派生节点”，但没有把精确 rect 和完整结果截图保存
  为本批可复用的视觉证据。

### Inference

- 深度动作捕捉需要一个独立于普通视频生成器的配置状态；
- 确认后结果应作为画布上的 source-linked reference node，而不是只显示 toast；
- 清晰度改变至少应影响 request-shaped metadata 和结果摘要。

### Clone-only decision

- 在现有 ready-video processing toolbar 中增加一个明确的深度动作捕捉入口；
  入口相邻关系和下方面板几何是 clone calibration，不写成 source DOM fact。
- 使用两个本地测试清晰度选项 `720P / 1080P`；这只表达已见到的 `720P`
  文案和常见配置形态，不声称当前原站选项全集。
- 默认测试 fixture 通过 `?duration=10` 进入可配置状态；默认 `30s` 视频
  保持 guard，不改变既有批次基线。
- 使用 request-shaped metadata 和 `深度动作捕捉-{sourceLabel}` pending
  reference node；不显示真实深度图或伪造 task ID。
- 由于未取得具体 `{maxMin}` / `{maxSec}` 值，clone 只验证本地测试态的
  `duration=10` 可提交和默认 `30s` 的 guard，不在 UI 中编造具体源站数值。

## 3. 实施步骤

1. 新增 `DepthMotionCaptureMetadata`、清晰度类型和 store graph action。
2. 新增 `DepthMotionCapturePanel`，包括说明、清晰度、源视频摘要、确认/
   取消、busy spinner 和稳定 selector。
3. 将 ready-video toolbar 接入入口；打开 panel 时隐藏普通 generation panel
   并保持节点锚定。
4. 扩展 VideoNode pending reference renderer，记录 source、resolution、
   duration、request mode 和 edge。
5. 新增 Batch 32 专项 Playwright，覆盖默认 guard、测试态提交、参数切换、
   pending graph、重复槽位、undo/redo、多选和移动端裁切。
6. 更新组件规格、行为目录、组件清单、Big Picture 和实施历史。

## 4. 验收标准

- 默认 `30s` ready video 点击深度动作捕捉显示限制反馈，不修改 graph/history。
- 测试态 `?duration=10` 能打开独立配置 panel，且普通 generation panel 被替换。
- panel 显示说明文案、清晰度选择、确认/取消和 busy 状态。
- 切换 `720P / 1080P` 后提交 metadata 使用当前值。
- 提交后创建一个 source-linked pending reference node 和一条 direct edge。
- 结果命名为 `深度动作捕捉-{sourceLabel}`，不复用 source poster 冒充深度媒体。
- 首个输出位于 source 右侧固定 world-unit gap，重复输出不重叠。
- source selection、atomic undo/redo、多选隐藏和 `390x844` 自然裁切通过。
- 专项脚本、Batch 9、15、26、27、28、29、30、31 和工程/文档门禁通过。

## 5. 不在本批

- 真实深度估计模型、深度视频/深度图编码和下载；
- 具体源站最大分钟数、720P 秒数和完整清晰度枚举；
- 精确原站 dialog rect、动画曲线、真实图标 SVG；
- 服务端任务、计费、上传、轮询、失败/超时/部分输出矩阵。

## 6. 实施状态

- [x] 证据边界、缺口排序和 workflow/component spec 已落档
- [x] 入口、panel、guard、busy 和 pending graph 已实施
- [x] 专项 Playwright、截图台账和 zero browser-error 检查已完成
- [x] 跨批回归与 `npm run check`
- [ ] commit/push 实现结果
