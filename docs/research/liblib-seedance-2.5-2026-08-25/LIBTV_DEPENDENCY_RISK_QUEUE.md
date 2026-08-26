# LibTV Seedance 2.5 能力依赖、风险与研究队列

> 目的：在不编码的前提下，把 LibTV 当前已观察到的五项 Seedance 2.5 主推能力排成“依赖关系 + 证据闸门 + 研究价值”的队列。
>
> 本文关注 LibTV **有什么、如何在画布上呈现**。它不采用外部项目对“想要做什么”的实现展望，也不授权修改 `src/`、真实 Provider、共享源站项目或远端数据。

## 1. 结论先行

五项能力不是五条可以各自加按钮的功能线。它们共享三类底座：

```text
素材身份 / source node / media version
        |
        +--> 引用关系 / reference role / prompt token
        |          |
        |          +--> Auto Link
        |          +--> 逐帧拉片候选及其可复用引用
        |          +--> 片段重拍的 source version + time range
        |          +--> 超长视频过程图的中间镜头、候选和结果关系
        |
        +--> 生成参数上下文 / mode / model / duration / cost
                   |
                   +--> 普通 Seedance 生成
                   +--> 超长视频 Beta 参数分支
```

推荐研究顺序：

1. 先锁定图片/视频节点的选中态、浮层和输入身份合同；
2. 并行复核 Seedance 生成参数面板，因为它是所有视频能力的共同提交入口；
3. 再验证 Auto Link 的正式引用语义和逐帧拉片的结果卡身份；
4. 有了稳定的 source version、引用和时间范围后，才研究片段重拍；
5. 最后研究超长视频的多阶段过程图、局部重算、费用和状态分解；
6. 旋转、图层分离、标注保存和下载水印维持高风险暂停，不作为上述队列的隐式前置条件。

这是一条**研究和原型风险队列**，不是后端开发计划，也不是用户编码授权的替代品。

## 2. 五项能力的事实基线

| 能力 | 当前 LibTV 画布呈现 | 当前 clone 基础 | 关键未知 | 研究优先级 |
|---|---|---|---|---|
| Seedance 2.5 生成 | 视频节点下方约 `660px` 生成面板；模型、模式、画幅、清晰度、时长、音频、数量、积分同属提交上下文；普通和超长模式会改变可见参数 | 已有参数面板和本地提交态 | 当前 clone 参数与源站版本漂移；真实运行不在原型范围 | P0，并行主线 |
| Auto Link | 高级设置全局开关；从 connected/reference 素材候选池匹配；Prompt 内联 ghost；接受后形成带稳定 node ID、媒体类型和 ordinal 的正式 mention | 固定候选弹窗、全量接受、textarea 字符串前缀写回 | 候选作用域、token 生命周期、替换/删除和 graph 关系仍需授权后实现 | P0，底座 |
| 逐帧拉片 | 独立分析入口/节点；选择分镜、动态、音乐；结果为关键帧、动态片段和 BGM 波形等可复用卡片 | 已有 `shot-breakdown` 节点、三维选择和结果组 | 当前登录态缺少可安全执行的就绪视频结果态 | P1，引用产物 |
| 片段重拍 | 就绪视频顶部工具条进入；时间带按 `4s` 粒度；最多 `5` 段；选区写入 Prompt 的视频/时间范围 token；提交后替换目标区间 | 已有五段选择、disabled 尾段、token 投影和本地反馈 | 源站真实入口、边界帧、替换结果和历史版本关系未闭环 | P1，依赖 source version |
| 超长视频 Beta | 生成模式独立入口；时长范围可到 `30-300s`；底栏显示 `300s / 14700`；过程可在画布观察素材、镜头、候选和成片关系 | 已有 12 节点/22 边的本地 pending 过程图和 atomic undo/redo | 源站局部重算、状态拆分、费用/任务关系和结果替换仍不完整 | P1，依赖状态/版本 |

证据详见 [`LIBTV_FEATURE_GAP_MATRIX.md`](LIBTV_FEATURE_GAP_MATRIX.md)、[`LIVE_AUDIT.md`](LIVE_AUDIT.md)、[`LIBTV_VERIFICATION_COVERAGE.md`](LIBTV_VERIFICATION_COVERAGE.md) 和 [`LIBTV_UI_STATE_HIERARCHY.md`](LIBTV_UI_STATE_HIERARCHY.md)。

## 3. 依赖图

### 3.1 逻辑依赖

