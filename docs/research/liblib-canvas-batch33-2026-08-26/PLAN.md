# Batch 33 计划：超长视频画布过程图

## 1. 缺口与价值排序

| 候选 | 当前 clone | 当前证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 超长视频画布过程图 | 面板内四张横向只读卡；提交只改按钮颜色 | 登录态确认入口/参数；文章截图确认完整画布过程 | 5 | 本批实施 |
| 多角度 / 打光 / 九宫格 | 通用派生 prototype | 缺少逐动作登录态 DOM/结果证据 | 3 | 延后，避免继续脑补 |
| 高清 / 宫格切分 | 通用派生 prototype | 缺少结果态与参数证据 | 3 | 延后 |
| 真实长视频任务进度 | 无 | 无可复现任务协议或媒体 | 1 | 不实现 |

当前超长视频能力的最大错位不是样式细节，而是交互模型错误：原证据把过程
表达为可观察的画布图，clone 却把它压缩成 `660x274` 面板里的四步条，生成
按钮也不会产生 graph。修正这一点比继续扩展低证据图片动作更有价值。

## 2. Source Fact / Inference / Clone Decision

### Source fact

- 2026-08-25 登录态原站存在 `超长视频 Beta` 模式；
- 时长范围为 `30-300s`；
- `300s` 时显示 `14700`；
- 外部文章保存的过程截图是深灰大画布，不是 modal 或输入面板；
- 截图中可见多列素材/镜头卡、多对多连线、候选生成结果、汇聚处理节点和
  最右侧成片卡。

### Inference

- 超长视频提交应在画布上产生一组可查看的过程对象，而不是只切换按钮颜色；
- source video 和 Prompt 中的参考素材应进入过程图上下文；
- 一次提交应作为一个 graph transaction，便于用户撤销整批过程节点；
- 中间节点应表达“待处理/待生成”，不能把文章中的示例画面冒充本次结果。

### Clone-only decision

- 使用一个 `long-video-process` renderer 的多种 stage 变体表达素材、镜头、
  候选、汇聚和最终成片；
- 每批本地创建 3 个素材、3 个镜头、4 个候选、1 个汇聚、1 个最终节点；
- 使用当前仓库已有咖啡馆素材作为可辨识缩略图，但候选/最终状态覆盖等待态；
- 使用固定 world-unit 列间距、批次纵向避让和约 `520ms` 本地忙状态；
- graph metadata 保存请求形状，不创建 task ID 或伪造后端状态；
- `查看过程` 不再渲染面板内四步图，改为说明“提交后在画布查看过程”。

以上数量、标签、位置、图片和时序均为 clone calibration，不写成原站合同。

## 3. 实施步骤

1. 新增长视频 request/stage metadata 和 `createLongVideoProcess` store action。
2. 新增紧凑 `LongVideoProcessNode`，注册到 LibTV React Flow。
3. 将 `VideoGenerationPanel` 的长视频提交接到 source video graph action。
4. 创建素材、镜头、候选、汇聚和最终节点，以及 source/many-to-many/汇聚边。
5. 保留 source selection；重复提交按整批 graph bounds 纵向避让。
6. 新增 Batch 33 专项 Playwright，覆盖参数、busy、graph、metadata、拓扑、
   避让、history、多选和移动端。
7. 更新组件规格、行为目录、组件清单、Big Picture、Harness 和实施历史。

## 4. 验收标准

- 普通模式提交继续保持既有本地反馈，不创建长视频 graph。
- 长视频模式提交按钮短暂 disabled，并显示可观察的忙状态。
- 提交后新增 12 个过程节点，覆盖五类 stage。
- source video 连接到镜头过程；素材与镜头存在多对多关系。
- 镜头连接到两批候选，候选汇聚到处理节点，处理节点连接最终成片。
- 所有节点共享 process ID，并记录 source、prompt、model、ratio、resolution、
  duration、audio、credits 和 stage/index。
- 最终节点显示等待拼接，不声称已有完成媒体。
- source selection 保持；一次 undo/redo 移除/恢复整批节点和边。
- 重复提交整批纵向避让，无节点重叠。
- 多选隐藏单节点浮层；`390x844` 无 document 级横向 overflow。
- Batch 33 专项、Batch 9/15/21/26-32、文档和工程门禁通过。

## 5. 不在本批

- 自动把当前画布全部素材解析成真实角色/场景/道具；
- 真实镜头拆分数量、时长分配、候选选择或自动拼接算法；
- 任务 ID、队列、失败重试、部分完成、取消任务或服务端状态同步；
- 文章截图中文字、精确节点数、精确坐标和连线端口的猜测；
- 把本地缩略图或 poster 宣称为本次长视频生成结果。

## 6. 实施状态

- [x] 证据边界、一次性截图识别、缺口排序和规格已落档
- [x] store transaction 与过程节点 renderer
- [x] 生成面板 graph handoff 与 busy 状态
- [x] Batch 33 专项 Playwright 和 clone screenshot ledger
- [x] 跨批回归、`npm run check`、实施收口和 commit/push
