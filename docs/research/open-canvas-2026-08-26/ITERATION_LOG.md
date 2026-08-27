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
- 同一视口下补测失败视频节点：下方生成面板外框为 `660x273.797`，仍以节点中心和 `16 * zoom` 间距锚定；失败态没有观察到就绪视频顶部处理工具条；
- 确认两个浮层都以图片节点中心为 anchor，底部 gap 约为 `16 * zoom`，节点靠近左边缘时负 x 和裁切是源站当前行为；
- 保存当前顶部图片处理动作顺序，并将现场记录写入 [`LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md#8-2026-08-26-浏览器现场几何抽查)；
- 明确这次 `1092.5x49` 与先前其他节点/状态的 `900.5x49` 必须按场景并列，不得未经归因覆盖；
- 没有提交生成、上传媒体、修改参数或写入远端画布，保持 `src/`、FrameOS、upstream submodule 和其他开发者 WIP 不变。

## 2026-08-26：v7 五图片节点矩阵与工具条版本归因

本轮继续使用已打开的登录态 LibTV 画布，只读复测全部五个现有图片节点：

- 新增 [`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](LIBTV_OVERLAY_GEOMETRY_MATRIX.md) 和结构化 JSON，记录五组 node/toolbar/panel rect、中心误差、上下 gap、panel 高度和内容态；
- 确认五个节点当前都使用 `1092.5x49`、13 按钮的同一工具条，不支持“宽度由图片内容态决定”的旧假设；
- 将 `900.5 -> 1092.5` 归因为源站时间版本漂移：新增 `元素编辑 / 图层分离` 两个 `88px` 按钮及两个 `8px` 间距；
- 对照 clone 静态实现，确认其仍固定 `900.5px`、缺两个新文字动作，并以 `撤销 / 重做` 替代源站四个末端图标动作；
- 修订 ImageNode 规格和实施候选，明确保留当前双 anchor 结构、禁止新增 viewport clamp，下一步优先研究动作语义和多 zoom 时序；
- 没有修改 `src/`、FrameOS、upstream submodule、其他开发者截图或 Director WIP，也没有写入 LibTV 远端画布。

## 2026-08-26：v8 图片工具条动作状态审计

本轮从当前页面加载的 128 个 LibTV chunks 中定位图片工具条实现，并只对无任务风险的动作做 live 复测：

- 新增 [`LIBTV_IMAGE_ACTION_MATRIX.md`](LIBTV_IMAGE_ACTION_MATRIX.md)，将元素编辑、图层分离、标注、旋转、下载和预览按 UI 状态、保存/任务边界与 clone 价值分级；
- 确认元素编辑进入 `InteractiveImageEditMode`，使用 point/box/brush records，只有显式生成才创建/复用输出节点并提交任务；
- 确认图层分离拥有 splitting/ready/redrawing/merging composition 状态和任务提交路径，因此没有在当前研究画布上点击；
- live 确认预览是全屏 `MediaPreviewOverlay`，显示当前图片和水印，关闭后保持节点选择与参数不变；
- live 确认空标注态以 `536x49` 专用工具条替换标准工具条、隐藏底部生成面板，并在节点上挂 DPR=2 的绘制 canvas；Escape 可无修改退出；
- 将 clone 的统一 `addDerivedNode` 行为识别为关键语义缺口，并记录 preview -> editingImageTool -> task-backed composition 的待授权实施顺序；
- 没有绘制、保存、下载、上传、生成或修改源站画布，也没有触碰当前仓库 `src/` 和其他开发者 WIP。

## 2026-08-26：v9 AutoLink 状态与数据契约审计

本轮继续使用当前登录态画布和页面已加载的生产 chunks，只进行节点选择、高级设置 disclosure 和 DOM 读取：

- 新增 [`LIBTV_AUTOLINK_STATE_MATRIX.md`](LIBTV_AUTOLINK_STATE_MATRIX.md) 和结构化 JSON，记录全局开关、候选池、ghost suggestion、接受/拒绝键盘路径、mention commit 和 graph connect 分支；
- live 确认图片 AutoLink 位于高级设置折叠区；`660x191` 面板展开为 `660x275.5`，`627x36` toggle row 中的 `38x20` switch 为 checked；
- live 确认参考缩略图和 Prompt mention 是两层状态：`分镜 #2` 有两个 `48x48` draggable references，但 Prompt 本身没有正式 mention；
- live 提取视频 Prompt 的四个正式 badge，确认媒体 token 保存 stable node ID/media type/ordinal，同一 `i-1FQ9tErTcC` 在两处都显示“图片 1”；
- 从当前 chunks 确认 AutoLink 先注入 inline ghost，再由 click/Tab/Shift+Tab 接受；Escape、编辑、blur 清理建议，并有 IME、suspend 和 stale-result guards；
- 将 clone 的固定 `陈默/咖啡` 候选、独立确认 popover、全量接受和字符串前缀写回标记为当前源站语义缺口；
- 没有编辑 Prompt、切换开关、接受 mention、创建连接、生成、上传、下载或保存，也没有修改 `src/`、FrameOS、upstream submodule 和其他开发者 WIP。

## 2026-08-26：v10 双浮层多 Zoom 与生命周期审计

本轮继续使用当前登录态画布，只切换源站 zoom 菜单、节点选择和空白画布选择态：

- 新增 [`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](LIBTV_OVERLAY_MULTIZOOM_MATRIX.md) 和结构化 JSON，补齐 28%/34%/50%/100% 的几何与 virtualization 边界；
- 直接 live 确认 28%/34%/50% 下工具条均为 `1092.5x49`、面板均为 `660x191`，两者保持 node center；
- 确认底部面板 gap 在 28%/34%/50% 分别为 `4.525/5.430/8px`，均等于 `16 * zoom`；
- 发现顶部工具条 gap 在 28%/34%/50% 分别为 `16.794/18.152/22px`，三点支持 `10 + 24 * zoom` 的近似模型，但仍标为待源码确认的 source contract，不用固定 `16px` 概括；
- 空白画布点击会同时卸载 toolbar/panel，`适合屏幕`恢复约 28% 后可重新选择图片并恢复一组双浮层；
- 100% 时选中 node 因源站可见性策略离开 DOM，记录为 virtualization boundary，不把缺失 DOM 误判成业务选择丢失；
- 没有修改节点数据、Prompt、AutoLink、生成任务、上传、下载或远端保存，也没有触碰 `src/`、FrameOS、upstream submodule 和其他开发者 WIP。

## 2026-08-26：v11 顶部工具条间距归因补测

本轮在不移动节点、不修改画布数据的前提下，补测源站 zoom 菜单的第三个直接可见档位，并把观察和推断分开：

- 在 fit-view 约 `28.28%` 基线后使用一次“放大”得到约 `33.94%`，重新测得图片节点、顶部工具条和底部面板的 screen rect；三者仍以同一节点中心为 anchor；
- 28% / 34% / 41% / 50% 的顶部 gap 分别为 `16.794 / 18.152 / 19.778 / 22px`，底部 gap 分别为 `4.525 / 5.430 / 6.516 / 8px`；后者继续精确符合 `16 * zoom`；
- 四个顶部样本可用 `10 + 24 * zoom` 拟合，最大残差约 `0.008px`；随后从当前生产 chunk 确认 toolbar host 的 `top: nodeTop - 24 * zoom - 10` 与 `translateY(-100%)`，因此该模型已升级为标准工具条的 source fact，仍需把 clone 的 `NodeToolbar offset=16` 映射到这个结果；
- 100% 档仍观察到选中节点 DOM 被可见性/virtualization 策略移出，但 toolbar host 保留在 DOM；这说明 clone 的验证必须同时检查 selection state、host presence 和 node DOM presence，不能只用节点 DOM 是否存在判定双浮层是否失效；
- 将本批结构化样本追加到 [`libtv-overlay-multizoom-audit-2026-08-26.json`](../liblib-seedance-2.5-2026-08-25/libtv-overlay-multizoom-audit-2026-08-26.json)，并同步矩阵、Big Picture、ImageEditPanel 规格和实施影响文档；
- 没有修改 `src/`、FrameOS、upstream submodule、其他开发者截图或 Director WIP，也没有写入 LibTV 远端画布。

## 2026-08-26：v12 图片动作的安全进入边界

本轮继续遵守“不生成、不上传、不保存”的限制，重点验证两个此前只由 bundle 推断的高价值动作：

- `元素编辑` 在 `41%` zoom 的空态会替换标准双浮层，出现 `272x44` 专用 toolbar、`250.852x203.711` mode root、`250.211x141.711` edit stage 和 `400x50` 空 record panel；初始 mask/guide、point/box/brush 和 disabled undo 都是可见合同；Escape 可恢复标准 toolbar/panel；
- `旋转` 的一次入口点击在当前共享 fixture 中实际新增并选中了“旋转与镜像”派生节点；随后一次 `Meta+Z` 将其撤销。没有继续改变角度/镜像，也没有打开 dirty modal、保存、上传或生成；因此旋转入口升级为“可能先发生 graph mutation”的高风险动作；
- 将元素编辑空态和旋转入口副作用分别写入 [`LIBTV_IMAGE_ACTION_MATRIX.md`](LIBTV_IMAGE_ACTION_MATRIX.md)、[`LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)、[`EVIDENCE_MATRIX.md`](EVIDENCE_MATRIX.md)；后续如需非空 record 或旋转 modal，必须使用可丢弃副本或取得明确授权；
- 没有修改 `src/`、FrameOS、upstream submodule、其他开发者截图或 Director WIP；对源站的唯一 graph 操作是为恢复误触发动作而执行一次撤销。

