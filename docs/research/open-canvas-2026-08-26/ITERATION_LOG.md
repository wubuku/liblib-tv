# Open Canvas 调研报告迭代历史

## 版本说明

本目录的报告是可持续更新的研究基线。每轮只记录已完成的研究/文档变更；业务代码和上游 submodule 的修改不属于本报告迭代。

## 2026-08-26：v1 初始基线

对应提交：`0d4e01d docs: research open-canvas upstream`

- 引入并固定 `ZeroLu/open-canvas` submodule；
- 浏览官网中文 landing page 和 `/zh/canvas` 空状态；
- 保存桌面/移动端截图；
- 建立 `PLAN.md`、`REPORT.md`、`SOURCE_ANALYSIS.md`、`RUNTIME_AUDIT.md` 和 `IMPLEMENTATION_IMPLICATIONS.md`；
- 初步识别 provider 声明与 current runner 的实现漂移；
- 明确“只研究、不编码”的授权门槛。

## 2026-08-26：v2 证据化优化

本轮目标是让报告从“长篇结论”升级为 agent 可检索、可引用、可复核的研究包：

- 新增 `EVIDENCE_MATRIX.md`，为核心事实、推断和未决项分配 OC claim ID；
- 新增本文件，保留研究报告的版本演进；
- 在主报告加入研究成熟度、证据置信度和“不能据此得出”的边界；
- 在源码分析中补充 API surface、入口漂移和验证限制；
- 在官网审计中补充证据等级、未登录限制和截图用途；
- 在实施影响文档中补充 claim ID 引用规则、依赖关系和停止条件；
- 保持 `src/`、其他开发者 WIP、上游源码和真实 provider 数据不变。

## 2026-08-26：v3 面向 LibTV UI/UX 的持续转译

本轮不新增上游功能判断，而是把研究成果接入后续复刻工作：

- 新增 `UIUX_TRANSLATION.md`，建立 LibTV 源站事实、Open Canvas 启发和 clone-only 决策的三层边界；
- 以当前已知的 LibTV 双浮层问题为 P0，拆解为坐标系统、层级、状态生命周期和边缘策略四类可测问题；
- 记录 Open Canvas selected overlay 的 `measured node + live viewport + screen anchor` 方法；
- 明确 LibTV 自有的 `NodeToolbar`/节点内编辑器合同不能被 Open Canvas 的 Panel 结构替换；
- 建立 `LIBTV-UIX-01` 至 `LIBTV-UIX-08` 的后续研究队列和统一 batch 文档模板；
- 未修改 `src/`，未触碰其他开发者 WIP，未将 Open Canvas provider/runtime 接入当前项目。

## 维护规则

1. 上游 submodule 更新时，新建一轮带日期的研究记录，不覆盖旧 commit 的结论；
2. 官网行为改变时，更新 `RUNTIME_AUDIT.md` 和证据截图，并在此记录变化；
3. 新增结论先进入 `EVIDENCE_MATRIX.md`，再写入 `REPORT.md`；
4. 任何从推断升级为事实的结论，必须补充直接源码或运行证据；
5. 每轮文档优化单独 commit + push，且暂存区不得包含他人 WIP。

## 2026-08-26：v4 交互模式目录

本轮目标是继续把 Open Canvas 的研究成果转化为后续 LibTV UI/UX 复刻的可执行研究队列，而不是开始编码：

- 新增 `INTERACTION_CATALOG.md`，覆盖选中双浮层、Quick Add/连接、视口、复制粘贴、媒体历史、运行/保存状态、层级和 onboarding；
- 补充 Open Canvas 源码中的 measured node/live viewport、screen/flow 双坐标、pending connection、内部子图 clipboard 和显式状态证据；
- 新增 OC-021 至 OC-025，确保主报告中的交互结论可以追溯到固定 commit 的行号；
- 建立 `LIBTV-UIX-09..16` 后续 batch，明确每个批次的源站取证内容、停止条件和“不得直接搬运”的边界；
- 保持 `src/`、FrameOS、upstream submodule 和其他开发者 WIP 不变。

## 2026-08-26：v5 Seedance 能力交叉研究

本轮继续围绕“Open Canvas 给 LibTV 后续 UI/UX 复刻的启发”推进，并读取用户指定的 LibTV Seedance 2.5 功能调研文档及当前仓库的原站复核记录：

- 新增 `LIBTV_SEEDANCE_CROSSWALK.md`，逐项对照 Seedance 2.5 生成、片段重拍、Auto Link、超长视频和逐帧拉片；
- 明确 Open Canvas 的 video history/index、引用分桶、descriptor、pending connection、graph transaction 和 run/save 状态，分别如何启发 LibTV 的视频版本、素材职责、过程图和反馈设计；
- 明确当前 clone 已有的 `VideoGenerationPanel`、`ShotBreakdownNode`、长视频过程图和 Auto Link 合同不能被 Open Canvas 五类节点模型替换；
- 新增 `LIBTV-SEEDANCE-OC-01..04` 后续取证批次，分别追踪输出版本、引用投影、长视频局部修改和拉片候选生命周期；
- 保持 `src/`、FrameOS、upstream submodule 和其他开发者 WIP 不变。

## 2026-08-26：v6 LibTV 现场几何抽查

本轮使用当前已打开的登录态 LibTV 画布进行只读节点切换和 DOM 矩形测量：

- 在 `929x874`、约 `27.81%` zoom 下确认图片节点选中态的顶部工具条为 `1092.5x49`，底部编辑面板外框为 `660x191`；
- 确认两个浮层都以图片节点中心为 anchor，底部 gap 约为 `16 * zoom`，节点靠近左边缘时负 x 和裁切是源站当前行为；
- 保存当前顶部图片处理动作顺序，并将现场记录写入 [`LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md#8-2026-08-26-浏览器现场几何抽查)；
- 明确这次 `1092.5x49` 与先前其他节点/状态的 `900.5x49` 必须按场景并列，不得未经归因覆盖；
- 没有提交生成、上传媒体、修改参数或写入远端画布，保持 `src/`、FrameOS、upstream submodule 和其他开发者 WIP 不变。
