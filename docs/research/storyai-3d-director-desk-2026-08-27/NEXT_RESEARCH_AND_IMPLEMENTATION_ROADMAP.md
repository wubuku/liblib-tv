# StoryAI 启发下的 Director 后续路线图

> 状态：`CURRENT_GUIDANCE / NO_CODE_AUTHORIZATION`
> 本路线图给出建议顺序，不代表已授权实施。

## 1. 推荐策略

当前 Director 已经有足够多的用户可见能力。下一阶段应从“feature breadth”转向
“durable authoring core”，顺序是：

```text
current evidence authority
  -> project/session identity
  -> command/history/reference repair
  -> resource/persistence lifecycle
  -> panorama + real asset vertical slice
  -> multi-camera/shot lifecycle
  -> authenticated LibTV UI/UX calibration
```

## 2. 价值队列

| 优先级 | 工作 | 用户价值 | 风险降低 | 前置条件 | 授权 |
|---|---|---|---|---|---|
| P0 | Director project/session/owner contract | 跨节点、跨画布和刷新后可预测 | 最高 | 研究可立即做 | 编码未授权 |
| P0 | Director command/history/delete repair contract | 复杂编辑可撤销、可安全删除 | 最高 | project identity | 编码未授权 |
| P0 | current verifier manifest | 清楚知道当前 HEAD 是否稳定 | 高 | fixture inventory | 脚本编码未授权 |
| P1 | resource ingress/lease/persistence contract | 真实资产不再是 proxy 假象 | 高 | 复用 media ingress authority | 编码未授权 |
| P1 | panorama node -> Director scene input | 主画布与 3D 场景形成高价值连接 | 高 | owner/resource contract | source/product 决策 + 编码未授权 |
| P1 | real local mesh vertical slice | 本地模型真正出现在 R3F 中 | 中高 | format/license/error policy | 编码未授权 |
| P2 | multi-camera/shot lifecycle | 真正支持多镜头预演 | 中高 | source evidence + schema | 编码未授权 |
| P2 | scene settings parity | 提高场景搭建效率 | 中 | source evidence | 编码未授权 |
| P2 | authenticated UI/UX calibration | 提升 LibTV 还原准确度 | 中 | 可访问 source fixture | 只读取证可做；变更未授权 |
| P3 | remote asset/cloud/project sync | 跨设备/账户工作流 | 高复杂度 | backend/product scope | 不在当前 frontend prototype 范围 |

## 3. 研究工作包

这些工作不修改业务代码，可优先继续：

### `STORY-R01` Project Authority Static Audit

- 枚举 Director scene/object/group/camera/capture/timeline/path/local asset identity；
- 记录每个 action 的读写字段、引用、副作用和当前 owner；
- 定义 runtime state、portable project、session UI、resource lease 四层；
- 输出 V1 schema 草案、migration table 和 unknown queue。

完成标志：任何 agent 能判断一个字段是否应持久化、进入 history 或按 node 隔离。

### `STORY-R02` Command / History / Delete Matrix

- 枚举现有 Director mutation entrypoint；
- 将动作分为 transient、gesture commit、semantic command、async result；
- 为 object/group/camera/track/path/capture/local asset 删除定义 reference repair；
- 明确 Director history 与普通 canvas graph history 的边界。

完成标志：能为每个动作回答 one-entry、noop、reject、undo/redo 和 cleanup。

### `STORY-R03` Resource And Panorama Crosswalk

- 复用 [`../LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](../LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)；
- 对照 StoryAI local model/panorama loader 与当前 proxy import；
- 定义 accepted formats、MIME/size、metadata probe、parse error、object URL lease；
- 设计普通 LibTV panorama/image node 到 Director scene asset 的 typed handoff。

完成标志：资源身份与 scene instance 分离，不把 data URL 当 durable asset。

### `STORY-R04` Current Verifier Manifest

- 将 17 个历史脚本映射到 current contracts、fixtures、artifacts 和运行成本；
- 标记 `CURRENT_GATE / HISTORICAL_ONLY / MERGE_CANDIDATE / SOURCE_STALE`；
- 设计不覆盖历史截图的 current smoke/full 命令；
- 将 Three.js deprecation/performance warnings 分为 accepted baseline 与 regression。

完成标志：一个入口能报告当前 Director 核心链，历史 batch 仍可追溯。

### `STORY-R05` Authenticated Source Reinspection

- 复核 shell、panel、timeline、resource library、camera、capture、path 和 export；
- 采集 desktop/mobile、selected state、overlay geometry、close/focus/keyboard；
- 只读共享 fixture；涉及创建、上传、导出或删除时必须另有 disposable fixture
  与逐动作授权；
- 将结果写为 dated source evidence，不覆盖 2026-08-26/27 旧记录。

完成标志：能把 `SOURCE_GATED` 能力拆成 source match、clone decision 和 unknown。

## 4. 待授权实施批次

### `STORY-I01` Director Project Document

目标：把单例 store 状态变为可版本化、可按 owner 隔离的 project document。

最低合同：

- `route/canvasId/sourceNodeId/projectId/schemaVersion/generation` owner；
- strict decode、migration、unknown-field policy；
- scene/objects/groups/cameras/timeline/paths/captures/resource refs 的 portable schema；
- open/switch/close/delete/duplicate canvas lifecycle；
- session UI 和 WebGL runtime refs 不进入 document。

不包含：cloud sync、账号资产和 StoryAI JSON 直接兼容。

### `STORY-I02` Director Edit Safety

目标：提供 reference-aware commands、undo/redo、copy/paste 和 object delete。

最低合同：

- one gesture -> one Director history entry；
- invalid/noop -> zero history；
- 删除修复 group member、track、path、camera relation、active selection/camera；
- canvas result return 继续只产生普通 graph 的一步 history；
- foreground shortcut 不穿透普通 canvas。

### `STORY-I03` Real Asset And Panorama Slice

目标：完成一个真实、可失败、可清理的本地资产纵切。

建议只选一种 mesh format 加 panorama：

- validate -> probe/parse -> object URL lease -> R3F object -> scene instance；
- error/retry/cancel/cleanup 可见；
- project document 只存 stable descriptor，不存 File/Blob/Object3D；
- panorama 可从普通 canvas media node typed handoff；
- 不宣称 remote upload 或 durable cloud asset。

### `STORY-I04` Multi-Camera And Shot Lifecycle

目标：在 source/product 语义明确后补多机位工作流。

最低合同：camera rig、shot record、active camera、capture grouping、timeline track、
delete fallback 和 result provenance identity 清晰。不要先把 StoryAI 的 dual record
原样复制进当前内嵌 camera object。

### `STORY-I05` Source Calibration

目标：用新的 authenticated evidence 校准 shell、controls、geometry、copy 和
responsive behavior。此批只改被证据命中的视觉/交互，不借机重写 project core。

## 5. 停止条件

出现以下任一情况时，不继续扩展实现：

- 没有明确编码授权；
- project/history/resource authority 尚未形成而新功能需要再写 store；
- 需要上传、生成、删除或导出源站数据但没有 disposable fixture/动作授权；
- 真实资产 license/format 未确认；
- 新设计只能由 StoryAI 截图推出，缺少 LibTV source 或明确 clone-owned 标记；
- 当前 verifier manifest 无法覆盖将要修改的共享行为。

## 6. 推荐的第一步

下一轮只做 `STORY-R01 + STORY-R02` 文档工作最划算。它们能同时解锁持久化、
undo、delete、multi-camera、real asset 和 verifier consolidation，且不会干扰当前
业务 WIP。得到编码授权后，优先 `STORY-I01`，不要从新的视觉亮点开始。