## 2026-08-26：v13 双浮层定位合同

本轮把前十二轮的几何和动作证据收敛成一个供后续 agent 直接使用的组件级合同：

- 新增 [`LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md)，统一定义 node/world、viewport、zoom、screen rect 和 node-center anchor 的符号；标准图片工具条与下方面板分别给出可复核的定位公式；
- 合同明确区分标准双浮层和标注、元素编辑、旋转、图层分离、预览等 active-tool 分支，避免把所有图片工具错误地实现为同一个浮层或统一的派生节点动作；
- 将当前 live 样本、生产 chunk 事实、virtualization 边界、自然裁切规则和 clone-only 的待授权决策写在同一处，并加入后续实现必须满足的七条验证断言；
- 在组件规格入口、Open Canvas 研究 README、研究计划和 [`BIG_PICTURE.md`](../../BIG_PICTURE.md) 增加可发现性链接；
- 没有修改 `src/`、FrameOS、upstream submodule、其他开发者截图或 Director WIP，也没有继续点击可能改变共享源站画布的动作。

## 2026-08-26：v14 Seedance 2.5 能力缺口总矩阵

本轮把外部 Seedance 2.5 功能调研中的“LibTV 有什么”与当前仓库的真实状态重新对齐：

- 新增 [`LIBTV_FEATURE_GAP_MATRIX.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md)，按 Seedance 2.5 生成、片段重拍、Auto Link、超长视频和逐帧拉片五项主推能力记录源站呈现、clone 缺口、证据等级、价值排序和授权闸门；
- 明确区分 `SOURCE_FACT`、文章截图线索、源站推断、`CLONE_FACT` 和待授权的 `CLONE_DECISION`，避免把第三方文章的 4 秒/5 段/300 秒等产品数字写成模型永久契约；
- 将图片工具条、智能剪辑 Beta、失败视频与就绪视频工具条列为相邻但不可混并的能力，并把节点上下文、提交阶段、结果回画布和可审计引用作为共同 UI/UX 结构；
- 通过当前登录态画布的只读 DOM 刷新确认当前图片工具条仍为 9 个文字动作 + 4 个图标动作；没有点击生成、上传、保存、下载或其他可能改变共享画布的动作；
- 同步 Seedance 研究 README、PLAN、research index、docs index 和 [`BIG_PICTURE.md`](../../BIG_PICTURE.md)，形成后续 agent 的单一能力缺口入口；没有修改 `src/`、FrameOS、upstream submodule、其他开发者截图或 Director WIP。

## 2026-08-26：v15 Auto Link 组件状态合同

本轮对当前 clone 的图片/视频 Auto Link 实现做静态代码对照，并将源站状态链收敛成组件级合同：

- 新增 [`LibTVAutoLink.contract.md`](../components/LibTVAutoLink.contract.md)，定义全局偏好、候选池、异步检测、ghost、structured mention、ordinal 投影、graph connection 和竞态保护；
- 明确指出当前 clone 的固定候选、独立确认 popover、全量接受、textarea 前缀写回和局部 references 更新属于结构性 fidelity gap，不能靠增加装饰文案修补；
- 将未来工作切成 preference/visibility、read-only ghost、structured editor、graph transaction 四个独立授权 slice，并给出最小浏览器回归断言；
- 同步组件入口、`ImageEditPanel` 规格、Seedance 能力缺口总矩阵和 [`BIG_PICTURE.md`](../../BIG_PICTURE.md)；仍未修改 `src/`，未对共享源站 Prompt 输入、Auto Link 开关、建议接受或 graph 连接做 live 操作。

## 2026-08-26：v16 实施结果基线校正

本轮检查 Seedance 2.5 实施结果文档与当前源站证据，修正历史快照可能造成的误读：

- 在 [`IMPLEMENTATION.md`](../liblib-seedance-2.5-2026-08-25/IMPLEMENTATION.md) 标明 2026-08-25 是 clone 实施快照，不是当前源站完整合同；
- 记录当前图片工具条从 `900.5x49`/7 个文字动作到 `1092.5x49`/9 个文字动作 + 4 个图标动作的版本漂移，并明确 `元素编辑`、`图层分离` 带来的 active-tool/graph 状态差距；
- 将标准双浮层的两条 zoom 公式和 source/clone 的统一 `addDerivedNode` 差距链接到定位合同、Auto Link 合同和能力总矩阵；
- 没有修改 `src/`、FrameOS、upstream submodule、截图或其他开发者 WIP，也没有在共享源站执行动作。

## 2026-08-26：v17 验证覆盖矩阵

本轮对现有 LibTV Playwright 回归脚本做静态审计：

- 新增 [`LIBTV_VERIFICATION_COVERAGE.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md)，逐项映射双浮层、图片工具、Auto Link、Seedance 参数、片段重拍、逐帧拉片和长视频过程的已有覆盖与缺口；
- 明确 Batch 9 的 `900.5px`/顶部 `16px` 与 Batch 10 的固定 AutoLink popover 是历史 clone 快照合同，不能冒充当前源站 `1092.5px`/`10 + 24 * zoom` 和 inline structured mention；
- 将未来验证分为纯合同、local disposable fixture 和 source observation 三层，并记录哪些项目可以在未授权时继续研究、哪些必须先获得编码/测试或源站副本授权；
- 同步 `HARNESS.md`、docs index、research index、Seedance README 和 [`BIG_PICTURE.md`](../../BIG_PICTURE.md)；没有修改任何回归脚本、`src/`、FrameOS、upstream submodule、截图或其他开发者 WIP。

## 2026-08-26：v18 Open Canvas 启发合同桥接

本轮继续迭代 Open Canvas 研究，重点检查它对 LibTV 后续复刻是否提供可执行帮助：

- 在 [`UIUX_TRANSLATION.md`](UIUX_TRANSLATION.md) 新增合同桥接矩阵，把 measured/live viewport、typed input buckets、run/save 状态、media history、serialized subgraph 和 pending connection 分别映射到 LibTV 双浮层、Auto Link、片段重拍、逐帧拉片和长视频过程；
- 明确上游的具体 gap、宽度、节点类型、provider slug 和 Handle 规则不能直接替代 LibTV 源站合同；只有经过 `SOURCE_FACT -> LibTV evidence -> clone-only contract -> authorized implementation` 才能进入代码；
- 在 Open Canvas 深度报告中链接 LibTV 能力缺口总矩阵与验证覆盖矩阵，补上“研究机制如何接到后续 batch”的入口；
- 没有修改 `src/`、回归脚本、FrameOS、upstream submodule、截图或其他开发者 WIP。

## 2026-08-26：v19 研究-only 后续路线获批并落档

用户批准继续从调研和借鉴角度推进、暂不编码。本轮先把执行顺序独立落档：

- 新增 [`NEXT_RESEARCH_PLAN.md`](../liblib-seedance-2.5-2026-08-25/NEXT_RESEARCH_PLAN.md)，确定先做 LibTV UI 状态层级图，再做 Open Canvas 四类模式卡、五项能力依赖/风险队列和编码授权前 go/no-go；
- 计划明确允许的只读工作、禁止的共享源站动作、disposable fixture 前提、协作保护规则和每批 commit/push 验收标准；
- 将计划接入 Seedance README、research index、docs index 和 [`BIG_PICTURE.md`](../../BIG_PICTURE.md)，使后续 agent 能从正式入口发现当前执行路线；
- 没有修改 `src/`、回归脚本、FrameOS、upstream submodule、截图或其他开发者 WIP。

## 2026-08-26：v20 LibTV UI 状态层级合同

本轮完成第十五批研究项：

- 新增 [`LIBTV_UI_STATE_HIERARCHY.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md)，将 LibTV UI 分为 page shell、canvas graph、标准选中节点控制、active authoring tool、page-level preview 和过程/结果 graph 六层；
- 将标准双浮层、标注/元素编辑/旋转/图层分离、预览和派生结果分别写成状态转换及副作用合同，明确哪些只改 UI、哪些可能改变 nodes/edges；
- 补充 geometry、z-index、pointer-events、selection、pan/zoom、multi-selection、virtualization、undo/redo 和 disposable fixture 验证要求；
- 同步 Seedance README、research index、docs index 和 [`BIG_PICTURE.md`](../../BIG_PICTURE.md)；没有修改 `src/`、回归脚本、FrameOS、upstream submodule、截图或其他开发者 WIP。