```text
                    +-----------------------------+
                    | 生成参数 / mode / model     |
                    | duration / cost / submit     |
                    +--------------+--------------+
                                   |
                                   v
                        +----------+----------+
                        | Seedance 生成上下文  |
                        +----------+----------+
                                   |
                  +----------------+----------------+
                  |                                 |
                  v                                 v
       +----------+----------+            +---------+----------+
       | 普通视频结果版本     |            | 超长视频过程/结果   |
       | source media version |            | shot/candidate/task |
       +----------+----------+            +--------------------+
                  |
                  v
       +----------+----------+
       | 稳定素材身份         |
       | node + media + version|
       +----+------------+----+
            |            |
            v            v
     +------+-----+  +---+------------------+
     | Auto Link  |  | 时间范围/片段语义    |
     | mention    |  | source + start/end   |
     +------+-----+  +---+------------------+
            |            |
            v            v
     +------+-----+  +---+------------------+
     | 逐帧拉片   |  | 片段重拍            |
     | 可复用产物 |  | 目标区间替换         |
     +------------+  +--------------------+
```

图中的箭头表示研究前提，不声称源站内部一定以同样的软件模块实现。例如“稳定素材身份”是从源站 Auto Link、画布结果和现有节点结构推导出的 clone 研究合同；只有源站行为确认后，才可升级为实现规格。

### 3.2 共享底座与分支

| 底座 | 依赖它的能力 | 如果底座未确定，不能先做什么 |
|---|---|---|
| source node identity | 五项能力全部依赖；尤其 Auto Link、拉片结果和重拍 | 不能只用媒体 URL 或显示标题作为引用主键 |
| media version / selected output | 生成结果、重拍、长视频过程 | 不能让下游引用静默跟随用户切换后的另一个候选 |
| reference role / typed mention | Auto Link、Seedance 生成、拉片输入 | 不能把 graph edge、reference role 和 prompt 字符串合并 |
| time range | 片段重拍、拉片动态片段、长视频镜头 | 不能把 `start/end` 当普通文案 token；需明确边界和单位 |
| run/node/save status | 普通生成、重拍、长视频、拉片分析 | 不能用一个 `loading` 覆盖编辑、任务、结果和保存反馈 |
| graph mutation boundary | 结果回画布、派生节点、过程图 | 不能把所有动作都实现为统一 `addDerivedNode` 或统一原节点回写 |

## 4. 队列条目

### Q0：节点上下文与素材身份

**优先级：P0，所有后续能力的共同前置。**

**要回答的问题：**

- 选中视频/图片节点时，顶部工具条和下方生成/编辑面板分别属于哪个 UI 层；
- 当前输出是节点当前媒体、候选历史中的一个版本，还是独立派生节点；
- 引用在 graph edge、reference role、Prompt mention 和提交 payload 之间如何保持身份；
- 节点失焦、多选、预览、active tool 和 graph mutation 时，引用/浮层/选择如何卸载。

**已有证据：**

