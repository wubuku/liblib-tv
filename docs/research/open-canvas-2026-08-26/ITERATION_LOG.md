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
