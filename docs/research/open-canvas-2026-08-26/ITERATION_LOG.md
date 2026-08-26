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
