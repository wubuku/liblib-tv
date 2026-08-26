# Open Canvas 上游研究计划

## 1. 目标

把 `ZeroLu/open-canvas` 作为可复核的开源研究对象引入当前仓库，回答以下问题：

1. 它实际解决的是哪一种画布问题，和当前 LibTV/FrameOS 克隆的边界有什么不同？
2. 图模型、节点状态、边约束、执行链路、持久化、provider 和 storage 如何协作？
3. 官网当前公开的交互是否与固定 commit 的源码能力一致？
4. 哪些设计适合借鉴，哪些会与当前项目的双路线架构、原站证据纪律或本地 prototype 边界冲突？
5. 在没有用户授权编码前，哪些工作可以形成清晰、可执行的后续任务队列？

## 2. 范围

### 必查

- submodule 版本、许可证、README、贡献与发布约束；
- Next.js 路由、画布列表、studio shell 和 React Flow 编排；
- `CanvasNodeData`、序列化/规范化、图校验、环检测和 store 事务；
- 上游输入解析、scene 推断、credit quote、task descriptor 和本地 runner；
- Cyberbara/OpenRouter/Replicate provider、上传接口和 S3-compatible storage；
- 多语言、provider 设置、JSON 导入导出、画布保存/冲突/模板 API；
- 官网落地页、托管应用入口、设置向导和可见的空状态。

### 不做

- 不在当前项目 `src/` 中编码或重构；
- 不改变上游 submodule 的 checkout、源码或依赖安装状态；
- 不在官网创建画布、输入 Key、上传文件、执行生成或修改远端数据；
- 不把官网营销文案当作源码事实；
- 不把 open-canvas 的设计直接替换当前 LibTV 的原站行为。

## 3. 方法

1. 先记录工作区状态，所有提交只暂存本任务新增的 submodule/研究文件；不使用 `stash`、不回滚其他人的 WIP。
2. 以 submodule 指向的 `cf3a906` 为唯一源码基线，使用 `rg`、行号和静态调用链阅读。
3. 将结论拆成三类：`源码事实`、`官网观察`、`面向当前项目的推断/建议`。
4. 对官网使用只读浏览：读取 DOM、标题、可见文本、入口结构和截图；登录/Key/生成/上传均不进行。
5. 把每个高价值能力写成“当前项目现状 → 上游证据 → 价值 → 风险 → 待授权动作”，避免只列功能名。
6. 完成报告后只运行不改代码的文档/仓库状态检查；不因研究需要启动或改动当前业务实现。

## 4. 交付物

| 文档 | 用途 |
|---|---|
| `README.md` | 研究入口和结论摘要 |
| `SOURCE_ANALYSIS.md` | 固定版本源码考古和模块证据 |
| `RUNTIME_AUDIT.md` | 官网只读观察、截图和事实边界 |
| `REPORT.md` | 深度报告、架构图、数据流、比较和决策 |
| `EVIDENCE_MATRIX.md` | 声明 ID、证据级别、可证明范围和待验证项 |
| `UIUX_TRANSLATION.md` | Open Canvas 启发到 LibTV 后续 UI/UX 复刻 batch 的转译 |
| `INTERACTION_CATALOG.md` | 选中、连线、视口、复制、媒体历史、状态和 onboarding 的交互模式目录 |
| `LIBTV_SEEDANCE_CROSSWALK.md` | Open Canvas 交互启发与当前 LibTV Seedance 2.5 能力链的逐项交叉研究 |
| `LIBTV_OVERLAY_GEOMETRY_MATRIX.md` | LibTV 五图片节点双浮层、工具条版本漂移和 clone 缺口矩阵 |
| `IMPLEMENTATION_IMPLICATIONS.md` | 仅作为待授权的后续设计队列 |
| `ITERATION_LOG.md` | 研究报告的版本演进和维护规则 |

## 5. 状态

- [x] 确认当前实际分支为 `master`，保护其他 WIP
- [x] 读取项目文档与已有研究入口
- [x] 查询并锁定上游 `main` commit
- [x] 以 git submodule 引入上游
- [x] 官网落地页和应用入口只读核对
- [x] 完成源码模块与数据流分析
- [x] 完成深度报告和当前项目映射
- [x] 完成 LibTV 五图片节点双浮层矩阵与 clone 静态差异审计
- [x] 文档检查、提交并推送研究成果

## 6. 验收标准

- 任何 agent 从本 README 能找到固定上游版本、完整报告和源码证据；
- 报告能解释“为什么这样设计”，而不只是复述 README；
- 每个跨项目建议都明确是推断/建议而非 LibTV 或 open-canvas 的事实；
- 没有触碰其他人已修改的截图、Batch 36 文件或业务代码；
- submodule 和研究文档均可通过 Git 历史复核。
