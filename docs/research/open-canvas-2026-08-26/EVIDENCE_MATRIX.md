# Open Canvas 证据与声明矩阵

> 用途：让 agent 在引用 Open Canvas 结论时，能快速区分源码事实、官网运行事实、静态推断和待验证项。置信度只表示本次研究对该声明的证据强度，不表示上游产品质量。

## 1. 置信度规则

| 级别 | 定义 |
|---|---|
| High | 固定 submodule 中有直接源码/配置证据，或官网公开页面在本次浏览器审计中直接可见 |
| Medium | 多个源码位置互相支持，但存在入口漂移、legacy 路径或未执行 live request |
| Low | 仅来自落地页预览、营销文案、代码命名或尚未完成的运行态操作 |
| Pending | 当前无法在无登录/无 key/无副作用条件下确认 |

## 2. 核心声明

| ID | 声明 | 类型 | 置信度 | 直接证据 | 证据支持的范围 | 不能据此得出 |
|---|---|---|---|---|---|---|
| OC-001 | Open Canvas 是 local-first、BYOK 的工作流画布 | 源码 + 官网 | High | [`README.md`](../../../research/upstream/open-canvas/README.md#L8)；[`RUNTIME_AUDIT.md`](RUNTIME_AUDIT.md#2-中文落地页) | 产品定位和入口叙事 | 不代表没有服务端 API、KV 或远程 provider |
| OC-002 | 固定版本支持 `text/note/image/video/audio` 五类节点 | 源码 | High | [`types.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/types.ts#L11) | graph 类型合同、默认 data 和 UI 方向 | 不代表每类节点在真实 runner 都可执行 |
| OC-003 | graph 是 version 1 的可序列化 DAG | 源码 | High | [`serialization.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/serialization.ts#L124)；[`validation.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/validation.ts#L418) | 节点/边/viewport、方向归一化、数量和环检测 | 不代表可以自由创建环或接受任意第三方 graph |
| OC-004 | 输入会按文字、图片、风格、omni、视频、音频分桶 | 源码 | High | [`execution.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/execution.ts#L191) | descriptor 之前的语义解析 | 不代表每个 provider 都消费全部 bucket |
| OC-005 | scene 由节点类型、输入和模型设置推断 | 源码 | High | [`execution.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/execution.ts#L282) | text/image/video/audio 的场景分类 | 不代表 provider API 接受同名 scene |
| OC-006 | 模型 registry 路由范围大于基础设置表单 | 源码 | High | [`public-ai-models.ts`](../../../research/upstream/open-canvas/shared/services/public-ai-models.ts#L527)；[`provider-settings.ts`](../../../research/upstream/open-canvas/lib/provider-settings.ts#L5) | registry 和用户可配置 provider 的结构差异 | 不代表 registry 中每个 provider 已有 current runner adapter |
| OC-007 | 当前具体 canvas execute route 的 runner 以 Cyberbara 为执行通道 | 源码调用链 | High | [`execute route`](../../../research/upstream/open-canvas/app/api/canvas/[canvasId]/nodes/[nodeId]/execute/route.ts#L1)；[`local-canvas-runner.ts`](../../../research/upstream/open-canvas/shared/services/canvas/local-canvas-runner.ts#L90) | 当前 `/canvas/[canvasId]` 页面实际调用的静态路径 | 不代表 legacy `/api/execute` 没有其他分支 |
| OC-008 | legacy `/api/execute` 包含 OpenRouter/Replicate 分支 | 源码 | High | [`app/api/execute/route.ts`](../../../research/upstream/open-canvas/app/api/execute/route.ts#L1) | 旧 endpoint 的静态能力 | 不代表当前 studio 页面使用该 endpoint |
| OC-009 | Audio 已进入图模型/descriptor，但 current OSS runner 明确未接通生成 | 源码 | High | [`types.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/types.ts#L110)；[`local-canvas-runner.ts`](../../../research/upstream/open-canvas/shared/services/canvas/local-canvas-runner.ts#L190) | 数据层存在、执行层抛出未接通错误 | 不代表音频 UI/上传方向不存在 |
| OC-010 | 画布保存有 revision、dirty、saving、saved、error、conflict 语义 | 源码 | High | [`canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L80)；[`local-canvas-store.ts`](../../../research/upstream/open-canvas/shared/models/local-canvas-store.ts#L302) | graph 保存与冲突处理合同 | 不代表所有 DB 更新都有全局原子事务 |
| OC-011 | 本地开发默认使用 `data/open-canvas-db.json`，Cloudflare 使用按 client ID 的 KV | 源码 | High | [`local-canvas-store.ts`](../../../research/upstream/open-canvas/shared/models/local-canvas-store.ts#L77) | alpha local-first 持久化路径 | 不代表这是多用户认证或协作同步 |
| OC-012 | `open_canvas_client_id` 是命名空间标识，不是认证 | 源码 + 推断 | High | [`middleware.ts`](../../../research/upstream/open-canvas/middleware.ts#L13)；[`local-canvas-store.ts`](../../../research/upstream/open-canvas/shared/models/local-canvas-store.ts#L91) | cookie 创建和 KV key 构造 | 不代表公开托管环境已有访问控制 |
| OC-013 | provider settings cookie 不是 HttpOnly，包含归一化设置 | 源码 | High | [`provider-settings-cookie.ts`](../../../research/upstream/open-canvas/lib/provider-settings-cookie.ts#L19)；[`provider-settings-cookie.ts`](../../../research/upstream/open-canvas/lib/provider-settings-cookie.ts#L42) | 当前 alpha 的 key 传递方式和硬化风险 | 不代表本次研究读取了任何真实 key |
| OC-014 | 官网首屏以 BYOK、空间化画布、多模态节点、保存/分享/缩放/播放预览传达产品形象 | 官网运行事实 | High | [`RUNTIME_AUDIT.md`](RUNTIME_AUDIT.md#2-中文落地页)；[桌面截图](../../design-references/open-canvas-official-landing-zh-2026-08-26.png) | 公开页面的信息层级 | 不代表每个预览标签对应固定 alpha 版本的可用功能 |
| OC-015 | `/zh/canvas` 空状态显示设置、JSON 导入、新建画布，并自动弹出设置向导 | 官网运行事实 | High | [`RUNTIME_AUDIT.md`](RUNTIME_AUDIT.md#3-中文画布入口)；[空状态截图](../../design-references/open-canvas-official-canvas-empty-zh-2026-08-26.png) | 未登录、无 key 场景的入口流程 | 不代表已验证节点编辑和生成流程 |
| OC-016 | 官网 provider marquee/向导的宣传范围宽于本次已核实的 current execute runner | 交叉推断 | Medium | OC-006、OC-007、OC-014、OC-015 | 需要在报告中标记的声明/实现漂移 | 不代表官网是错误页面，可能对应其他部署或目标状态 |
| OC-017 | 当前尚未完成 studio 选中节点上下浮层的运行态几何审计 | 研究边界 | High | [`RUNTIME_AUDIT.md`](RUNTIME_AUDIT.md#6-仍需后续取证的交互) | 清楚标记哪些内容不可用于视觉 clone | 不代表源码中的 Panel 没有定位逻辑 |
| OC-018 | Open Canvas 的 selected editor/action overlay 共用 measured node + live viewport 的 screen anchor 语义，但分别位于节点上下 | 源码 | High | [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L5964)；[`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L6015) | 可迁移的几何组织方法 | 不代表 LibTV 应改用同样的 Panel 容器或数字 |
| OC-019 | 当前 clone 的 ImageNode 已将顶部 `NodeToolbar` 与节点内底部 `ImageEditPanel` 分开实现 | 当前仓库源码 | High | [`ImageNode.tsx`](../../../src/components/nodes/ImageNode.tsx#L125)；[`ImageNode.tsx`](../../../src/components/nodes/ImageNode.tsx#L166) | 当前实现形态和后续诊断入口 | 不代表当前运行态所有边缘/缩放场景都已验证 |
| OC-020 | 当前 LibTV 复刻合同要求工具条以节点中心为基准、编辑器跟随节点并反向缩放，且边缘允许裁剪 | LibTV 研究记录 | High | [`ImageNode.spec.md`](../components/ImageNode.spec.md#selected-state)；[`ImageEditPanel.spec.md`](../components/ImageEditPanel.spec.md#positioning-contract) | LibTV 的源站行为基线 | 不代表 Open Canvas 的几何合同可以覆盖它 |
| OC-021 | Open Canvas 的 Quick Add 同时保存菜单屏幕坐标和 `screenToFlowPosition` 后的节点 flow 坐标 | 源码 | High | [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4144)；[`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4899) | 菜单定位与 graph 落点的双坐标关系 | 不代表 LibTV 的新增节点也以相同位置或 clamp 规则落点 |
| OC-022 | Open Canvas 的悬空连线结束于 React Flow pane 时会以释放点打开 connection Quick Add，并保存 pending source/handle | 源码 | High | [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L6046) | 连接入口与创建节点的状态链 | 不代表 LibTV 源站存在相同的悬空连线菜单 |
| OC-023 | Open Canvas 选择 Quick Add 节点后，先创建节点，再依据 pending connection 方向创建边，失败以 toast 反馈并关闭菜单 | 源码 | High | [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4925) | 一次用户动作中的 graph mutation 顺序 | 不代表 clone 应复制其节点类型、文案或连接方向 |
| OC-024 | Open Canvas 将 clipboard 限定为 versioned 选中子图，复制内部边并在粘贴时重写 ID、按视口中心和递增偏移落点 | 源码 | High | [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L3896)；[`canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L339) | 可复用的复制/粘贴 graph 边界 | 不代表当前 LibTV 的父子、派生节点和媒体字段可以被该 payload 替换 |
| OC-025 | Open Canvas 将节点/任务运行状态与画布保存状态分开，并以 debounce 保存 dirty graph | 源码 | High | [`types.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/types.ts#L11)；[`canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L38)；[`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4868) | 反馈状态的分层建模 | 不代表当前 LibTV prototype 已有真实运行、保存或冲突后端 |
| OC-026 | current studio 在 execute 前保存 graph，并以 revision + node ID 创建独立 run；非 terminal run 以 run ID 轮询，页面可从 node `status + lastRunId` 恢复 polling | 源码调用链 | High | [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4768)；[`local-canvas-runner.ts`](../../../research/upstream/open-canvas/shared/services/canvas/local-canvas-runner.ts#L90)；[`run route`](../../../research/upstream/open-canvas/app/api/canvas/[canvasId]/runs/[runId]/route.ts#L1) | descriptor/run/poll 控制面与 reload recovery | 不代表 run reservation 与 revision compare 是原子事务，也不证明 cancel/retry UI 已接通 |
| OC-027 | server node patch 会增加 durable canvas revision，并在 client 同时 patch live node 与 saved graph baseline | 源码 | High | [`local-canvas-store.ts`](../../../research/upstream/open-canvas/shared/models/local-canvas-store.ts#L337)；[`canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L836) | remote authority 与 local dirty/save baseline 分层 | 不代表 patch 已校验 current run、source version 或每个字段的 owner |
| OC-028 | fixed node patch path 只以 canvas/node existence 定位目标，不要求 expected current run、source version 或 expected revision；client apply 也不比较 `lastRunId` | 源码 | High | [`types.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/types.ts#L670)；[`local-canvas-store.ts`](../../../research/upstream/open-canvas/shared/models/local-canvas-store.ts#L337)；[`canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L836) | stale-write 与 field ownership 的静态设计缺口 | 不证明已经发生生产事故，也不表示 revision/save 分层没有价值 |
| OC-029 | runner 在创建 `running` run 后才进入 audio unsupported/provider 调用，且没有 runner-level catch/finally 将异常 run 收敛为 terminal failure | 源码 | High | [`local-canvas-runner.ts`](../../../research/upstream/open-canvas/shared/services/canvas/local-canvas-runner.ts#L120)；[`local-canvas-runner.ts`](../../../research/upstream/open-canvas/shared/services/canvas/local-canvas-runner.ts#L190) | 失败补偿和 stranded-run 风险 | 不证明所有 provider 异常都必然留下同一状态，也不替代 live provider 测试 |
| OC-030 | local store 的 `updateDb` 是无 storage CAS 的 read-modify-write；run terminal update 与 node patch 使用独立写入 | 源码 + 并发推断 | Medium | [`local-canvas-store.ts`](../../../research/upstream/open-canvas/shared/models/local-canvas-store.ts#L133)；[`local-canvas-runner.ts`](../../../research/upstream/open-canvas/shared/services/canvas/local-canvas-runner.ts#L160) | graph projection recovery 与并发验证需求 | 不等于已证明数据丢失；需要并发实验、部署拓扑和 storage 语义才能升级为运行事实 |

## 3. 对当前 clone 的引用规则

引用 Open Canvas 结论时按以下规则处理：

1. 只引用带 ID 的声明，或先为新声明增加 ID；
2. 涉及产品“有什么”时优先引用 OC-002、OC-004、OC-005、OC-010、OC-014、OC-015；
3. 涉及“能否执行”时必须同时检查 OC-006、OC-007、OC-008、OC-009；涉及结果回写/竞态时再检查 OC-026..030；
4. 涉及安全/托管时必须同时检查 OC-011、OC-012、OC-013；
5. 不能用 Open Canvas 的源码事实替代 LibTV 源站证据；
6. 不能用官网预览、provider marquee 或 README 宣称证明当前 clone 已实现。
7. 涉及选中、连线、视口、复制、媒体历史或状态反馈时，优先查阅 [`INTERACTION_CATALOG.md`](INTERACTION_CATALOG.md) 的模式和 batch 合同。

## 3.1 当前 LibTV 源站补充声明

| ID | 声明 | 类型 | 置信度 | 直接证据 | 证据支持的范围 | 不能据此得出 |
|---|---|---|---|---|---|---|
| LIBTV-001 | 当前图片标准工具条 host 以节点屏幕中心为水平 anchor，top 为 `nodeTop - 24 * zoom - 10`，并以 `translateY(-100%)` 抬起自身高度；因此顶部 gap 为 `10 + 24 * zoom` | 当前生产 chunk + live DOM | High | [`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](LIBTV_OVERLAY_MULTIZOOM_MATRIX.md#35-源站-chunk-对顶部-host-定位的直接证据)；[`libtv-overlay-multizoom-audit-2026-08-26.json`](../liblib-seedance-2.5-2026-08-25/libtv-overlay-multizoom-audit-2026-08-26.json) | 标准图片工具条的 screen-space 定位合同 | 不代表标注、旋转、元素编辑或图层分离专用 host 使用同一定位分支，也不代表 clone 的 `NodeToolbar offset=16` 已经等价 |
| LIBTV-002 | 元素编辑空态会替换标准 toolbar/panel，提供 point/box/brush、初始 mask/guide 和空 record panel；Escape 可恢复标准双浮层 | 当前 live DOM | High | [`LIBTV_IMAGE_ACTION_MATRIX.md`](LIBTV_IMAGE_ACTION_MATRIX.md#31-元素编辑)；[`LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md#13-元素编辑与旋转入口的安全边界) | 元素编辑空态的层级、几何和退出合同 | 不代表非空 record 的生成、上传、任务或输出节点语义已在共享画布验证 |
| LIBTV-003 | 当前共享画布点击旋转入口产生了一个选中的“旋转与镜像”派生节点，单次 `Meta+Z` 可撤销该节点；旋转入口应按可 graph mutation 的高风险动作处理 | 当前 live DOM + 撤销结果 | High | [`LIBTV_IMAGE_ACTION_MATRIX.md`](LIBTV_IMAGE_ACTION_MATRIX.md#34-旋转与镜像)；[`LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md#13-元素编辑与旋转入口的安全边界) | 当前 fixture 的入口副作用和研究安全边界 | 不代表所有项目权限、图片状态或部署版本都一定走同一派生路径，也不代表保存/上传合同已确认 |

## 4. 待补证据队列

| 优先级 | 待验证项 | 最小证据 | 当前阻塞 |
|---|---|---|---|
| P0 | studio 选中节点上下 Panel 的实际位置和缩放行为 | 登录/可创建画布；DOM rect + 929/390 截图 | 本次无登录、无创建操作 |
| P0 | current runner 与官网部署是否同一版本 | 官网 network/API 版本信息或部署 commit | 公网部署版本未锁定 |
| P1 | 真实 provider 执行覆盖范围 | 每类 provider 的无付费 mock/live 请求结果 | 无 key，不触发生成 |
| P1 | 模板/分享按钮是真能力还是预览 | 入口点击前后 URL/API/DOM 变化 | 本次保持只读 |
| P2 | KV 并发下的 read-modify-write 行为 | 并发写入实验与冲突日志 | 当前研究不部署/不压测 |

## 5. 结论使用示例

### 合法

> “固定源码建模了 Audio 节点，但 current OSS runner 抛出未接通错误（OC-009），所以 clone 的 Audio UI 不能直接宣称已有真实生成能力。”

### 不合法

> “官网展示了 Replicate，所以 Open Canvas 当前 studio 已经可以稳定执行所有 Replicate 模型。”

第二种说法混用了官网宣传和运行事实，且没有经过 OC-007/OC-008 的入口核对。