- 图片双浮层的定位和替换已在 [`LIBTV_UI_STATE_HIERARCHY.md`](LIBTV_UI_STATE_HIERARCHY.md) 与 [`LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md) 落档；
- Auto Link 的候选、ghost、structured mention 和 graph 事务已在 [`LibTVAutoLink.contract.md`](../components/LibTVAutoLink.contract.md) 落档；
- 当前 clone 的差距和历史断言已在 [`LIBTV_VERIFICATION_COVERAGE.md`](LIBTV_VERIFICATION_COVERAGE.md) 标明。

**风险：**高。身份边界一旦错误，后面五项能力都可能“看起来能用”但引用错版本。

**进入下一步的闸门：**完成 source node / media version / reference role / mention token 的状态表；明确哪些是源站事实，哪些只能作为 clone-only 选择；获得编码授权后才进入实现。

### Q1：Seedance 生成参数上下文

**优先级：P0，可与 Q0 的文档研究并行。**

**源站事实：**模型和模式、画幅、清晰度、时长、音频、数量和预计积分集中在视频节点的生成面板；普通/超长模式改变参数可见性和费用展示。

**研究任务：**

1. 对普通和超长模式建立 control matrix：字段、默认值、可见/禁用、互斥项和提交前反馈；
2. 把当前可见数字记录为采样值，不把 `4-30s`、`30-300s`、`300s / 14700` 写成永久后端契约；
3. 分清参数草稿、提交状态、结果回画布和保存状态；
4. 将 Auto Link/视频引用/音频开关作为输入语义接入研究矩阵，而不是只检查表单视觉。

**风险：**中。它是高价值主流程，但真实 Provider 不属于当前前端原型边界。

**进入下一步的闸门：**源站普通/长视频面板的 DOM/截图和 clone 现状可以逐字段对照；所有未验证的 API、计费和任务细节保持 `UNKNOWN`。

### Q2：Auto Link 稳定引用

**优先级：P0，依赖 Q0。**

**研究任务：**

- 记录全局偏好和当前画布候选池的边界；
- 记录 ghost 出现、接受、批量接受、Escape、编辑、blur、替换和删除的生命周期；
- 建立 mention token 与 source node ID、媒体类型、ordinal、reference role 的映射；
- 验证连接关系、引用关系和 Prompt mention 关系是否能独立存在；
- 研究模型切换、候选重排、源节点删除时正式引用如何退化。

**风险：**高。现有 clone 的固定 popover/前缀写回容易把短期视觉结果误当成长期数据模型。

**进入下一步的闸门：**必须先更新 Auto Link 组件合同和验证覆盖；如果需要在共享项目输入 Prompt 或接受建议，直接标为 `BLOCKED_BY_FIXTURE`，不操作共享项目。

### Q3：逐帧拉片结果卡

**优先级：P1，依赖 Q0，部分依赖 Q1。**

**源站事实：**独立 `shot-breakdown` 能力将视频转成分镜、动态和音乐维度；结果呈结构化图像/视频/音频卡，可以继续作为参考。当前共享源站没有安全的 ready-video fixture 可供完整结果态探索。

**研究任务：**

- 用本地固定视频 fixture 记录输入节点、分析维度、结果组、selected result、source ID 和时间范围；
- 观察结果卡是原节点内历史、独立节点还是结果 group；
- 记录处理中、失败、重试和部分成功是否影响其它维度；
- 验证结果再次成为 Auto Link/Seedance 输入时，引用的是结果版本而不是显示标题。

**风险：**中高。结果组和多媒体类型会放大 graph identity、浮层和状态问题。

**进入下一步的闸门：**先完成 local disposable fixture 的只读结果态；没有 fixture 时只补矩阵和合同，不在共享源站触发分析。

### Q4：片段重拍

**优先级：P1，依赖 Q0 + Q1 + 视频 source version + time range。**

**源站/文章线索：**就绪视频顶部工具条进入，时间带按 `4s` 粒度选择，最多 `5` 段，选区成为 Prompt 中的视频/时间范围 token，提交后替换目标区间。数字和完整结果边界仍需以当前产品采样为准。

**研究任务：**

1. disposable ready-video fixture 上复核入口、工具条、filmstrip、选段禁用和 token 几何；
2. 记录区间单位、端点是否包含、相邻段是否允许重叠、最多段数在何处反馈；
3. 观察提交后是原节点替换、版本叠加、派生节点还是结果组；
4. 记录取消、失败、重试、返回画布和撤销的边界；
5. 验证下游引用在替换前后指向固定版本还是当前版本。

**风险：**高。需要就绪视频和可能的任务提交，不能使用共享项目试探。

**进入下一步的闸门：**必须有可丢弃 source fixture 和明确编码授权；没有二者时只维护研究文档。

### Q5：超长视频过程图

**优先级：P1，依赖 Q0 + Q1 + 状态/版本合同；在 Q3/Q4 之后。**

**源站事实：**生成模式存在超长视频独立入口，参数可扩展到 `30-300s`，费用/时长在提交上下文显示；文章证据显示过程包含素材、镜头、候选和成片关系。当前 clone 已有 12 节点/22 边本地 pending 过程图，但这只证明 clone 形态，不证明源站完整过程状态。

**研究任务：**

- 将过程拆成输入、分镜/镜头、候选、成片、失败和重算等可观察状态；
- 研究局部镜头重算是否生成新版本/新节点，是否影响成片；
- 记录费用、任务、节点和保存状态是否各自可见；
- 验证过程图在选择、预览、缩放、删除和撤销时的 graph 关系；
- 研究长视频结果是否可被片段重拍、逐帧拉片和 Auto Link 继续引用。

**风险：**高。复杂度和远端副作用最高，最容易把文章截图拼成未经证实的状态机。

**进入下一步的闸门：**先只读审阅现有 clone fixture 和已有文章证据；源站过程图需要 disposable project 或用户明确授权，不能在共享项目触发。

## 5. 可并行与不可并行

### 5.1 可以并行的研究

| 研究线程 | 并行条件 |
|---|---|
| 普通 Seedance 参数面板 | 不需要真实 ready-video；只读 DOM/截图和 clone 静态审计即可 |
| 双浮层与 active tool 几何 | 不需要 Provider；可用源站安全空态和本地 disposable clone fixture |
| Auto Link 合同 | 先做文档/静态 bundle 审计；实际输入和接受动作需 fixture |
| 逐帧拉片信息架构 | 先做已有独立节点、文章证据和本地 result group 静态审计 |
| Open Canvas 模式借鉴 | 固定 submodule 只读，不依赖 LibTV 远端写入 |

### 5.2 必须串行的研究

| 前置 | 后置 | 原因 |
|---|---|---|
| source node/media version | Auto Link、拉片、重拍、长视频 | 下游引用必须知道自己引用哪个版本 |
| time range contract | 片段重拍、动态片段、长视频局部重算 | 没有单位和边界无法验证替换结果 |
| Auto Link token contract | 多引用生成、拉片产物复用、重拍 Prompt | 不能把不可逆字符串当跨功能接口 |
| run/node/save status | 长视频过程、异步重拍、拉片失败/重试 | 复杂过程需要正交状态，而不是一个 loading |
| disposable source fixture | ready-video live 入口和结果态 | 共享项目不能承受 graph mutation 或任务提交 |

## 6. 风险登记

| 风险 ID | 风险 | 影响 | 触发条件 | 处理 |
|---|---|---|---|---|
| R-01 | 把文章数字当永久契约 | 参数 clone 错误、测试脆弱 | `4s`/`5`/`300s`/积分被直接硬编码为官方规格 | 标为采样证据，重新读取当前 DOM/bundle |
| R-02 | 共享源站没有 ready-video fixture | 无法安全验证重拍/拉片/视频工具条 | 入口只显示失败/空态 | 标记 `BLOCKED_BY_FIXTURE`，转本地 fixture 研究 |
| R-03 | Auto Link 字符串化 | 引用错节点或错版本 | 只保存显示文本/前缀 | 先完成结构化 token 合同和回归断言 |
| R-04 | 统一 `addDerivedNode` | 标注、预览、旋转、图层分离语义混淆 | 所有图片动作共用同一副作用 | 按 UI state / graph mutation / task 三类拆分 |
| R-05 | 运行和保存状态相互覆盖 | 异步结果覆盖编辑、冲突不可解释 | 单一 `loading`/`status` 字段 | 建立正交状态词汇，暂不接真实后端 |
| R-06 | 过程图假装源站事实 | clone 研究超出证据 | 用现有 12/22 本地图反推源站 | 明确 `CLONE_FACT`，等待 source fixture |
| R-07 | 其他开发者 WIP 干扰研究提交 | 丢失或污染业务工作 | workspace 有并发截图/业务变更 | 只做 path-scoped add/commit，不 stash/reset/revert |

## 7. 研究队列的验收标准

### 7.1 进入编码授权评审前，必须具备

- 一张 source node / media version / reference role / mention token 的状态表；
- 普通与超长生成面板的字段/状态/费用展示矩阵；
- Auto Link 的 ghost、structured mention、候选、删除和竞态合同；
- 逐帧拉片结果卡的 source ID、时间范围、媒体类型和结果 group 记录；
- 片段重拍的 ready-video fixture 要求、时间区间合同和版本替换问题清单；
- 超长视频过程图的“已证实 / clone-only / 未知”三栏状态图；
- 每项任务的 `BLOCKED_BY_FIXTURE` 或“可继续只读”的明确停止条件。

### 7.2 仍然不允许做的事情

- 不修改 `src/`、stores、节点组件、回归脚本或业务实现；
- 不修改 `research/upstream/open-canvas` submodule 内容；
- 不输入 Prompt、不接受 Auto Link、不上传、不生成、不保存、不下载、不发布；
- 不在共享项目试探旋转、图层分离、标注保存、ready-video 重拍或过程图生成；
- 不因“有一个相似的 Open Canvas 实现”就补齐 LibTV 未证实的功能。

## 8. 与现有文档的关系

- 五项能力和 clone 差距：[`LIBTV_FEATURE_GAP_MATRIX.md`](LIBTV_FEATURE_GAP_MATRIX.md)
- UI 状态层级：[`LIBTV_UI_STATE_HIERARCHY.md`](LIBTV_UI_STATE_HIERARCHY.md)
- 验证现状和测试授权边界：[`LIBTV_VERIFICATION_COVERAGE.md`](LIBTV_VERIFICATION_COVERAGE.md)
- 后续研究总计划：[`NEXT_RESEARCH_PLAN.md`](NEXT_RESEARCH_PLAN.md)
- Open Canvas 模式卡：[`OPEN_CANVAS_PATTERN_CARDS.md`](../open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md)
- Open Canvas 到 LibTV 的机制转译：[`UIUX_TRANSLATION.md`](../open-canvas-2026-08-26/UIUX_TRANSLATION.md)

**本队列的核心决策：**先稳定身份、引用、参数上下文和状态边界，再研究高风险视频结果与过程图；所有需要共享源站写入或就绪视频的未知，都由 fixture 闸门拦住，而不是用猜测填空。
