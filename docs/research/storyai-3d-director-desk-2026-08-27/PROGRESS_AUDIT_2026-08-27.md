# LibTV Director Desk 借鉴进展审计

> 审计日期：2026-08-27
> 固定上游：`storyai-3d-director-desk@8c8bd36`
> 当前结论：**功能纵深高，核心工作流已成立；项目可靠性、真实资产和 source fidelity 尚未闭环。**

## 1. 审计方法与快照

本审计同时读取四类事实，避免只按 UI 功能数量判断完成度：

1. 固定 StoryAI 源码：schema、store、canvas、panels、io、loaders、tests；
2. 当前 clone 源码：Director components/store、React Flow entry、result return；
3. 历史证据：Batch 34-50、59 的 spec、implementation、screenshot 和 verifier；
4. 当前运行：localhost 只读 Playwright desktop smoke。

量化快照仅用于说明规模，不作为质量分数：

| 项目 | StoryAI 上游 | 当前 clone Director |
|---|---:|---:|
| TypeScript 行数 | 17,675 | 13,563 |
| 源码/领域文件 | 86 个 `src` 文件 | 20 个 Director component/utility + 1 store |
| test 文件 / focused verifier | 35 个 test 文件 | 17 个历史 Playwright verifier |
| 当前测试结果 | build PASS；304/312 tests | 本轮 smoke PASS；未重跑全部 17 个历史脚本 |
| 历史研究/合同文件 | Batch 34 代码考古 | Batch 35-50、59 共 124 个 batch 文件 |
| Director 设计参考图 | README 7 张上游图 | 95 张 clone Director 图 |

上游 8 个失败测试并非单一环境噪声：model library 3 项，scene style、aspect
overlay、pose calibration、gizmo hit geometry、camera visual scale 各 1 项。
build 虽通过，仍报告缺失缩略图运行警告和约 `1.36 MB` chunk 警告。因此本审计
把上游视为高价值研究对象，不把它视为可直接继承的全绿工程基线。

## 2. 能力进展矩阵

状态定义：

- `ADOPTED`：已吸收上游模式并形成当前 clone 合同；
- `EXTENDED`：clone 已超出固定上游；
- `PARTIAL`：已有可用切片，但关键真实语义或工程基础缺失；
- `MISSING`：上游已有、clone 当前未实现；
- `SOURCE_GATED`：clone 可用，但不能宣称 LibTV source-exact。

