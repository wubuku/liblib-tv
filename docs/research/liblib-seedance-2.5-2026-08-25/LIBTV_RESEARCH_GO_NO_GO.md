# LibTV 后续复刻研究授权闸门

> 目的：收束当前“先调研、再借鉴、暂不编码”阶段，并为后续 agent 提供可执行的 go/no-go 判断。
>
> 当前结论不是产品上线建议，也不是后端开发批准。它只回答：在现有证据、安全边界和协作状态下，什么可以继续研究，什么可以申请编码，什么必须先补 fixture 或源站证据。

## 1. 总体决策

| 工作类别 | 当前决策 | 原因 |
|---|---|---|
| 研究文档、状态图、模式卡、依赖队列 | **GO** | 不改变业务行为，不触发源站写入；证据和入口已落档 |
| LibTV 双浮层、active tool、图片动作的 clone 编码 | **NO-GO，等待明确编码授权** | 已有较完整源站合同，但用户当前要求仍是只调研/借鉴 |
| Auto Link ghost/structured mention 编码 | **NO-GO，等待明确编码授权** | 需要改变编辑器数据结构、候选生命周期和 graph 事务 |
| 普通 Seedance 参数面板的细节校正 | **NO-GO，等待明确编码授权** | 视觉差距明确，但可能碰到其他开发者业务 WIP |
| 片段重拍、逐帧拉片结果态、超长视频过程图编码 | **NO-GO，先准备 disposable fixture + 明确授权** | 需要就绪视频、版本/时间范围语义和复杂状态回归 |
| 旋转、图层分离、标注保存、下载水印 | **NO-GO，先取得 disposable fixture + 源站证据** | 已观察到可能的 graph mutation、任务提交或浏览器副作用 |
| 真实 Provider、上传、计费、持久化、远端任务轮询 | **OUT OF SCOPE** | 不属于当前前端原型研究，需另行产品/后端合同 |

## 2. 当前研究已达到的决策成熟度

### 2.1 已经可以作为实现前合同的内容

- 图片节点标准上下双浮层的层级职责、node-center anchor、zoom gap、自然裁切和选择卸载；
- active image tool 会替换标准双浮层的状态边界；预览、标注、元素编辑、旋转和图层分离不能再统一当作一个 `addDerivedNode` 动作；
- 当前源站图片工具条动作集合、`w-fit` sizing 和 `1092.5x49` 当前版本，旧 `900.5px` 只保留为历史快照；
- Auto Link 是全局偏好 + 候选池 + inline ghost + structured mention；graph connection、reference role 和 mention token 是独立关系；
- Seedance 普通/超长生成的参数、费用和提交属于同一上下文，但文章中的数字只作采样证据；
- 五项能力共享 source node、media version、reference role、time range、run/node/save status 和 graph mutation boundary 六类研究底座；
- Open Canvas 只能提供 measured viewport、typed input、状态分离和 serialized subgraph 等一般机制启发，不能替代 LibTV 源站证据。

对应文档：[`LIBTV_UI_STATE_HIERARCHY.md`](LIBTV_UI_STATE_HIERARCHY.md)、[`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md)、[`LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md)、[`LibTVAutoLink.contract.md`](../components/LibTVAutoLink.contract.md)、[`LIBTV_DEPENDENCY_RISK_QUEUE.md`](LIBTV_DEPENDENCY_RISK_QUEUE.md) 和 [`OPEN_CANVAS_PATTERN_CARDS.md`](../open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md)。

### 2.2 尚不能升级为实现规格的内容

- 片段重拍在当前登录态就绪视频上的真实入口、端点包含规则、替换结果和版本保留方式；
- 逐帧拉片在当前源站的处理中、失败、部分成功、重试和结果复用生命周期；
- 超长视频过程图的真实任务拆分、局部重算、费用刷新和成片替换；
- 旋转/图层分离的最终提交方式、撤销边界和远端/graph 副作用；
- 文章中 `4s` 粒度、最多 `5` 段、`300s` 和积分值在未来版本中的稳定性；
- 所有真实 provider、上传、计费、保存和任务轮询实现。

## 3. 分批授权矩阵

