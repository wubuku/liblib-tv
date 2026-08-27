# StoryAI 3D Director Desk 借鉴专题

> 状态：`CURRENT_RESEARCH / CURRENT_GUIDANCE`
> 上游：`research/upstream/storyai-3d-director-desk`
> 固定版本：`8c8bd361790be4d37158a7430365e65546e358fe`
> 复核日期：2026-08-27
> 范围：调研、进展审计与后续建议；本专题不授权修改业务代码。

## 1. 为什么有这个专题

StoryAI 上游的研究和借鉴已经产生了 Batch 34-50、59 的大量历史记录、
17 个 focused verifier、95 份 Director 视觉证据，以及当前真实 R3F Director
实现；但结论长期分散在批次目录中。历史 batch 能解释“当时做了什么”，不能
单独回答以下当前问题：

1. 当前 LibTV 原型到底已经从 StoryAI 借鉴了什么？
2. 哪些能力已经超过固定上游，哪些基础能力反而尚未吸收？
3. 哪些结果是 StoryAI 上游事实、LibTV 原站事实、clone 运行事实或建议？
4. 下一步应继续堆功能，还是先补工程可靠性与源站证据？

本目录把这些问题收敛为稳定的专题入口。批次文档继续保留历史 provenance，
但新的 agent 应先读本目录，再按链接下钻。

## 2. 建议阅读顺序

1. [`PROGRESS_AUDIT_2026-08-27.md`](PROGRESS_AUDIT_2026-08-27.md)：当前进展、
   能力矩阵、成熟度和主要风险。
2. [`BORROWING_DECISION_MATRIX.md`](BORROWING_DECISION_MATRIX.md)：StoryAI 模式
   哪些继续采用、改造、暂缓或拒绝。
3. [`NEXT_RESEARCH_AND_IMPLEMENTATION_ROADMAP.md`](NEXT_RESEARCH_AND_IMPLEMENTATION_ROADMAP.md)：
   后续研究和待授权实施顺序。
4. [`EVIDENCE_MATRIX.md`](EVIDENCE_MATRIX.md)：所有关键主张的证据等级、路径和
   不可推出结论。
5. [`PLAN.md`](PLAN.md)：本轮调研计划、完成条件和范围边界。
6. [`ITERATION_LOG.md`](ITERATION_LOG.md)：专题迭代与维护历史。

历史起点仍是
[`../liblib-canvas-batch34-2026-08-26/README.md`](../liblib-canvas-batch34-2026-08-26/README.md)；
具体能力的实现合同位于 Batch 35-50、59 目录。

## 3. 当前结论

### 3.1 已经取得的进展

当前 clone 已经正确吸收 StoryAI 最有价值的产品骨架：

- React Flow 画布中的 Director 节点只负责进入工作区；
- Director 是 lazy-loaded、全屏、独立 store 的 R3F authoring island；
- 对象树、真实 3D 视口和 selection-driven Inspector 组成稳定三栏工作台；
- 机位、画幅、九宫格、截图、截图图库和回流画布构成完整闭环；
- 资源库、本地模型描述符、群组/群演和响应式 shell 扩展了场景搭建能力；
- typed timeline、姿态轨、运动路径、速度曲线、预设运镜、浏览器视频导出和
  手机虚拟运镜已经明显超过固定 StoryAI 上游的静态导演台能力。

2026-08-27 的只读运行复核确认：桌面工作区、非空 WebGL、对象树、Inspector、
时间线、5 类资源库、预览后加入场景、graph 隔离和侧栏折叠均可工作，未观察到
console/page error。

### 3.2 不能宣布“完成”的原因

当前 Director 更接近“功能丰富的连续 frontend prototype”，还不是“可靠的
项目级创作子系统”。最高价值缺口集中在基础层：

- Director 状态仍是单例 session；没有按 canvas/node 隔离的可迁移项目文档；
- 缺少 Director 内部 undo/redo、copy/paste、对象删除和批量编辑事务；
- 缺少 project JSON 的严格导入/导出、schema version/migration 和恢复路径；
- FBX/OBJ 目前只是 data URL descriptor + proxy object，不是真实 mesh loader；
- 缺少全景图输入、场景整体变换和较完整的场景设置；
- 单机位 fixture 很强，但多机位创建、删除、重命名和 shot lifecycle 不完整；
- 已认证 LibTV Director DOM/CSS 和交互运行证据仍不足，source-exact fidelity
  不能由 StoryAI 或 clone 截图替代；
- 17 个 verifier 分散在历史 batch，没有一个“当前 Director 总验收入口”。

### 3.3 下一步总原则

暂停继续增加独立亮点功能，先进入一次 **reliability plateau**：

1. 先定义 project/session/owner/history/resource 合同；
2. 再在明确编码授权后补项目持久化、编辑安全和真实资产入口；
3. 最后用新的 LibTV authenticated evidence 校准 UI/UX 和产品语义。

这不是否定现有成果，而是保护已经形成的 13,563 行 Director 实现，避免更多
能力继续建立在单例 session、proxy asset 和分散 verifier 之上。

## 4. 证据纪律

本专题统一使用以下标签：

| 标签 | 含义 |
|---|---|
| `UPSTREAM_FACT` | 固定 StoryAI SHA 的源码、构建或测试事实 |
| `REMOTE_FRESHNESS_FACT` | 2026-08-27 远端 `main` 与固定 SHA 一致 |
| `LIBTV_SOURCE_FACT` | 已保存的 LibTV 原站 bundle/DOM/截图事实 |
| `CLONE_STATIC_FACT` | 当前提交代码可直接证明的事实 |
| `CLONE_RUNTIME_FACT` | 2026-08-27 本地只读浏览器复核事实 |
| `HISTORICAL_RECORDED_PASS` | 历史 verifier 的已记录结果，不自动等于当前回归通过 |
| `RECOMMENDATION` | 面向后续的建议，不是已实施行为 |
| `UNKNOWN` | 证据不足，不允许用 StoryAI 或 clone 行为补写成 LibTV 事实 |

## 5. 维护规则

- StoryAI submodule SHA 变化时，先按 `EVIDENCE_MATRIX.md` 标记受影响主张，再
  更新结论；不要直接覆盖旧版本事实。
- Director 业务行为变化时，更新 progress audit、decision matrix、roadmap 和
  component coverage；历史 batch 不回写成“当前真相”。
- 新 LibTV authenticated evidence 优先写入 dated source record，再更新本专题；
  不把 clone screenshot 升级为 source screenshot。
- 没有明确编码授权时，本专题只触发研究、合同、fixture 和 verifier 规划。
- 上游代码 MIT 不等于上游模型、贴图、缩略图和 README 图片可直接再分发。