| 能力 | 固定 StoryAI | 当前 clone | 状态 | 判断 |
|---|---|---|---|---|
| React Flow -> Director 入口 | host bridge/session 概念 | canvas node + full-screen lazy island | `ADOPTED` | 边界比 iframe/postMessage 更适合当前同应用架构 |
| 三栏工作台 | 220/300 rail + central viewport | desktop rail + mobile drawer + collapse | `ADOPTED` | IA 稳定，exact LibTV geometry 仍未知 |
| 真实 R3F viewport | 有 | 有 | `ADOPTED` | 主价值已保留，不是 2D 假预览 |
| semantic object tree | 搜索、分组、可见、锁定、删除、多选 | 搜索、分组、多选、可见 | `PARTIAL` | lock/delete/CRUD 不完整 |
| selection-driven Inspector | scene/character/prop/camera route | scene/character/prop/camera/path/group/capture | `EXTENDED` | selection route 已成为稳定架构 |
| TransformControls | translate/rotate/scale | translate/rotate/scale + timeline/path sampling | `EXTENDED` | 仍需统一 edit history |
| scene settings | transform、scale、ground、labels、snap、panorama | colors、ground/grid 显隐 | `MISSING` | 上游低风险基础能力尚未吸收 |
| panorama | file/host import、projection、yaw/radius、remove | 普通 LibTV 有 panorama node；Director 内无输入 | `MISSING` | 是连接主画布与 Director 的高价值缺口 |
| camera object/shot | 多机位、active camera、target/FOV、captures | 单 fixture camera、target/follow/FOV、captures | `PARTIAL` | camera intelligence 强，shot lifecycle 弱 |
| add camera | 有 | 无 action/UI | `MISSING` | 限制真正多镜头创作 |
| add primitive | 多种 geometry | 默认 props + proxy library，无通用 primitive action | `PARTIAL` | 资源库弥补可发现性，但不是等价能力 |
| aspect/rule-of-thirds | 有 | 有 | `ADOPTED` | capture framing 主链成立 |
| native axis gizmo | 有 | 有离散方向控件 | `ADOPTED` | Batch 49 有界合同 |
| character body types | 8 类 body type | 单一 articulated mannequin 视觉基线 | `PARTIAL` | clone 强在姿态，不强在角色体型 breadth |
| pose presets/control | 20 presets + rig controls | 20 source-named presets + SAM controls | `EXTENDED` | 有独立 pose track |
| group/crowd | crowd arrays、group transform | group/crowd + typed group track | `EXTENDED` | Batch 45 已形成纵切 |
| screenshot | current/four/twelve + camera records | current capture、gallery、single/bulk return | `PARTIAL` | 管理/回流更强；多方位 capture breadth 需复核 |
| capture viewer/download | 有 | 有 | `ADOPTED` | 当前 Inspector 中可查看/下载/删除/发送 |
| model library | 有真实/外部 catalog 引用 | 5 类 proxy catalog + preview + insertion | `PARTIAL` | 工作流成立，资产不真实 |
| local FBX/OBJ | data URL + imported asset path | data URL descriptor + proxy object | `PARTIAL` | 两者都不应视为完整生产资产系统 |
| GLTF runtime helper | 有 loader helper | 无 | `MISSING` | 是否采用取决于 LibTV asset format 证据 |
| project schema/version | `DirectorProject.version` + migration | store shape，无独立 project document/version | `MISSING` | 当前最高工程风险之一 |
| project JSON import/export | 有，但 parser 仅 cast | 无 | `MISSING` | 应借结构，不应照抄不校验的 parser |
| project persistence/snapshot | scoped localStorage + latest snapshot | local model list 持久化；scene/timeline 不持久化 | `MISSING` | 页面刷新/多节点恢复未闭环 |
| Director undo/redo | undo stack + batch | 无 | `MISSING` | Batch 50 只阻止背景 undo 穿透 |
| copy/paste | 有 | 无 | `MISSING` | 对重复摆位和群演效率影响高 |
| delete object/camera | 有 | capture/path/local asset 可删；scene object 通用删除缺失 | `PARTIAL` | 引用修复需与 timeline/group/path/camera 共同设计 |
| typed timeline | 无 | transform/camera/pose/group | `EXTENDED` | clone 的核心差异化能力 |
| motion path/curve | 无 | preset/free path、Bezier、speed curve、path transform | `EXTENDED` | source geometry 仍 calibration |
| camera relationship/presets | manual target 基线 | look-at/follow/FP/TP + 7 preset motions | `EXTENDED` | source runtime 细节仍 gated |
| animation video export | 无 | `captureStream` + `MediaRecorder` + graph return | `EXTENDED` | session blob，不是 durable media pipeline |
| phone virtual camera | 无 | local preview + orientation/pointer + track import | `EXTENDED` | 明确不冒充 LAN/QR/WebRTC |
| responsive shell/keyboard | single collapse | desktop/mobile + foreground shortcut boundary | `EXTENDED` | 完整 focus trap 仍缺 |
| current integrated verifier | upstream Vitest suite | 17 个 batch script，暂无单一 current suite | `PARTIAL` | 历史通过不等于每次 HEAD 全量通过 |

## 3. 当前运行复核

2026-08-27 在当前工作区已有 dev server 上进行只读检查，未写 screenshot 或
runtime audit：

