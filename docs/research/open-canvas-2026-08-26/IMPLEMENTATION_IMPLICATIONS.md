# Open Canvas 对当前项目的实施影响

> 本文件是研究后的候选实施清单，不是授权。当前用户要求在获得允许前不能修改代码，因此本轮只建立任务边界、验收标准和依赖关系。

## 1. 实施前提

1. 研究对象固定为 `research/upstream/open-canvas` 的 commit `cf3a906bb8c35bb940d3267497e7f394b8f42582`。
2. 当前项目的 LibTV 与 FrameOS 仍保持 store/route 隔离。
3. 所有涉及 `src/` 的修改都要在用户明确授权后开始。
4. 任何 provider、上传或登录相关工作都不能用真实凭据做无意副作用验证。
5. 每个实现 batch 必须先补 source evidence，再改代码，再截图/测试，再 commit + push。

## 2. 候选批次

批次排序基于 [`EVIDENCE_MATRIX.md`](EVIDENCE_MATRIX.md) 的证据成熟度：先处理已由当前 LibTV 源站证实、且会影响视觉可信度的交互；再处理可纯函数验证的图语义；最后才考虑 provider 和持久化。

### Batch A：LibTV 选中节点浮层定位合同（最高优先）

**目标**：解决当前已发现的“点击图片节点后，上方工具条和下方参数面板位置乱”的视觉问题。

**先研究**：

- 源站选中图片节点时两层浮层相对 node rect 的定位；
- 画布平移/缩放、靠近边缘、移动端时的跟随和裁剪；
- 两层浮层的固定高度、滚动策略、z-index 和关闭条件；
- 多选、节点拖拽、节点删除和切换选中节点时的瞬态状态。