## 2026-08-26：v21 Open Canvas 可迁移模式卡

本轮完成第十六批研究项：

- 新增 [`OPEN_CANVAS_PATTERN_CARDS.md`](OPEN_CANVAS_PATTERN_CARDS.md)，将 Open Canvas 的高价值启发收敛为四张卡：`measured node + live viewport`、`typed input buckets + provider projection`、`node/run/save status` 分离、`serialized subgraph + ID map`；
- 每张卡均按 `SOURCE_FACT`、LibTV 对应事实、`INFERENCE`、`CLONE_DECISION` 和验证门槛组织，明确 Open Canvas 只能提供一般性机制启发，不能替代 LibTV 的视觉和交互源站证据；
- 将四张卡纳入 Open Canvas README、PLAN、深度报告、research index 和 docs index，形成可发现的后续评审入口；
- 没有修改 `src/`、回归脚本、FrameOS、upstream submodule、截图或其他开发者 WIP。

## 2026-08-26：v22 Seedance 能力依赖、风险与研究队列

本轮完成第十七批研究项：

- 新增 [`LIBTV_DEPENDENCY_RISK_QUEUE.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_DEPENDENCY_RISK_QUEUE.md)，把普通/超长生成、Auto Link、逐帧拉片、片段重拍和超长视频过程放入同一张依赖图；
- 明确 `source node / media version / reference role / time range / run-node-save status` 六类共享底座，并区分可并行研究和必须串行的证据前提；
- 为每条队列记录研究任务、风险、`BLOCKED_BY_FIXTURE` 停止条件和编码前验收标准，避免用文章截图或现有 clone 过程图填补源站未知；
- 更新 Seedance README、NEXT_RESEARCH_PLAN、research index、docs index 和 [`BIG_PICTURE.md`](../../BIG_PICTURE.md)，标记前 3 项已完成、go/no-go 仍待执行；
- 没有修改 `src/`、回归脚本、FrameOS、upstream submodule、截图或其他开发者 WIP。

## 2026-08-26：v23 研究阶段 go/no-go 闭环

本轮完成第十八批研究项并收束本阶段：

- 新增 [`LIBTV_RESEARCH_GO_NO_GO.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md)，明确文档/只读研究为 `GO`，所有 clone 编码为等待明确授权的 `NO-GO`，真实 Provider/上传/计费/远端持久化为当前范围外；
- 按双浮层、Auto Link、生成参数、逐帧拉片、片段重拍、超长视频和高风险图片动作建立分批授权矩阵，记录最小实现边界和不得顺手扩大的范围；
- 补充 local disposable fixture、源站 disposable fixture、授权请求最小信息、编码后验收顺序和其他开发者 WIP 阻塞处理规则；
- 更新 Seedance README、NEXT_RESEARCH_PLAN、research index、docs index 和 [`BIG_PICTURE.md`](../../BIG_PICTURE.md)，将四项后续研究全部标为已完成；
- 没有修改 `src/`、回归脚本、FrameOS、upstream submodule、截图或其他开发者 WIP。

## 2026-08-27：v24 Open Canvas 机制采纳治理

本轮不再扩写 Open Canvas 产品概述，而是修复研究结论与当前实施治理脱节的问题：

- 新增 [`ADOPTION_DECISION_MATRIX.md`](ADOPTION_DECISION_MATRIX.md)，将 15 类上游机制标为 `ADOPT_METHOD`、`ADAPT_TO_LIBTV`、`RESEARCH_ONLY`、`DEFER` 或 `REJECT_TRANSPLANT`；
- 将坐标、typed input、状态分层、graph transaction、Quick Add、模型能力、持久化和 provider 分别映射到当前 `LIBTV-PAR-*`、`LIBTV-FIX-*` 和 `LIBTV-VR-*`；
- 增加反移植清单，明确 Open Canvas 的视觉皮肤、provider key cookie、保存语义和未被 LibTV 证实的悬空连线行为不能进入 clone；
- 更新 Open Canvas README、research index 和 docs index，并以 commit `c0b068e` 推送；
- 没有修改 `src/`、回归脚本、FrameOS、upstream submodule、截图或其他开发者 WIP。

## 2026-08-27：v25 LibTV 七层实施交接

本轮将已分类的上游启发继续转成面向未来授权的纵向交接合同：

- 新增 [`LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md`](LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md)，定义 evidence、identity、transaction、surface、fixture、verifier 和 provenance 七层；
- 为标准图片双浮层、低风险 active surface、typed Auto Link、graph hardening、process/result lifecycle 和模型能力投影建立 `OC-BP-001..006`；
- 每个 blueprint 记录对应采纳决策、parity、fixture、replacement、候选 ownership、禁止扩边和停止条件；
- 将 [`IMPLEMENTATION_IMPLICATIONS.md`](IMPLEMENTATION_IMPLICATIONS.md) 标为保留第一阶段 A-E provenance 的历史候选清单，当前编号交由采纳矩阵、交接蓝图和全局 parity backlog；
- 蓝图以 commit `333bc17` 推送；随后将 `DEC-024`、`OC-TR-005..008`、任务导读、生命周期和文档审计接入治理闭环；
- 没有修改 `src/`、回归脚本、FrameOS、upstream submodule、截图或其他开发者 WIP。

## 2026-08-27：v26 Process / Result 正交状态设计

本轮完成 `OC-BP-005` 的文档态设计，不接入任务后端：

