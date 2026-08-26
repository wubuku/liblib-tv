# LibTV / Open Canvas 后续研究执行计划

> 批次：第十四批计划落档
> 批准状态：用户已批准“先调研、再借鉴、暂不编码”的后续路线
> 记录日期：2026-08-26
> 当前分支：`master`

## 1. 目标

继续围绕 LibTV 的实际产品表现推进 UI/UX 复刻研究，先消除影响实施决策的高价值不确定性，再把 Open Canvas 固定版本中的通用工程机制转译成可审查、可验证的启发。

本计划不授权修改 `src/`，不授权修改 FrameOS，不授权修改 upstream submodule 内容，也不授权在共享 LibTV 项目上执行可能产生远端写入或 graph mutation 的操作。

## 2. 已批准执行顺序

| 顺序 | 研究项 | 产出 | 状态 |
|---:|---|---|---|
| 1 | LibTV UI 状态层级图 | 节点、双浮层、active tool、预览、任务和 graph mutation 的状态合同 | 已完成 |
| 2 | Open Canvas 高价值模式卡 | measured viewport、typed inputs、run/save 状态、serialized subgraph 四张模式卡 | 已完成 |
| 3 | 五项能力依赖/风险队列 | Auto Link、逐帧拉片、片段重拍、长视频和生成面板的依赖顺序与证据闸门 | 已完成 |
| 4 | 编码授权前 go/no-go | 可继续只读研究、可授权编码、必须先取得 disposable source fixture 的清单 | 待执行 |

每完成一项，必须先更新对应文档和索引，再进行文档校验；每个关键进展单独 commit 并 push。

## 3. 研究方法

### 3.1 证据优先级

1. 当前登录态 LibTV DOM、computed rect、可复现的静态 bundle 事实；
2. 已保存的源站结构化 JSON 和截图分析；
3. 2026-08-07 第三方文章中的功能截图与文章陈述；
4. Open Canvas 固定 commit `cf3a906bb8c35bb940d3267497e7f394b8f42582` 的源码启发；
5. clone 当前代码和既有回归脚本，只用于确认 clone 现状，不用于反推源站事实。

每条结论继续拆成 `SOURCE_FACT`、`ARTICLE_EVIDENCE`、`OPEN_CANVAS_INSPIRATION`、`INFERENCE` 和 `CLONE_DECISION`。

### 3.2 允许的无编码工作

- 阅读、整理和交叉链接现有 Markdown、JSON、截图分析和源代码；
- 从当前源站读取 DOM、可见文本、test id、computed style 和静态资源信息；
- 在不产生写入的前提下复核已知安全空态，例如预览或已确认可退出的空编辑态；
- 设计状态图、数据合同、验证断言和后续实现切片；
- 运行 `python3 scripts/verify-docs.py` 和其他不写入共享业务状态的文档检查。

### 3.3 明确禁止的源站动作

- 输入或提交 Prompt；
- 接受 Auto Link 建议、切换 Auto Link 设置或建立新的引用连接；
- 上传、生成、保存、下载、发布或分享；
- 继续在共享项目上试探旋转、图层分离、标注保存和可能创建派生节点的入口；
- 为取得 ready-video 结果而修改远端项目。

若研究问题必须执行上述动作，先把问题标记为 `BLOCKED_BY_FIXTURE`，记录所需 disposable source fixture，不用共享项目冒险取证。

## 4. 预期研究结果

### 4.1 LibTV UI 状态层级图

应回答：

- 标准图片/视频双浮层分别属于哪一层；
- active image/video tool 如何替换标准浮层；
- preview 为什么属于 page-level overlay；
- 哪些转换只改变 UI，哪些转换改变 node data、nodes/edges 或任务状态；
- selection、pan、zoom、multi-selection 和 virtualization 如何影响浮层生命周期。

### 4.2 Open Canvas 模式卡

每张卡应记录：

- 固定源码文件和行号；
- 上游机制解决的问题；
- 对 LibTV 哪项能力有启发；
- 必须服从的 LibTV 源站事实；
- 不可直接搬入的上游规则；
- 后续可验证的 clone-only 断言。

### 4.3 五项能力依赖队列

至少保留以下依赖关系：

```text
素材身份 / 引用关系
  -> Auto Link
  -> 逐帧拉片候选产物
  -> 片段重拍的源版本与时间区间
  -> 超长视频过程图与局部重算
```

该顺序是研究和原型风险排序，不是产品后端承诺，也不是用户授权编码的替代品。

## 5. 授权门槛

| 工作 | 当前能否执行 | 需要的前提 |
|---|---|---|
| 文档、状态图、模式卡、依赖队列 | 可以 | 继续保持只读/文档-only |
| 图片 toolbar 当前动作集合与标准定位实现 | 暂不编码 | 用户明确授权修改 clone |
| 预览、空标注态 | 暂不编码 | 用户明确授权修改 clone |
| Auto Link ghost/structured mention | 暂不编码 | 用户明确授权 + 组件合同已读 |
| 片段重拍/拉片结果态 | 暂不编码 | 用户明确授权 + local disposable fixture |
| 旋转、图层分离、下载水印 | 暂不编码 | 用户明确授权 + disposable source/clone fixture |
| 真实 Provider、上传、计费、远端持久化 | 不在本计划范围 | 单独的产品/后端授权和接口合同 |

## 6. 变更与协作规则

- 工作区可能同时存在其他开发者的业务、截图、脚本和文档 WIP；不使用 `stash`，不 reset，不 checkout 覆盖，不删除未跟踪文件；
- 只对本批明确新增或修改的路径执行 `git add`；发现他人已暂存内容时，使用 path-scoped commit 保留其 index 状态；
- 不为文档-only 研究运行会写入共享截图或业务状态的完整回归；
- 若编译或测试被他人 WIP 阻塞，先记录阻塞信息。只有在业务接口确认稳定后，才允许做最小测试夹具适配，禁止修改业务实现；
- 每个关键研究进展都要在 [`ITERATION_LOG.md`](../open-canvas-2026-08-26/ITERATION_LOG.md) 追加历史记录，并 commit/push。

## 7. 验收标准

- 本计划从 Seedance 研究 README、research index、docs index 和 Big Picture 可发现；
- 四项研究产出都区分源站事实、Open Canvas 启发、推断和 clone 决策；
- 每一项高风险未知都有停止条件和 fixture 前提；
- 没有修改业务代码、FrameOS 或 upstream submodule 内容；
- 每个关键进展均有独立 commit/push，文档链接检查通过。