| Slice | 研究状态 | 编码前必须具备 | 最小实现边界 | 不得顺手扩大的范围 |
|---|---|---|---|---|
| `LIBTV-UIX-01` 双浮层与 active tool | 合同较完整，clone 差距明确 | 用户明确授权；读 `ImageNode`/toolbar/panel 规格；local disposable fixture | 同一 viewport/rect；当前工具条动作集合；标准/active tool 生命周期 | 不引入自动避让、窗口居中、统一 page Panel 或新动作 |
| `LIBTV-UIX-02` Auto Link | 源站状态合同完整，clone 数据模型不符 | 用户明确授权；读 AutoLink 合同；编辑器 token 回归 fixture | 候选、ghost、单项/全量接受、structured mention、关系隔离 | 不接真实模型、不改变 Handle/edge flow、不做隐式全文解析 |
| `LIBTV-UIX-03` 生成参数上下文 | 普通/超长面板证据较完整 | 用户明确授权；确认当前 clone API 与他人 WIP 不冲突 | 字段可见性、模式切换、disabled、费用文案和本地提交态 | 不接 Provider、计费或远端持久化 |
| `LIBTV-UIX-04` 逐帧拉片 | 结构化结果有证据，实时态不足 | 用户明确授权；local disposable video fixture | 结果 group、source ID、时间范围、选择和本地失败/重试态 | 不冒充真实分析结果，不改共享源站 |
| `LIBTV-UIX-05` 片段重拍 | 入口/结果需要 fixture | 用户明确授权；disposable ready-video fixture；时间范围合同 | filmstrip、选段、token、版本化本地结果和撤销 | 不在共享项目生成/重拍，不默认覆盖原节点 |
| `LIBTV-UIX-06` 超长视频过程 | 本地 clone 过程图存在，源站细节不足 | 用户明确授权；disposable process fixture 或稳定业务接口 | 只读过程图、候选/镜头关系、明确 mock 状态 | 不伪造任务进度、费用结算或局部重算后端 |
| `LIBTV-UIX-07` 高风险图片动作 | 空态/入口已部分取证 | 用户明确授权；逐动作 disposable fixture；撤销/副作用方案 | 按源站事实实现一个动作一个状态分支 | 不把旋转、分层、标注和下载打包成一次“大补全” |

## 4. Fixture 规格

### 4.1 通用 clone fixture

在获得编码授权后，优先使用本地可重置 fixture，至少包含：

- 一个普通图片节点和一个普通视频节点；
- 一个带输出媒体的 ready-video 节点；
- 一个带 source/version/time-range metadata 的派生视频节点；
- 两个可被 Auto Link 候选识别的媒体引用；
- 一个可复现的多节点过程图；
- 可捕获选择、拖动、平移、zoom、空白点击、撤销和重新加载的初始状态。

fixture 每次测试后必须能回到相同 graph、viewport、selection 和媒体版本。不得依赖共享源站项目当前的节点位置、登录态或浏览器 local storage。

### 4.2 源站 fixture

若研究必须触发就绪视频、真实 Prompt、生成、重拍、标注保存或图层分离，则需要独立且可丢弃的源站项目/账号边界。没有该边界时：

```text
未知行为 -> 标记 BLOCKED_BY_FIXTURE
          -> 记录需要的操作和观察量
          -> 不在共享项目试探
```

源站 fixture 需要明确：谁负责创建、是否允许任务消耗、如何撤销/删除远端数据、截图和 DOM 证据保存到哪里、观察完成后如何确认没有遗留写入。

## 5. 编码授权请求的最小信息

后续如果要从研究切换到编码，授权请求至少应明确：

1. 允许修改的 route、组件、store 和测试文件；
2. 目标 slice，例如只做 `LIBTV-UIX-01`，不默认包含 Auto Link 或真实任务；
3. 是否允许修改现有 Playwright 脚本、截图基线和 fixture；
4. 允许的副作用边界：local-only、mock-only，还是允许使用独立源站 fixture；
5. 验收 viewport、zoom、移动端和回归命令；
6. 需要保留的其他开发者 WIP 和不能触碰的业务接口。

缺少这些信息时，默认保持本文件的 **NO-GO**，继续做文档或只读证据整理。

## 6. 编码后的验收顺序

获得授权后，每个 slice 按以下顺序单独完成：

```text
组件规格/源站证据
  -> 变更边界确认
  -> local fixture
  -> 最小实现
  -> desktop/mobile/zoom 浏览器验证
  -> graph/selection/undo 回归
  -> 文档与实施记录
  -> path-scoped commit + push
```

验证必须区分：

- `SOURCE_FACT`：源站能复现的事实；
- `CLONE_FACT`：当前 clone 已实现的行为；
- `CLONE_DECISION`：本次实现的原型选择；
- `REGRESSION_GUARD`：防止以后回退到旧快照的测试断言。

如果其他开发者业务 WIP 造成编译/测试失败，先记录阻塞；只有在业务接口稳定且确有必要时，才做最小测试夹具适配，不修改其业务实现。

## 7. 研究阶段关闭条件

当前阶段在以下条件满足后可以关闭并等待编码授权：

- UI 状态层级、Open Canvas 模式卡和五项能力依赖队列均已从正式索引发现；
- 当前图片双浮层、active tool 和 Auto Link 的合同可供 agent 直接引用；
- 文章线索、源站事实、clone 事实和未知项没有混写；
- 所有高风险动作都有 fixture 闸门和停止条件；
- 工作区其他开发者 WIP 未被丢弃、覆盖或通过 `stash` 干扰；
- 文档链接检查通过，每个关键批次有独立 commit/push。

**本轮最终决策：**研究闭环已具备；LibTV 复刻下一步可以进入“明确授权后的单 slice 编码评审”，但在获得授权前不得自动开始编码。
