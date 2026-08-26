# Batch 34 计划：导演台上游代码考古与 UX 借鉴评估

## 1. 任务背景

Batch 33 已完成并推送。下一批最高优先级是“导演台”功能的 UI/UX 复刻。
用户指定开源项目：

```text
https://github.com/jiguang132/storyai-3d-director-desk.git
```

本批先回答“这个既有复刻有什么值得借鉴”，再决定如何实现。研究结果必须让
后续 agent 能在会话中断后接力，不依赖当前模型记忆。

## 2. 事实分层

| 层级 | 允许写入的内容 | 不能越界 |
|---|---|---|
| LibTV source fact | 原站登录态 DOM、交互、截图和已存证据 | 不能用上游源码补齐原站未知行为 |
| Upstream implementation fact | 子模块固定 commit 中真实存在的文件、依赖、组件、状态和交互 | 不能把它写成 LibTV 原站事实 |
| Clone inference | 基于两边证据推导的产品映射或适配方案 | 必须标注推断，不伪装成证据 |
| Clone-only decision | 当前原型为可验证性做的数量、样式、mock 和状态选择 | 不能反向污染 source evidence |

## 3. 研究问题与价值排序

| 研究项 | 对导演台复刻的价值 | 本批决策 |
|---|---:|---|
| 工作区信息架构：顶部模式、左对象树、中视口、右属性面板 | 5 | 必须分析 |
| 3D 场景对象与选中态的实体/状态模型 | 5 | 必须分析 |
| 机位视角、导演视角、取景框、九宫格和截图记录 | 5 | 必须分析 |
| 场景/角色/模型/相机属性编辑和即时反馈 | 5 | 必须分析 |
| 镜头列表、镜头元数据和时间线关系 | 4 | 必须分析，区分已实现和 README 宣称 |
| 本地工程保存、导入导出和嵌入通信 | 4 | 必须分析，评估边界 |
| Three.js/R3F 运行时移植到当前 Next.js/React Flow | 4 | 必须分析适配成本 |
| 上游模型库和示例素材 | 2 | 只核对许可证和引用，不直接复用 |
| 上游测试缺口和潜在回归风险 | 3 | 必须记录 |
| 原站当前时间轴、运动路径、动画导出与手机运镜 | 5 | 必须建立与上游的差距矩阵 |

## 4. 实施批次

### Batch 34-A：上游固定与代码考古

1. 引入 git submodule 到 `research/upstream/storyai-3d-director-desk`；
2. 记录 submodule URL、branch、commit、许可证和工作树状态；
3. 读取 README、`package.json`、入口、目录、核心组件、store、类型和测试；
4. 绘制源码到用户能力的映射；
5. 记录上游明确实现、README-only 声明和未验证项。

### Batch 34-B：可借鉴 UX 与适配矩阵

1. 按工作区、对象树、视口、属性面板、镜头、持久化、快捷键拆分 UX；
2. 对照当前 LibTV React Flow + Zustand 架构；
3. 标出可直接借鉴的 R3F 运行时、需要适配的代码和不可直接移植的资产；
4. 形成下一批最高价值实现候选；
5. 本批不修改产品运行时代码。

## 5. 交付文档

```text
docs/research/liblib-canvas-batch34-2026-08-26/
├── README.md
├── PLAN.md
├── SOURCE_EVIDENCE.md
├── LIBTV_DIRECTOR_EVIDENCE.md
├── CODE_ARCHAEOLOGY.md
├── UPSTREAM_SCREENSHOT_ANALYSIS.md
├── REPLICATION_REFERENCE_MATRIX.md
├── BORROWABLE_UX.md
├── PORTABILITY_MATRIX.md
└── IMPLEMENTATION.md
```

## 6. 验收标准

- 子模块可由新 clone 按 `.gitmodules` 复现，并固定到明确 commit；
- 许可证、依赖、入口、目录、核心源码和测试状态均有文件级引用；
- 文档明确区分 LibTV 原站事实、上游实现事实和 clone 决策；
- 至少列出 5 项高价值可借鉴 UX，并说明为什么、借什么、不借什么；
- 对当前 `canvasStore`、React Flow 节点、浮层和路由边界给出适配判断；
- 不复制上游源码、模型、贴图或示例资源到 `src/`；
- `npm run docs:check` 和 `git diff --check` 通过；
- 实施结果、固定版本、验证命令和后续接力入口写入 `IMPLEMENTATION.md`。

## 7. 保护点

- [x] Batch 33 实现已提交并推送：`2bf1617`
- [x] Batch 34 计划和初始证据边界已落档
- [x] 子模块固定版本和许可证核对
- [x] 代码考古与 UX 借鉴文档
- [x] 适配矩阵、验证和实施结果
- [x] Batch 34 commit/push: research `e1d20ef` plus handoff metadata `84a7c59`,
  both pushed to `origin/master`

Parent verification is complete:

- `npm run docs:check` passed;
- `git diff --check` passed;
- `npm run check` passed with 9 existing lint warnings and no errors.

## 8. Verified Research Conclusion

The upstream project is most valuable as a reference for editor interaction
contracts:

1. full-bleed three-zone workbench;
2. semantic tree plus selection-driven inspector;
3. first-class shot records linked to visible camera objects;
4. visible framing guides and capture history;
5. grouped selection, batched undo and scoped persistence.

The first LibTV implementation should reuse the existing replication as the
static R3F director-workspace baseline: scene schema, viewport, object tree,
selection-driven inspector, camera records, framing and capture return. React
Flow remains the host graph and R3F owns the director viewport. The current
LibTV-only timeline, motion-path, animation-export and phone-camera layers follow
after that baseline is integrated. External model catalogs remain a separate
asset and licensing decision.