- 新增 [`LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](LIBTV_PROCESS_RESULT_STATE_MATRIX.md)，将 source node/version、operation/range、run 和 result identity 分开；
- 建立 authoring、node availability、run、result 和 save 五个正交状态轴，以及 queued/running/partial/failed/candidates/accepted/stale/canceled 场景；
- 分别记录逐帧拉片的一次性本地结果事务、片段重拍的 local confirmation 和长视频 12/22 pending graph，明确三者不能冒充统一真实任务合同；
- 为 `LIBTV-FIX-LOCAL-PROCESS-STATES-01`、`LIBTV-FIX-SOURCE-PROCESS-01` 和 `LIBTV-VR-007` 补齐构造、stale/retry、graph/history、reset 与停止条件；
- 更新交接蓝图、Open Canvas/research/docs index、任务导读、fixture catalog、replacement map 和 traceability；
- 没有修改 `src/`、回归脚本、FrameOS、upstream submodule、截图或其他开发者 WIP。

## 2026-08-27：v27 模型能力与执行投影审计

本轮完成 `OC-BP-006` 的文档态审计，不创建 Provider 实现 backlog：

- 新增 [`LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md`](LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md)，将 source-visible catalog、authoring controls、clone UI state、request projection 和 adapter/runner 分层；
- 记录七个 source-visible 模型的 label、estimate、premium 和两个已确认 description，明确七项不是完整模型库，estimate 不是 SLA；
- 对 Seedance 2.5 normal/long 的 mode、ratio、resolution、duration、audio、count、helper 和 credits 做 source/clone/projection 对照；
- 明确 clone credits 公式属于 calibration，只有采样显示是 source fact；其他模型的 mode/control capability 仍未知；
- 将 Open Canvas registry/current runner 漂移转成 LibTV 的 UI/descriptor/adapter/run 审计规则，并保持 `LIBTV-PAR-012 OUT_OF_SCOPE`；
- 更新 VideoGenerationPanel 合同、交接蓝图、Open Canvas README 和 traceability；没有修改 `src/`、verifier、FrameOS、upstream submodule、截图或其他开发者 WIP。

## 2026-08-27：v28 Authority 与上游版本影响协议

本轮完成研究去重和长期维护边界：

- 在 Open Canvas README 增加 authority map，明确固定事实、runtime、pattern、adoption、handoff、Auto Link、graph、process、model 和当前排期的唯一 owner；
- 增加 research completeness boundary，确认剩余高价值问题主要依赖 source freshness、disposable fixture 或新上游 commit，不应继续新建重复总览；
- 新增 [`UPSTREAM_VERSION_IMPACT_PROTOCOL.md`](UPSTREAM_VERSION_IMPACT_PROTOCOL.md)，定义 immutable candidate SHA、path watchlist、逐 claim 状态、pattern/adoption/LibTV 影响、runtime 分离和 baseline decision；
- 明确未经批准不移动 submodule pointer，pointer、研究文档和 LibTV code change 必须分 commit；
- 新增 `OC-TR-009` 供版本更新任务反查；当前 baseline 与 submodule 内容均未改变；
- 没有修改 `src/`、verifier、FrameOS、upstream submodule、截图或其他开发者 WIP。

## 2026-08-27：v29 设计就绪度一致性校准

本轮在 Batch 50 释放共享文档后，复核交接蓝图、parity backlog、fixture catalog 和 replacement map 的状态是否一致：

- 将 `OC-BP-003` 从泛化的 `DESIGN_FIRST` 校准为 `DESIGN_READY`，明确 typed identity/state/transaction、fixture topology、deterministic controls 和 verifier split 已完成文档设计；
- 同时保留 `LIBTV-FIX-LOCAL-AUTOLINK-01` 与 `LIBTV-FIX-LOCAL-PROCESS-STATES-01` 的 `RUNTIME_MISSING`，不把接收规格误写为可运行 fixture；
- 将 `LIBTV-PAR-003` 的 blocker 从“缺设计”收窄为运行 fixture、disposable source input fixture 和编码授权；
- 标记 graph invariant/compatibility case 表已完成，剩余设计缺口是 `GI-004..007` source/product decisions、validation result shape 和专用 replacement；
- 更新正式索引、任务导读、生命周期和审计，使 process、model 与 upstream protocol 可从全局入口发现；
- 没有修改 `src/`、verifier、FrameOS、upstream submodule、截图或 Batch 50 并行实施记录。

## 2026-08-27：v30 下一阶段证据获取队列

本轮将 research completeness boundary 中的六项剩余问题转成唯一执行计划：

- 新增 [`NEXT_EVIDENCE_ACQUISITION_PLAN.md`](NEXT_EVIDENCE_ACQUISITION_PLAN.md)，建立 `OC-EQ-001..006`；
- 将 source freshness、非 Seedance 模型 controls 和 graph bundle guard 归入当前可推进的 read-only/static wave；
- 将 Auto Link input/IME/accept、ready-video/process lifecycle 和 graph mutation 场景归入必须等待 disposable source fixture 的 wave；
- 将 Open Canvas commit diff 设为只在新 immutable SHA 出现时触发，并继续禁止先移动 submodule pointer；
- 为每项记录允许动作、禁止动作、最小证据包、退出标准、authority 更新和 blueprint/parity 影响；
- 将计划接入 Open Canvas authority map、docs/research index 和 agent task map；没有修改代码、verifier、截图、共享源站状态或 submodule。

## 2026-08-27：v31 `OC-EQ-001` 标准图片 freshness

本轮使用用户已打开的登录态 LibTV tab，只读取接管前已经存在的 41% 图片选中态：

- 新增 [`LIBTV_SOURCE_FRESHNESS_2026-08-27.md`](LIBTV_SOURCE_FRESHNESS_2026-08-27.md)、结构化 JSON 和 source screenshot；
- 同一 frame 记录 selected node、`1092.5x49` toolbar 和 `660x191` panel，三者 center X 误差均小于 `0.01px`；
- 顶部 gap `19.77399px` 与 `10 + 24 * zoom` 残差约 `0.00049px`，底部 gap `6.51563px` 与 `16 * zoom` 残差约 `0.00004px`；
- 记录 toolbar/panel 在 929px viewport 左边界为负并自然裁切，没有观察到 clamp；
- 将 `OC-EQ-001` 标为 `PARTIAL_RECORDED`，因为本轮没有点击、改变 zoom、进入 active tool 或覆盖 mobile/selection transition；
- 没有修改 Batch 51、`src/`、verifier、共享源站状态或 Open Canvas submodule。

## 2026-08-27：v32 `OC-EQ-002` 模型目录 freshness

本轮在 fit-view 28% 下只读选择已有 failed video，展开并滚动模型 dialog：

- 新增 [`LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md`](LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md)、35-row JSON 和 top/bottom screenshot；
- 当前 dialog 加载 35 行，前 14 行使用 selectable style，后 21 行使用 `cursor-not-allowed opacity-50`；
- 35 行均非 native disabled 且缺少 `aria-disabled`，因此不为 unavailable style 补写业务原因；
- 当前 panel short label `2.0 Fast` 与 selected catalog row `Seedance 2.0 Fast VIP` 的 alias 得到直接证明；
- 旧七行样本保留历史截图边界，current catalog authority 升级到新日期 35 行；
- 没有选择其他模型或修改 mode/params，所以 per-model controls 与 runner 继续 unknown/out-of-scope；没有修改代码、verifier、共享源站 graph 或 submodule。

## 2026-08-27：v33 `OC-EQ-003` graph compatibility 静态审计

本轮完成 Wave A 的 graph 静态阶段，仍不执行共享项目连线：

- 新增 [`LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md`](LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md) 和结构化 JSON，记录 13 node/12 edge 的 DOM、Handle instance state、ARIA edge identity、viewport 和 production bundle 坐标；
- 从当前画布 chunk 确认普通连接 path 的 target-start 方向归一化、同/反向 node-pair duplicate guard、普通非 Reference 的 adjacency + DFS cycle guard 和 programmatic equal-ID guard；
- 从当前 action/type bundle 确认 LibTV 的连接兼容性继续受 node action、默认 action、group/script 特例、目标容量、model capability 和可选 `switchToModel` 影响；Handle CSS class 不是最终业务规则；
- 将 `LIBTV-GI-004..007` 和 `LIBTV-GC-002..005` 更新为 `STATIC_RECORDED` 但保留 `SOURCE_DECISION_REQUIRED`：Reference 例外、导入/批量/同步入口、invalid feedback、history/no-residue 和真实拖线仍需 disposable source fixture；
- 同步 Open Canvas README、采纳矩阵、实施交接蓝图、证据队列、graph authority 和 traceability，明确上游 DAG/typed validation 只作为方法启发，不能替代 LibTV graph 语义；
- 没有修改 `src/`、verifier、FrameOS、共享源站 graph、其他开发者 Batch 51 WIP 或 Open Canvas submodule。

## 2026-08-26：v34 `OC-EQ-001` freshness 接管阻塞留档

本轮尝试继续推进 `LIBTV-PAR-005` / `OC-EQ-001`，但没有获得可用的源站画布
运行态：

- 目标 canvas URL 接管后重定向到 LibTV 首页，当前 tab 没有保留目标画布登录态；
- 浏览器自动化运行时报告 `26.818.41509` 插件路径不存在，实际安装目录为
  `26.818.61809`；
- 没有输入、生成、保存、上传、下载、连线、删除或其他 graph mutation；
- 新建 [`../liblib-canvas-batch55-2026-08-26/`](../liblib-canvas-batch55-2026-08-26/README.md)，
  记录 blocked handoff、已有 standard image evidence 和未覆盖场景；
- `OC-EQ-001` 保持 `PARTIAL_RECORDED`，`LIBTV-PAR-005` 保持
  `RESEARCH_FIRST`，不能把本轮重定向解释成 source drift；
- 没有修改 `src/`、verifier、FrameOS、共享源站状态或 Open Canvas submodule。

## 2026-08-27：v35 graph connection 实施前合同收敛

本轮没有新增 source mutation，而是把 Open Canvas 方法、LibTV source static evidence 和当前 clone gap 收敛为可执行的文档交接包：

- 新增 [`LibTVGraphConnection.contract.md`](../components/LibTVGraphConnection.contract.md)，定义 target-start normalize、result/reason taxonomy、guard precedence、reject/unknown 零 mutation 和 accepted one-step history；
- 为 `LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01` 定义 A/B/C topology、逐场景 fresh Page reset 和禁止 undo-as-teardown；
- 新增 `LIBTV-VR-009` pure/browser replacement 设计，保留 Batch 4-8 历史 graph regressions，不通过直接 store 注入制造通过；
- 将 `OC-BP-004` connection 子切片升级为 `DESIGN_SPEC_COMPLETE / RUNTIME_MISSING`，snapshot/copy 仍保持独立 `DESIGN_FIRST`；
- 将 Reference、import/batch/sync、未建模 action 和 source invalid feedback 保持显式 unknown/source-blocked，不用 Open Canvas 规则填空；
- 同步 adoption、evidence、parity、fixture、verifier、decision、traceability、component coverage 和 agent navigation；
- 没有修改 `src/`、测试脚本、FrameOS、共享源站 graph、其他开发者 Batch 56 WIP 或 Open Canvas submodule。

## 2026-08-27：v36 graph document 与 snapshot 分层合同

本轮继续将 Open Canvas 的 versioned graph 方法转译为 LibTV clone 文档，不引入上游 persistence 产品语义：

- 复核固定版本的 `SerializedCanvasGraph version: 1`、flow serializer、strict API validator、local DB normalization、revision/save baseline、template runtime reset 和 conflict rebase；
- 复核当前 clone 的 in-memory `CanvasData`、浅层 nested `GraphSnapshot`、50-step history、canvas duplicate、selection copy 和无普通画布 persistence 边界；
- 新增 [`LibTVGraphDocument.contract.md`](../components/LibTVGraphDocument.contract.md)，分开 runtime graph、history snapshot、portable document、clipboard packet 和 future persistence envelope；
- 定义 clone-only V1 conceptual schema、node dataVersion、runtime-field whitelist、media portability、strict parse/migration、future-version stop 和 zero-partial load；
- 为 `LIBTV-FIX-LOCAL-GRAPH-DOCUMENT-01` 与 `LIBTV-VR-010` 定义 pure payload corpus、nested history isolation 和 future import-as-new-canvas boundary；
- 新增 `DEC-026` / `LIBTV-TR-031`，明确 history deep isolation 不等于 import/export/save 已实现；Open Canvas limits、file/KV、revision/debounce/rebase 保持 deferred；
- 同步 adoption、handoff、graph catalog、fixture、verifier、component coverage、agent navigation 和 authority map；
- 没有修改 `src/`、测试脚本、FrameOS、共享源站、其他开发者 Batch 56 WIP 或 Open Canvas submodule。

## 2026-08-27：v37 subgraph copy 与 duplicate 身份合同

本轮继续使用 Open Canvas 的结构化子图方法作为设计输入，但不移植其 payload、产品限制或快捷键语义：

- 复核固定版本的 custom MIME/version、selected-node closure、internal-edge extraction、two-pass node ID map、endpoint rewrite、viewport-center placement、48 flow-unit repeated-paste shift、editable-target guard 和 in-memory fallback；
- 复核当前 clone 的 `duplicateNode`、`duplicateSelectedNodes`、recursive group descendants、child detach/remap、single-node incident-edge compatibility、one-step history 和独立 `duplicateCanvas` 边界；
- 新增 [`LibTVSubgraphCopy.contract.md`](../components/LibTVSubgraphCopy.contract.md)，将 `duplicate-selection`、`create-node-copy`、`paste-subgraph`、`option-drag-copy` 与 canvas lifecycle 分开；
- 定义 descendant closure、two-pass structural identity、node-data reference role registry、internal-only edge policy、flow-space placement、full-plan prevalidation 和 atomic undo/redo；
- 新增 `LIBTV-FIX-LOCAL-SUBGRAPH-COPY-01`、`LIBTV-VR-011`、`DEC-027` 和 `LIBTV-TR-032`，把 single-node incident edge 标为 `COMPATIBILITY_HOLD`，将 clipboard runtime 与 Option-drag source gesture 保持 blocked；
- 同步 adoption、handoff、graph catalog、shortcut crosswalk、parity、fixture、verifier、component coverage、agent navigation 和 authority map；
- 没有修改 `src/`、测试脚本、FrameOS、共享源站、其他开发者 WIP 或 Open Canvas submodule。

## 2026-08-27：v38 node data identity、aggregate 与 portability 合同

本轮继续把 Open Canvas 的 closed union、normalize、serialization whitelist 和 runtime reset 方法转译为 LibTV 专属 registry，不移植其五类 node data：

- 新增 [`LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](../LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md)，固定当前 11 runtime types、8 public creation types、distributed interfaces/writers、nested source/edge refs、shot reciprocal refs、long-video process cohort、Director cross-store 和 media locator 风险；
- 明确 `src/types/canvas.ts`、Add Node、default-data switch、renderer registry 与 component interfaces 不是同一 allowlist，current history/duplicate/canvas duplicate 仍只做 shallow data spread；
- 新增 [`LibTVNodeDataIdentity.contract.md`](../components/LibTVNodeDataIdentity.contract.md)，定义 V0 registry、canonical field roles、七类 named operation profile 和 explicit transform verbs；
- 为 shot aggregate、process complete cohort、Director shell/workspace、node-scoped mark IDs、repo/https/data/blob media 和 per-type status 建立 preserve/map/reset/diagnose/reject 边界；
- 新增 `LIBTV-FIX-LOCAL-NODE-DATA-01`、`LIBTV-VR-012`、`DEC-028`、`LIBTV-TR-033` 和 `GI-013..015/GC-013..015`；
- 同步 graph document/copy、adoption、handoff、parity、fixture、verifier、component coverage、agent navigation 和 authority map；
- 事实审计以 commit `dbdc05f` 单独推送；规范合同批次没有修改 `src/`、测试脚本、FrameOS、共享源站、其他开发者 Batch 57 WIP 或 Open Canvas submodule。