当前五节点矩阵已经确认：上方工具条使用屏幕空间 offset，底部参数面板使用节点内 flow-space offset 和 inverse zoom；两者共享 node center，但不共享 containing block。源站明确允许边缘裁切，不存在需要复刻的 viewport clamp。详见 [`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](LIBTV_OVERLAY_GEOMETRY_MATRIX.md)。

动作审计进一步确认：进入标注等 active tool 后，标准工具条和底部参数面板不再同时存在，而是切换为专用工具条 + 节点内编辑 surface。preview 则使用 page-level overlay，不改变节点选择。详见 [`LIBTV_IMAGE_ACTION_MATRIX.md`](LIBTV_IMAGE_ACTION_MATRIX.md)。

**候选设计**：保留 React Flow `NodeToolbar` 和节点内 inverse-scale panel 两条现有结构；先把当前动作集合、内容自适应宽度、无 clamp 边缘策略和选择生命周期固化为同一份 anchor contract，不新增碰撞修正或页面级重排。

**验收**：桌面 929px、移动 390px、至少两种 zoom、节点靠近四条边、图片和视频各一组截图；中心误差、screen/flow 两类 gap、当前动作集合、源站预期裁切和切换卸载均符合矩阵。音频节点只有取得同类源站浮层证据后才纳入。

### Batch A2：AutoLink Prompt mention 合同（高优先）

**目标**：替换当前 clone 的固定候选确认 popover 和字符串前缀写回，建立 source-shaped、可审核、可撤销的 AutoLink 前端状态链。

**当前证据**：生产 chunk 和 live DOM 已确认高级设置全局 toggle、connected/reference candidate pool、inline ghost、click/Tab/Shift+Tab、IME/stale guards，以及带 stable node ID/media type/ordinal 的正式 badge；详见 [`LIBTV_AUTOLINK_STATE_MATRIX.md`](LIBTV_AUTOLINK_STATE_MATRIX.md)。

**候选设计**：先共享 toggle preference 和 mention data contract，再实现不改写正文的单项 ghost 接受；最后才接入 graph connection、reference reorder 和一次性键盘提示。删除固定匹配数和固定 `陈默/咖啡` 数组，不用另一个视觉 popover 替代 editor 内联状态。

**验收**：图片/视频开关一致；接受前 Prompt 字符不变；Tab/Shift+Tab/Escape/blur/IME 行为稳定；重复 mention 共享 node ID/ordinal；reference 重排只更新 ordinal；未连接素材的 connect/mention 是一个可撤销 transaction。

**限制**：本轮没有编码授权；ghost 的精确视觉和真实 connect payload 仍需在专用测试项目补证，不能据静态 bundle 猜测像素或 API。

### Batch B：图模型/连接纯逻辑合同

**目标**：在不改变现有 LibTV 源站效果的前提下，整理 clone 内部对节点、边和引用类型的表达。

**候选内容**：

- versioned graph snapshot；
- 节点输入按 text/image/video/audio/reference 分类；
- 边去重、self-edge/cycle guard；
- copy/paste 只恢复内部连接；
- 将源站证据和 clone-only 规则分别记录。

**验收**：纯函数测试/固定 JSON fixture 覆盖非法边、反向 handle、环、重复 ID、复制内部边和历史媒体选择。

**限制**：不引入 Open Canvas 的 route mode，不合并 `frameosStore`。

### Batch C：模型能力矩阵的研究型抽象

**目标**：减少 LibTV Seedance/图片/音频节点中散落的参数判断，让字段可见性与源站证据关联。

**先研究**：

- 当前 LibTV 原站和现有 clone 各模型的比例、分辨率、时长、参考图规则；
- Open Canvas `model-options.ts` 的能力矩阵可迁移部分；
- 当前项目是否只做 UI 展示，还是需要生成 descriptor。

**验收**：每个模型的 UI 字段、默认值、禁用条件和证据链接可在一个表中查询；模型变更不影响 FrameOS。

### Batch D：本地 graph 快照与保存状态

**目标**：仅当当前产品需要刷新后恢复或接力研究时，再引入 local-first graph persistence。

**候选内容**：

- `graphVersion`、revision、dirty/saving/saved/error/conflict；
- 作者参数与运行输出分层；
- 原型阶段的 localStorage/JSON fixture 选择；
- 迁移和损坏恢复策略。

**暂缓原因**：当前项目主要是画布视觉/交互原型，过早引入持久化会扩大状态面和测试成本。

### Batch E：真实 provider adapter（暂缓）

**前置条件**：用户明确授权、provider 合同确定、密钥管理方案通过评审、没有把 UI registry 当作执行事实。

**最低验收**：

- UI 可选模型与实际 adapter 一一对应；
- 请求、轮询、错误、重试、取消和输出回写都有状态机；
- 不把真实 key 放入可被 client script 读取的普通 cookie；
- 明确计费、超时、上传和跨域策略；
- mock 和 live 两套验证路径分开。

**停止条件**：如果只能证明 UI 可见或 descriptor 可构造，不能证明 current route 可执行和结果可回写，则保持研究态，不把该 provider 标记为已支持。

## 3. 当前项目文件边界

| 任务 | 允许触碰的候选边界 | 当前状态 |
|---|---|---|
| 研究记录 | `docs/research/open-canvas-2026-08-26/`、`docs/index.md` | 本轮完成 |
| 视觉浮层 | LibTV 对应组件、相关 UI store、测试/截图 | 等用户授权 |
| 图语义 | LibTV `src/lib`/`src/types`/`src/store` 对应纯逻辑 | 等用户授权 |
| FrameOS | `src/app/frameos`、`frameosStore` | 本轮不触碰 |
| 上游 | `research/upstream/open-canvas` | 只读，不修改 |

## 4. 开始编码前的检查清单

- [ ] 用户明确允许修改代码；
- [ ] 已阅读对应 `docs/ARCHITECTURE.md`、`docs/LAYERS.md`、`docs/QUALITY.md`；
- [ ] 已搜索现有 `SCREENSHOT_ANALYSIS.md`，避免重复取证；
- [ ] 已把源站事实、证据推断、clone-only 决策分栏；
- [ ] 已确认当前工作区没有被其他开发者修改的目标文件；
- [ ] 已定义最小改动文件清单；
- [ ] 已定义桌面/移动/边缘状态验证截图；
- [ ] 已确定 batch commit message 与 push 目标；
- [ ] 已确认不使用 stash、不 reset、不 revert 他人 WIP。

## 5. 研究出口

当前最合理的下一步不是立即编码，而是继续补齐多 zoom、选择时序、元素编辑/旋转的无提交状态，以及专用空白项目中的 AutoLink ghost 视觉，再由用户授权 Batch A/A2。28% 五图片节点、preview、空 annotate、六动作 bundle 状态和 AutoLink 静态状态链已经完成；图层分离 live 取证必须等待任务/积分授权。具体视觉克隆仍应以 LibTV 源站证据为最高优先级。

## 6. 变更授权门槛

本研究包可以继续扩充文档、截图和 claim matrix；以下动作必须等待用户明确授权：

- 修改当前仓库任何 `src/` 文件；
- 修改当前 LibTV/FrameOS 的 store、route、节点组件或样式；
- 把 Open Canvas provider、storage 或执行代码接入当前项目；
- 使用真实 API key、上传素材、触发生成或修改远端站点状态。
