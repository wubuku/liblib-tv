# Open Canvas 对当前项目的实施影响

> 本文件是研究后的候选实施清单，不是授权。当前用户要求在获得允许前不能修改代码，因此本轮只建立任务边界、验收标准和依赖关系。

## 1. 实施前提

1. 研究对象固定为 `research/upstream/open-canvas` 的 commit `cf3a906bb8c35bb940d3267497e7f394b8f42582`。
2. 当前项目的 LibTV 与 FrameOS 仍保持 store/route 隔离。
3. 所有涉及 `src/` 的修改都要在用户明确授权后开始。
4. 任何 provider、上传或登录相关工作都不能用真实凭据做无意副作用验证。
5. 每个实现 batch 必须先补 source evidence，再改代码，再截图/测试，再 commit + push。

## 2. 候选批次

### Batch A：LibTV 选中节点浮层定位合同（最高优先）

**目标**：解决当前已发现的“点击图片节点后，上方工具条和下方参数面板位置乱”的视觉问题。

**先研究**：

- 源站选中图片节点时两层浮层相对 node rect 的定位；
- 画布平移/缩放、靠近边缘、移动端时的避让；
- 两层浮层的固定高度、滚动策略、z-index 和关闭条件；
- 多选、节点拖拽、节点删除和切换选中节点时的瞬态状态。

**候选设计**：建立一个由 node rect + viewport transform 计算的 anchor contract；上方工具条和下方参数面板分别拥有明确的主轴方向和碰撞修正，不用两个独立的 magic offset。

**验收**：桌面 929px、移动 390px、至少两种 zoom、节点靠近四条边、图片/视频/音频节点各一组截图，浮层无重叠、无越界、切换后不残留。

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

当前最合理的下一步不是立即编码，而是继续补齐 LibTV 源站的选中节点浮层证据，然后由用户授权 Batch A。Open Canvas 的研究价值已经被提炼为可验证的图模型、执行合同和状态管理参照；具体视觉克隆仍应以 LibTV 源站证据为最高优先级。