## 2026-08-27：v39 graph delete impact 与 reference repair 合同

本轮继续使用 Open Canvas 的集中 deletion、incident-edge cleanup、selection delete 和 conflict no-op 作为方法输入，但不把其简单五类 node/edge 模型移植到 LibTV：

- 固定复核 Open Canvas `deleteNode/deleteEdge/deleteSelection/deleteIncomingReference`，确认上游没有 LibTV 的 parent descendants、nested owned edge IDs、shot reciprocal refs 或 process cohort；
- 固定复核 clone `removeNode/removeSelectedNodes/removeEdge/clearVideoContinuation/removeCanvas`，记录当前只修结构、不修 surviving node data、aggregate、UI owner 和 resource lifetime 的风险；
- 新增 [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](../LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)，定义 destructive command inventory、relation topology、inverse index、full-plan planner、correctness floor 和 stable reject/unknown reasons；
- 为 group/ordinary edge、owned edge metadata、shot source/result、V0 long-video process、Director provenance、canvas lifecycle 和 media locator 建立 active/proposed/source-required/deferred policy；
- 新增 `LIBTV-FIX-LOCAL-GRAPH-DELETE-01`、`LIBTV-FIX-SOURCE-GRAPH-DELETE-01`、`LIBTV-VR-013`、`DEC-029` 和 `LIBTV-TR-034` 的 authority chain；
- 新增 `OC-ADOPT-016`，明确只借 named deletion/zero-mutation/one-commit 方法，LibTV 仍必须做 relation-aware repair；
- 删除矩阵第一阶段以 commit `d635788` 推送；本轮未修改 `src/`、测试、FrameOS、共享源站、其他开发者 Batch 57 WIP 或 Open Canvas submodule。

## 2026-08-27：v40 graph mutation 入口信任边界

本轮继续从 Open Canvas 的 store/save/API 链提取可迁移方法，同时把上游自身的 partial ingress 作为反例保留：

- 固定复核 Open Canvas `hydrate/addNode/pasteClipboard/delete*/on*Change/onConnect/updateNodeData/applyServerNodePatch`、serialization/full-graph save validation、API strict parse、revision compare、conflict rebase 和 durable replace；
- 明确上游不是“所有入口经过一个 validator”：clipboard 只做浅 packet shape、paste 不做完整 DAG、framework delta 直接 apply、Handle retarget 不重跑所有 policy、tolerant storage normalize 可能静默丢弃；
- 固定复核 clone 全部 canvas/node/derived/copy/group/delete/data/setter/connection/history/future ingress，确认 Batch 57 只保护 connection/addEdge island；
- 新增 [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](../LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)，定义 `PROTECTED/PARTIAL/TRUSTED_OUTPUT_UNPROVEN/BYPASS/DEFERRED` 和 T0-T5 authority；
- 定义 multi-entity full-draft plan、transport whitelist、restore/remote boundary、`LIBTV-ING-DQ-001..008`、`GI-018..022/GC-018..023`；
- 新增 `LIBTV-FIX-LOCAL-GRAPH-ENTRYPOINT-01`、`LIBTV-VR-014`、`DEC-030`、`LIBTV-TR-035`、`OC-TR-010` 和 `OC-ADOPT-017` 的 authority chain；
- 同步 Big Picture、agent task map、docs/research/Open Canvas indexes、graph catalog、fixture/verifier、component coverage 和 handoff blueprint；
- 本轮只修改文档，不触碰其他开发者 Batch 58 的 `src/` WIP、测试、FrameOS、共享源站 graph 或 Open Canvas submodule。