| 检查 | 结果 |
|---|---|
| Director workspace | 可打开，`role=dialog`、`aria-modal=true` |
| WebGL | `932x656`，像素输出非空 |
| initial domain state | 5 objects、0 groups、transform + camera tracks |
| 三栏结构 | tree / viewport / Inspector / timeline 可见 |
| resource library | 5 tabs、3 initial cards、1 selected preview |
| add to scene | objects 5 -> 6，新增 object 成为 selection |
| graph isolation | 普通 canvas nodes/edges 保持 10/11 |
| panel collapse | expanded -> collapsed 正常 |
| diagnostics | 无 console/page error；有 Three.js 弃用和 WebGL ReadPixels warning |

该 smoke 只验证当前主链，不替代 17 个历史 verifier，也不证明 mobile、视频录制、
phone vcam、路径绘制和全部截图回流在当前 HEAD 同时通过。

## 4. 成熟度判断

| 维度 | 判断 | 理由 |
|---|---|---|
| 产品骨架 | `HIGH` | 入口、三栏、R3F、selection/Inspector、输出回流完整 |
| 创作功能纵深 | `HIGH` | timeline/path/pose/camera/video/vcam 明显超过上游 |
| StoryAI 基础能力吸收 | `MEDIUM` | shell/viewport/tree/capture 已吸收；project/history/panorama/CRUD 缺失 |
| LibTV source fidelity | `MEDIUM-LOW` | vocabulary/bundle 证据较多，authenticated Director DOM/CSS/runtime 较少 |
| 项目持久性 | `LOW` | Director project 不可版本化、导入导出或按 owner 恢复 |
| 编辑安全 | `LOW-MEDIUM` | graph return 原子化较好；Director 内部缺 undo/delete/reference repair |
| 资产真实性 | `LOW` | catalog/local import 仍以 proxy descriptor 为主 |
| 验证成熟度 | `MEDIUM-HIGH` | 历史专项覆盖丰富，但 current-suite 与持续回归入口缺失 |
| 文档可发现性 | `MEDIUM` -> `HIGH` | 历史分散；本专题建立后有统一入口和当前权威 |

## 5. 最高风险

### 5.1 单例 session 与 owner identity

`openSession(sourceNodeId)` 会保留既有 scene/objects/timeline。多个 Director node
或多个 canvas 不是独立 project；UI owner 虽记录 canvas/node，Director authoring
state 没有对应 registry。继续增加 feature 会扩大串场和恢复风险。

### 5.2 复杂编辑无 domain history

当前 store 已包含姿态、群组、路径、关键帧、相机关系和资源对象等互相引用数据，
却没有统一 mutation transaction、undo/redo 和 object-delete repair。越晚补，
需要兼容的 mutation entrypoint 越多。

### 5.3 资源 descriptor 冒充资产

本地 FBX/OBJ 的 bytes 被编码为 data URL 并形成 proxy visual；它证明 UI/identity
流程，不证明 loader、mesh、texture、skeleton、object URL lease、quota 和错误恢复。
文案与状态必须继续保留 prototype disclosure。

### 5.4 source fidelity 被 clone richness 掩盖

功能丰富容易让人误以为“已经复刻完”。实际 authenticated Director UI、资源库、
timeline、path、export、multi-camera 等 surface 仍缺系统化 DOM/CSS/runtime 量测。
后续 source parity 必须独立于 StoryAI adoption 评估。

### 5.5 verifier 历史碎片化

Batch 35-50、59 的脚本分别拥有自己的 fixture、query flag、artifact 和断言。
它们适合保留历史合同，但不适合作为当前 HEAD 的单命令 release gate。应先建立
current manifest，再决定哪些脚本保留、合并或降级。

## 6. 进展结论

从“有没有可用 Director Desk”看，进展已经很大：主工作流成立，多个关键切片
达到 frontend prototype 的可验证水平。从“能否继续稳定复刻 LibTV”看，当前
最重要的工作不是再加一个亮点按钮，而是把 StoryAI 已经提醒我们的 project、
history、resource、camera/shot 和 host-input 基础补成明确合同。

进一步建议见
[`NEXT_RESEARCH_AND_IMPLEMENTATION_ROADMAP.md`](NEXT_RESEARCH_AND_IMPLEMENTATION_ROADMAP.md)。
