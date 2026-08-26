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

## 3. 对当前 clone 的引用规则

引用 Open Canvas 结论时按以下规则处理：

1. 只引用带 ID 的声明，或先为新声明增加 ID；
2. 涉及产品“有什么”时优先引用 OC-002、OC-004、OC-005、OC-010、OC-014、OC-015；
3. 涉及“能否执行”时必须同时检查 OC-006、OC-007、OC-008、OC-009；
4. 涉及安全/托管时必须同时检查 OC-011、OC-012、OC-013；
5. 不能用 Open Canvas 的源码事实替代 LibTV 源站证据；
6. 不能用官网预览、provider marquee 或 README 宣称证明当前 clone 已实现。

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