## 2026-08-27：v41 async result ingress 与陈旧执行收敛

本轮继续深读 Open Canvas current execute/run/poll/patch chain，并将其正面结构与 stale-write 限制一起转译为 LibTV process/result completion 合同：

- 固定复核 execute 前 `saveGraphNow`、revision preflight、persisted-graph descriptor、独立 run record、runId-keyed polling、hydrate 后 polling recovery、server node patch 和 client saved-baseline projection；
- 明确 fixed implementation 的 revision compare/run reservation 非原子、generic patch 不比较 expected current run/source version/field owner、run terminal 与 node projection 两次写、audio/provider exception stranded-run 和 storage read-modify-write 风险；
- 使用 fixed clone commit `8007e13` 审计，确认普通 canvas 无 network/run store；shot、audio/depth/matting/picture、long-video 由 component timer 延迟写 graph，Director export 才是真实 browser async asset completion；共享分支随后推进的 Batch 58/59 不纳入本轮代码事实；
- 新增 [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)，定义 operation descriptor、result envelope、current/stale/duplicate/invalid disposition、field ownership、full-plan commit、selection/history/undo/redo、recoverable projection 和 resource transfer；
- 新增 `OC-PATTERN-05`、`OC-026..030`、`OC-ADOPT-018`、`OC-TR-011`、`DEC-031`、`LIBTV-TR-037`、`GI-023..030/GC-024..033`、`LIBTV-FIX-LOCAL-ASYNC-INGRESS-01` 和 `LIBTV-VR-015`；
- 明确当前短 timer 只算 `PROTOTYPE_LATENCY`，第一授权候选应是 deterministic shot-breakdown convergence fixture，不是 provider integration；
- 同步 Big Picture、agent/index、process state、graph ingress/catalog、fixture/verifier/coverage、evidence/report/source analysis、adoption/pattern/handoff 和 traceability；
- 本轮只修改文档，不触碰其他开发者 Batch 59 的 Director `src/`、verifier、截图/runtime-audit WIP、FrameOS、共享源站 graph 或 Open Canvas submodule。

## 2026-08-27：v42 React Flow change routing 与 transport whitelist

本轮继续把 Open Canvas 的 framework adapter 作为正反面研究对象，并将 clone graph ingress 的 T1 层细化为可实施合同：

- 确认 Open Canvas 与 clone 都锁定 `@xyflow/react@12.11.1` / `@xyflow/system@0.0.78`，排除 framework version mismatch；
- 精确记录 NodeChange select/position/dimensions/add/remove/replace、EdgeChange select/add/remove/replace，以及 reconnect 独立 callback 的边界；
- 深读 installed reducer 的 same-ID grouping、remove/replace precedence、deferred add 和 unknown no-op 行为，明确不能先 partial filter 再 apply；
- 固定复核 Open Canvas functional current Zustand state/conflict gate 的正面方法，以及 all non-select generic apply/dirty classification、Handle retarget incomplete validation 的反例；
- 固定复核 clone selection split、render-closure edge base、whole-array setter、semantic variant bypass、drag-stop one-history 和 runtime-field leakage；
- 新增 [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)，定义 whole-batch T0/T1 routing、field allowlist、current active-canvas snapshot、selection/history/document sanitation 和 stable result；
- 新增 `OC-PATTERN-06`、`OC-031..034`、`OC-ADOPT-019`、`OC-TR-012`、`DEC-032`、`LIBTV-TR-038`、`GI-031..037/GC-034..043`、`LIBTV-FIX-LOCAL-REACT-FLOW-CHANGES-01` 和 `LIBTV-VR-016`；
- 本轮只修改文档，不触碰其他开发者 Batch 60 图片组件/证据 WIP、测试、FrameOS、共享源站 graph 或 Open Canvas submodule。

## 2026-08-27：v43 multi-canvas lifecycle 与 cross-owner isolation

本轮继续从 Open Canvas canvas registry/list/studio chain 提取方法，并审计当前 clone 的跨画布 owner：

- 固定复核 Open Canvas summary/full record、URL canvasId、missing not-found、create/rename/delete、last-empty replacement、run cleanup、hydrate、viewport save 和 route-local async save；
- 记录 list/document/hydrate/delete-run cleanup 的正面方法，以及 old-route request 虽有 explicit URL target、global `finishSave/failSave/enterConflict` 却无 expected current canvas guard 的竞态推断；
- 固定复核 clone Batch 16 CRUD、per-canvas graph/viewport/history、global selection、Batch 58 node-bound owner、React Flow keyed remount，以及 invalid target、demo viewport preset、organize/drag/connection/viewport transient 和 delayed active-destination 风险；
- 新增 [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)，定义 registry/document/history/session/external owner、CRUD/switch plan、reconciliation manifest、invariants、decision queue 和实施切片；
- 新增 `OC-PATTERN-07`、`OC-035..039`、`OC-ADOPT-020`、`OC-TR-013`、`OC-BP-007`、`DEC-033`、`LIBTV-TR-039`、`GI-038..048/GC-044..058`、`LIBTV-FIX-LOCAL-CANVAS-LIFECYCLE-01` 和 `LIBTV-VR-017`；
- 主合同因共享 Batch 60 全量暂存被并行带入 `8881ad6`；本轮 follow-up commit 单独同步权威链，保留这一 provenance，不改写对方历史；
- 本轮没有修改 `src/`、测试、FrameOS、共享源站 graph 或 Open Canvas submodule。

## 2026-08-27：v44 command outcome 与 feedback ownership

本轮继续将 Open Canvas 的命令结果与反馈投影作为正反面研究对象，并把 clone 分散的 reason、string、timer 和 Director 状态收敛为实施前合同：

- 固定复核 Open Canvas Sonner root、typed command result、localized runtime message、node run/status/error、save/conflict、field error/pending、CRUD confirm/no-op 等层次，确认其优势是局部持续状态与全局瞬时通知分工；
- 同时保留两个上游反例：result code 粒度过粗、具体 identity 埋在本地化 message 并靠整段中文匹配翻译，以及 async toast 缺少 canvas/operation/attempt/dedupe owner；
- 固定审计 clone：connection 已有 stable reason 但 page reject 静默；Share/Agent/AddNode/VideoClip 仍是 string-only local status；VideoNode 使用 action-specific timer；Director 已有更强的 persistent progress/error/retry surface；FrameOS route/store 必须保持隔离；
- 新增 [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](../LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)，定义 `COMMITTED/STARTED/COMPLETED/REJECTED/NOOP/FAILED/CANCELED/STALE/CONFLICT/UNKNOWN`、reason/copy 分层、primary surface、announcement owner、clear/retry/dedupe、history/accessibility 和 route/canvas isolation；
- 新增 `OC-PATTERN-08`、`OC-040..045`、`OC-ADOPT-021`、`OC-TR-014`、`OC-BP-008`、`DEC-034`、`LIBTV-TR-040`、`GI-049..058/GC-059..075`、`LIBTV-FIX-LOCAL-COMMAND-FEEDBACK-01`、`LIBTV-VR-018` 和 `LIBTV-UIX-18` 的 authority chain；
- 明确第一实施切片应是本地 deterministic feedback adapter/fixture，不是新增 global toast host；exact source toast placement/timeout、invalid connection style 和 provider task 文案仍保留 source/fixture gate；
- 本轮只修改文档，没有修改 `src/`、测试脚本、FrameOS、共享源站、其他开发者 WIP 或 Open Canvas submodule。

## 2026-08-27：v45 selection、focus 与 command context 双向静态审计

本轮先固定事实，不提前编写全局 modal/shortcut 实现方案：

- 固定复核 Open Canvas selected node/edge flags、selected-node editor/count/copy/delete 的不同 projection，以及 conflict gate 同时冻结 selection 和 persistent change 的 coupling；
- 固定复核 Open Canvas document clipboard 的 input/textarea/select/contenteditable/role-textbox guard、image preview suspension、local editor Enter/Escape ownership、Quick Add weak Escape listener 和 Radix dialog/dropdown delegation；
- 明确 fixed studio 没有统一 app shortcut dispatcher，部分 destructive key 仍依赖 React Flow/default focus，因此上游是正反面方法输入，不是 LibTV shortcut 规格；
- 固定审计 clone node selection session projection、三类 node selection ingress、stored edge `selected` authority、node-only Delete input、active image capture guard、local Escape listeners、pointer-modal surfaces、Preview/Director focus owner 与缺失 focus return；
- 新增 [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)，登记 `LIBTV-SFC-001..012`、`OC-046..052`、formal contract questions，以及候选 `LIBTV-FIX-LOCAL-SELECTION-FOCUS-CONTEXT-01` / `LIBTV-VR-019`；
- 纠正 `PAR-004` 和 overlay `UI-05` 的旧事实：Batch 50 已让 Director active 时普通 page dispatcher 对全部快捷键 return，剩余缺口是完整 focus trap/return、nested listener 和 source-exact 语义；
- 同步 docs hub、research index、Open Canvas read order/authority、evidence/source/report/interaction/plan 与 shortcut crosswalk；
- 本轮只修改文档，没有修改 `src/`、测试脚本、FrameOS、共享源站、其他开发者 WIP 或任一 submodule。

## 2026-08-27：v46 selection、focus 与 command context 正式合同

本轮把 v45 的 fixed facts 转换为可交接、可验证的正式设计，不引入全局 modal/shortcut 实现：

- 新增 [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)，定义 active canvas/generation 下的 node IDs、edge IDs、primary selection snapshot，并明确 React Flow `selected` 只作 transport/projection；
- 定义 editable/node-control/canvas/modal/Director/route focus zone 与 context policy、top-context precedence、`HANDLED/CONSUMED/PASS/BLOCKED/NOOP` dispatch result、一次 Escape 只退一层，以及 acquire/contain/return/fallback 生命周期；
- 新增 `LIBTV-SFC-I-001..030`、`LIBTV-SFC-DQ-001..012`、`LIBTV-FIX-LOCAL-SELECTION-FOCUS-CONTEXT-01` 和 `LIBTV-VR-019`，覆盖 switch/delete/undo/unmount、stale return、zero semantic history 与 FrameOS route isolation；
- 新增 `OC-PATTERN-09`、`OC-ADOPT-022`、`OC-TR-015`、`OC-BP-009`、`LIBTV-UIX-19`、`DEC-035` 和 `LIBTV-TR-041`，把 Open Canvas selected/editable/local editor/Radix 正面方法与 conflict gate/weak Escape/default propagation 反例纳入完整 authority chain；
- 明确不移植 React Flow selected flags 作为完整 authority，不复制 Open Canvas conflict gate、默认 key propagation 或 Radix 产品语义，不引入 global modal manager；
- 同步 Big Picture、agent task map、docs/research/Open Canvas indexes、graph catalog、fixture/verifier、overlay/shortcut、parity、coverage 和 traceability；
- 本轮只修改文档，没有修改 `src/`、测试脚本、FrameOS、共享源站、其他开发者 WIP 或任一 submodule。

## 2026-08-27：v47 viewport、coordinate 与 gesture 双向静态审计

本轮先固定空间事实与缺口，不提前实现 Quick Add、drop、viewport adapter 或全局 geometry service：

- 落档 [`LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md`](../LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md)，区分 client、container-local、flow-world、node-local、screen-sized overlay 和 media-normalized 六个 domain；
- 固定 Open Canvas Quick Add screen/flow 双锚点、live/stable viewport、add/duplicate/paste/drop/double-click placement、hydrate projection 和 selected-overlay 共享 transform 方法；
- 同时记录 permissive viewport normalization、窄 host clamp/resize、panning cleanup、逐文件 async drop、pending node-then-edge 的上游反例；
- 固定 clone `flowViewport` / per-canvas viewport / zoom-percent 三重投影、V/H/Space blur/visibility cleanup、default/derived/duplicate/group/drag/organize placement writers；
- 新增 `OC-053..060` 和 `LIBTV-VGP-001..016`，确认最高置信可见缺口是 default add 以 browser window 而非 actual React Flow host 计算中心；
- 预留 `LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01` 与 `LIBTV-VR-020`，formal contract、adoption/traceability/handoff 尚在下一批；
- 本轮只修改文档，没有修改 `src/`、测试脚本、FrameOS、Director runtime、共享源站、其他开发者 WIP 或任一 submodule。

## 2026-08-27：v48 viewport、coordinate 与 placement 正式权威

本轮把 v47 fixed facts 转为可交接、可验证且不越过编码授权的空间合同：

- 新增 [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)，定义 `CLIENT/HOST_LOCAL/FLOW_WORLD/NODE_LOCAL/SCREEN_OVERLAY/MEDIA_NORMALIZED`、actual host frame/epoch、`BOOTSTRAP/LIVE/STABLE/TARGET` viewport phase；
- 定义 pan/zoom/drag/connection/menu/organize session start/update/end/cancel/stale、host resize anchor preservation、entry-specific placement、history/document/overlay composition 和 typed result；
- 新增 `LIBTV-VGP-I-001..032`、`LIBTV-VGP-DQ-001..012`、`LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01`、`LIBTV-VR-020`、`GI-059..070/GC-076..090`；
- 新增 `OC-PATTERN-10`、`OC-ADOPT-023`、`OC-TR-016`、`OC-BP-010`、`LIBTV-UIX-20`、`DEC-036` 和 `LIBTV-TR-042`，完成 pattern -> adoption -> parity -> fixture -> verifier -> handoff 追溯；
- 明确 actual-host default add 是 clone correctness floor，exact source add/fit/zoom/resize/drop 仍 gated；不实现 Quick Add、file drop、pending connection，不移植 Open Canvas menu/zoom/pan/overlay/persistence；
- 同步 Hub、research/Open Canvas indexes、Big Picture、agent task map、decision/traceability、fixture/verifier/coverage、graph、overlay/copy/routing/lifecycle/parity 权威；
- 将完成的研究计划从 `docs/drafts/` 迁入本目录保留交付历史，stable guidance 由正式合同承担；
- 本轮只修改文档，没有修改 `src/`、测试脚本、FrameOS、Director runtime、共享源站、其他开发者 WIP 或任一 submodule。

## 2026-08-27：v49 media ingress/resource lifecycle 三向静态审计

本轮先固定 Open Canvas、committed clone 与当前 LibTV source 的资源入口事实，不选择文件或提前设计真实上传：

- 以 `6325a1f` 落档 active research plan，明确新 authority 从 ingress intent/local bytes 开始，以 graph/document/delete/async/viewport owner delegation 结束；
- 新增 [`LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md`](../LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md)，固定 Open Canvas client validation、metadata probe、multipart route、server trust boundary、digest dedupe、normalized descriptor、copy/save path；
- 同时保留 accept/probe classifier drift、node-first running placeholder、sequential partial mutation、text/audio asymmetry、autosaved running、缺失 operation freshness/cancel/resource cleanup 等反例；
- 固定 clone Add Resource upload/history mock、Shot Breakdown component object URL + ready projection、picture replacement placeholder、Director data/blob locator island，以及 ordinary route 没有 drop/paste/upload/asset registry 的边界；
- 只读当前 LibTV source DOM，记录 Add Resource multiple image/video/audio chooser、Generated History 来源/type/cap/page、风格/特效 Material Library、Canvas/Assets + Personal/Agent Asset Manager、single-video Shot source 与 dormant generic uploader；
- 原始记录落档为 [`libtv-media-ingress-source-dom-audit-2026-08-27.json`](libtv-media-ingress-source-dom-audit-2026-08-27.json)，全程没有选择文件、上传、生成、保存、下载或删除；
- dated audit 以 `dfb7ec4` 独立提交并推送；本轮没有修改 `src/`、测试、FrameOS、Director runtime、共享源站状态、其他开发者 WIP 或任一 submodule。

## 2026-08-27：v50 media intent、asset/reference 与 resource lease 正式权威

本轮把 v49 fixed facts 转为可交接、可验证且保持前端 prototype 诚实的正式合同：

- 新增 [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](../LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)，定义 ten entry profiles、immutable ingress/attempt/cohort/canvas/node/source identity、canonical validation/probe/materialization/freshness 和 full projection plan；
- 明确 `File`/`Blob`/object URL 属于 instance operation/lease，stable asset、generated-history item、material preset、node media reference 和 session result 不共享 identity；
- 定义 provisional UI zero semantic history、accepted cohort original-order one-step commit、replace last-known-good、invalid/noop/stale/cancel zero residue，以及 graph/history/clipboard/editor/operation/asset/export reachability 后 exact-once release；
- 新增 `OC-061..070`、`LIBTV-SRC-MIR-001..006`、`OC-PATTERN-11`、`OC-ADOPT-024`、`OC-TR-017`、`OC-BP-011`、`LIBTV-UIX-21`、`DEC-037`、`LIBTV-TR-043`、`LIBTV-PAR-014` 的 authority chain；
- 新增 `GI-071..084/GC-091..108`、`LIBTV-FIX-LOCAL-MEDIA-INGRESS-01`、`LIBTV-FIX-SOURCE-MEDIA-INGRESS-01` 和 `LIBTV-VR-021`，并同步 fixture/verifier/ledger/coverage/Big Picture/report/evidence queue；
- 将 exact source limits/progress/cancel/placement/register/restore 归入 `OC-EQ-007`，没有 disposable source fixture 时不在共享项目试探；
- 将完成的研究计划从 `docs/drafts/` 迁入本目录，stable guidance 由 audit + contract 承担；
- 本轮只修改文档，没有修改 `src/`、测试脚本、FrameOS、Director runtime、共享源站、其他开发者 WIP 或任一 submodule。

## 2026-08-27：v51 foreground editor session/history 双向静态审计

本轮固定 Open Canvas 与 committed clone 的编辑器会话、局部历史和提交入口，不在共享源站输入或保存：

- 以 `0a1c0a3` 落档 active plan，以 `b5ea255` 落档 [`LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md`](../LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md) 与结构化 JSON；
- 新增 `OC-071..080` 和 `LIBTV-EDS-001..014`，区分 session identity、baseline/draft、bitmap snapshots、Restore、JPEG export、upload/patch、inline/rich draft 与 graph save owner；
- 固定 entry-only 40-step full bitmap 可达约 2.38 GiB、cleanup 未 abort hidden fetch、close-first async save、node-ID-only completion、active draft resync 和 caller 忽略 commit result 等反例；
- 固定 clone TextNode、ImageEditPanel、Annotate、Element、Picture、Subtitle、Range、Reshoot、Camera 与 VideoToolbar 的 fragmented maturity，以及 `updateNodeData` 无 semantic equality guard；
- 修正四份 component spec 中与 committed runtime 不一致的 editor/history/submit 描述；
- 本轮只修改文档，没有修改 `src/`、测试脚本、FrameOS、Director runtime、共享源站、其他开发者 WIP 或任一 submodule。

## 2026-08-27：v52 editor profile、commit 与 history 正式权威

本轮把 v51 facts 转为可交接、可验证且不越过编码授权的正式合同：

- 以 `20d4324` 落档 [`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)，定义十类 profile、session/baseline/draft、drift/equality、native/local/graph undo、commit/async/resource handoff；
- 新增 40 条 `LIBTV-EDS-I-*`、`GI-085..100`、`GC-109..126`、`LIBTV-FIX-LOCAL-EDITOR-SESSION-01`、`LIBTV-VR-022` 与 source decision queue；
- 发布 `OC-PATTERN-12`、`OC-ADOPT-025`、`OC-TR-018`、`OC-BP-012`、`LIBTV-UIX-22`、`DEC-038` 和 `LIBTV-TR-044`，明确 local editor trial 与 semantic graph commit 分权；
- 拒绝移植 40-entry full bitmap、JPEG/0.92、HTML/editor schema、close-first、node-ID-only patch、Open Canvas upload/provider/save 产品语义；
- runtime 仍 fragmented、source parity partial；任何实现、fixture 脚本或测试变更继续需要用户明确编码授权；
- 本轮只修改文档，没有修改 `src/`、测试脚本、FrameOS、Director runtime、共享源站、其他开发者 WIP 或任一 submodule。

## 2026-08-27：v53 media rendition、aspect 与 node geometry 三向静态审计

本轮先固定 intrinsic media、selected output、generation request、node frame、React Flow measurement 和 per-surface crop/fit 的不同权威，不提前增加 generic resize 或 runtime schema：

- 以 `fd90b18` 落档 active documentation plan，明确 passive measurement 不等于 user resize intent；
- 新增 [`LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md`](../LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md)，固定 Open Canvas fixed-width/request-aspect card、cover node/candidate、contain detail、selected output normalization 和 measured anchor 方法；
- 保留 per-output intrinsic dimensions 缺失、image/video probe asymmetry、edited output 不更新 aspect、thumbnail/full URL 无 crop metadata、serialized dimensions 被误读为 resize 等反例；
- 固定 clone default square-media/landscape-frame、derived-image frame reset、portrait/square Director capture crop、poster/video fit branch、mark overlay 绑定 cover-cropped node plane 等 `LIBTV-MRG-001..014`；
- 只读当前 LibTV source 五个既有图片节点，确认 `1808x1024 -> 618x350`、`1152x576 -> 700x350`、`1280x720 -> 622x350`，均为 centered cover 且当前 DOM 无 known node-resizer selector；
- 选择既有 `分镜 #2` 后只测量 node/top-toolbar/lower-panel rect，确认 media-shaped frame 会参与已有 center/gap contract；没有上传、生成、编辑、保存、删除或付费动作；
- 原始固定路径和测量落档为 [`media-rendition-geometry-static-evidence-2026-08-27.json`](media-rendition-geometry-static-evidence-2026-08-27.json)；formal contract、fixture、`VR-023` 与治理链进入下一文档批；
- 本轮只修改文档，没有修改 `src/`、测试脚本、FrameOS、Director runtime、共享源站持久状态、其他开发者 WIP 或任一 submodule。

## 2026-08-27：v54 media rendition、aspect 与 node geometry 正式合同

本轮把 v53 fixed facts 转为不依赖实现细节、可由后续编码 agent 直接执行和验证的几何权威：

- 新增 [`LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md)，把 media intrinsic、thumbnail、selected output、generation request、semantic node frame、passive measured rect、surface rendition、visible rect、editor media space 和 export output 分为十类 authority；
- 定义 `SOURCE_MEDIA_SHAPED`、`REQUEST_ASPECT_SHAPED`、`TYPE_FIXED`、`EXPLICIT_SEMANTIC_FRAME` 四类 frame policy，以及 node poster、candidate、detail、editor、mark overlay 和 export 的具名 rendition profile；
- 给出 cover/contain 双向坐标公式、border/content-box 边界、transform identity、mixed-ratio output 原子切换、last-known-good metadata 和 thumbnail/full freshness 规则；
- 将 passive measurement 与 semantic resize 分离，引入 `frameRevision`、`renditionRevision`、`measurementEpoch`，禁止 stale rect 驱动选中节点 toolbar、lower panel 或 editor surface；
- 新增 42 条 `LIBTV-MRG-I-*`、`GI-101..116`、`GC-127..145`、`LIBTV-FIX-LOCAL-MEDIA-RENDITION-01`、`LIBTV-VR-023` 与 `LIBTV-MRG-DQ-001..014`；
- 明确拒绝把 `width/height` 合并为一组字段、把 `object-fit` 当 node policy、把 request aspect 当 actual output、把 measured rect 当持久 resize 或照搬 Open Canvas fixed card policy；
- runtime 仍 fragmented，source portrait/square/video/mixed-output/resize 仍 gated；本轮没有修改 `src/`、测试脚本、FrameOS、Director runtime、共享源站、其他开发者 WIP 或任一 submodule。

## 2026-08-27：v55 media rendition 组件规格贯穿

本轮逐份复核媒体节点、详情预览和节点内编辑 surface，消除“normalized”等于“full intrinsic”的隐含错误：

- `ImageNode.spec.md` 区分 `ImageNodeData.width/height`、graph frame 和 passive measured rect，记录 generic/derived/Director still 的 ratio mismatch，并保留初始 landscape fixture 的 source-shaped 正面方法；
- `VideoNode.spec.md` 将 presentation `resolution`、poster intrinsic、full-video intrinsic 和 graph frame 分权，记录 ordinary poster cover 与 Director video contain 是未命名 runtime branch，不是 source policy；
- `ImagePreviewOverlay.spec.md` 将 preview 定义为 `DETAIL_INSPECTOR`，同时记录当前直接信任 node-data dimensions、缺少 output identity/provenance/invalid-metadata path 的事实；
- `PictureEditPanel.spec.md`、`SubtitleErasePanel.spec.md`、`ImageAnnotateMode.spec.md` 和 `ImageElementEditMode.spec.md` 明确当前 marks/canvas/stage 绑定 visible cropped node plane，未来 full-media 操作必须经过 content-box/fit transform 和 drift baseline；
- `ShotBreakdownNode.spec.md` 将 fixed near-16:9 cover 限定为 thumbnail/scanning role，不允许它泄漏成普通 node/detail/editor/export 几何；
- 八份规格共同指向正式 geometry contract 与 designed `LIBTV-VR-023`，现有 batch verifier 仍只是当前局部交互/兼容证据；
- 本轮只修改文档，没有修改 `src/`、测试脚本、FrameOS、Director runtime、共享源站、其他开发者 WIP 或任一 submodule。
