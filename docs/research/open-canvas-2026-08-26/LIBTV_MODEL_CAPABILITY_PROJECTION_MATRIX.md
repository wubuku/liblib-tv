# LibTV 模型能力与执行投影矩阵

> 状态：`CURRENT_RESEARCH` / `CURRENT_GUIDANCE`
>
> 对应：`OC-BP-006`、`OC-ADOPT-010`、`OC-TR-006`
>
> 当前授权：研究和设计；不接入 Provider、上传、计费、任务或远端保存

## 1. 目的

模型菜单能看见一个模型、参数面板能选择一个字段、前端能构造一份 descriptor、后端存在 adapter，以及 current runner 能成功回写结果，是五件不同的事。

Open Canvas 固定版本正好暴露了这类漂移：模型 registry、provider 设置、legacy execute route 和 current canvas runner 的覆盖范围不同。对 LibTV 的价值不是复制它的 registry，而是用同一审计方法阻止当前 clone 把“source-visible UI”升级成“真实可执行能力”。

本文统一回答：

1. LibTV 当前源站可见什么；
2. clone 当前呈现和保存什么本地状态；
3. 哪些字段只是视觉/authoring contract；
4. 需要什么证据才能声明 request、adapter 或 run 已支持；
5. 后续模型能力抽象应停在哪个授权边界。

## 2. 证据分层

| Layer | 可证明内容 | 当前证据 | 不可推出 |
|---|---|---|---|
| `L0 Source-visible catalog` | 菜单中可见 label、estimate、premium、selected description | live audit、Batch 22 screenshot analysis | 完整模型库、可调用性、账户权限 |
| `L1 Source-visible authoring` | selected model/mode 下可见/禁用字段、范围和费用提示 | Seedance 2.5 normal/long DOM 与截图 | 其他模型使用同一字段或范围 |
| `L2 Clone UI state` | 当前组件本地 model/mode/params/credits 和 local feedback | `VideoGenerationPanel.tsx`、Batch 21/22/33 verifier | 真实 request、计费、任务 |
| `L3 Request projection` | authoring snapshot 可映射为稳定 descriptor | 当前只有部分 clone-shaped metadata | provider 接受该 descriptor |
| `L4 Adapter / runner` | endpoint、鉴权、校验、请求、轮询、取消、错误、结果回写 | 当前项目没有实现 | 菜单或 descriptor 能证明执行成功 |

只有 `L0-L2` 有较成熟证据。`L3` 是设计边界，`L4` 属于 `LIBTV-PAR-012 OUT_OF_SCOPE`。

## 3. Source-visible 模型目录

### 3.1 2026-08-27 current loaded DOM catalog

新日期只读审计已在现有 failed video 的模型 dialog 中读取全部 `35` 个 loaded DOM row，其中前 `14` 行在当前 fixture 中使用 selectable style，后 `21` 行使用 `cursor-not-allowed opacity-50`。完整 label、estimate、premium、description、selected/style 状态和 screenshot 见 [`LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md`](LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md) 与 [`libtv-model-catalog-audit-2026-08-27.json`](libtv-model-catalog-audit-2026-08-27.json)。

35 行是当前登录态、当前失败视频和当前部署的 dialog 数据，不是 adapter/runner 支持表。所有 row 的 native `disabled=false` 且无 `aria-disabled`，因此 unavailable 只能作为当前 CSS/interaction style 事实，原因保持未知。

### 3.2 2026-08-25 历史顶部样本

以下七项来自 2026-08-25 的可见菜单顶部样本。它们仍解释历史截图，但不再承担当前 catalog 完整性：

| UI order | Visible label | Estimate text | Premium marker | Confirmed selected description | Evidence boundary |
|---:|---|---|---|---|---|
| 1 | Seedance 2.5 | `2min` | yes | `最强视频模型，全能参考，30s音画同步` | description confirmed；estimate 语义未证明是 SLA |
| 2 | Seedance 2.0 VIP | `2min` | yes | unknown | no inferred description |
| 3 | Minimax H3 | `2min` | yes | unknown | no inferred mode/parameter support |
| 4 | Seedance 2.0 Fast VIP | `2min` | yes | `最强视频模型快速版，会员专属通道，15s音画同步` | description confirmed；不等于 current adapter |
| 5 | Seedance 2.0 Mini | `2min` | yes | unknown | no inferred capability |
| 6 | Wan 3.0 Prime | `1min` | no | unknown | visible row only |
| 7 | Wan 3.0 | `3min` | no | unknown | visible row only；菜单底部可能还有内容 |

当前规则：

- `2min/1min/3min` 只记录为菜单 estimate text，不写成生成时长、排队 SLA 或请求超时；
- premium diamond 只证明 UI 标记，不证明当前账户可执行；
- 2026-08-27 的 35 行 description 可进入 dated source-visible contract；旧截图仍只证明当时直接读取的两个 description；
- 35 行可称 current loaded DOM catalog，不得称“完整支持模型列表”；
- 未逐项切换并读取参数前，不把 Seedance 2.5 的 mode/control matrix 套给其他模型。

## 4. Seedance 2.5 Authoring Capability

### 4.1 Mode menu

当前选中 Seedance 2.5 时的 source-visible mode：

| Mode | Source state | Clone representation | Execution claim |
|---|---|---|---|
| 文生视频 | disabled | disabled menu row | none |
| 全能参考 | enabled | `omnireference` | local authoring only |
| 图生视频 | disabled | disabled menu row | none |
| 首尾帧 | disabled | disabled menu row | none |
| 图片参考 | enabled | `image-reference` | local authoring only |
| 视频编辑 | disabled | disabled menu row | none |
| 超长视频 Beta | enabled | `long-video` | local process graph only |

Disabled row 是产品状态的一部分，不能因 clone 有相邻工具或 graph action 就宣称该 mode 可用。

### 4.2 Control projection

| Control | Normal source | Long source | Current clone | Projection decision |
|---|---|---|---|---|
| ratio | `Auto/16:9/4:3/1:1/3:4/9:16/21:9` | same visible set | same local strings | UI vocabulary only；real API enum unknown |
| resolution | `480P/720P/1080P` | same visible set | same local strings | visible label not provider key |
| duration | `4-30s`；sample `6s` | `30-300s`；sample `30/300s` | local slider with mode range | sampled current product range, not permanent API contract |
| audio | on/off | on/off | local boolean | request/provider behavior unknown |
| count | visible segmented control | absent | normal local count；long hidden | omission is mode capability, not CSS-only difference |
| helper | none in sampled normal dialog | visible long-duration guidance | conservative clone paraphrase | clone copy is not verbatim source DOM |
| credits | visible near submit | `300s / 14700` observed | normal `duration*46*count`; long `duration*49` | formulas are clone calibration; only sampled values are source facts |
| references | reference strip and input commands | same authoring context | three local mock assets | no upload/permission/provider projection |
| Auto Link | advanced global preference | same preference concept | currently local component state | separate typed identity contract |

The clone's `settingsLabel` includes count even when long mode hides count in the dialog. This is a current clone representation detail to inspect in any future fidelity slice, not evidence that source long mode submits a count.

## 5. 三层能力矩阵

| Capability claim | Source-visible UI | Clone UI / local graph | Request/runner | Current classification |
|---|---|---|---|---|
| browse current 35-row loaded model catalog | yes；14/21 为当前 fixture style split | clone 只有有界菜单样本 | no adapter proof | `UI_ONLY` |
| selected-only description | two descriptions confirmed | rendered for confirmed rows | irrelevant | `SOURCE_SHAPED_UI` |
| normal Seedance params | yes | local state and historical verifier | no request | `SOURCE_SHAPED_UI` |
| long Seedance params | yes | local state and 12/22 graph handoff | no task | `BOUNDED_PROTOTYPE` |
| estimated credits | sampled UI values | clone formula | no billing | `DISPLAY_CALIBRATION` |
| audio generation | visible toggle | local boolean | no audio-capable adapter proof | `UI_ONLY` |
| Auto Link references | source state contract exists | fixed legacy prototype; typed design exists | no provider projection | `DESIGN_FIRST` |
| model-specific field filtering | only Seedance 2.5 sampled | mostly global component controls | no capability registry | `RESEARCH_ONLY` |
| execute model and poll task | source product clearly has backend capability, but this project has no recovered contract | absent | absent | `OUT_OF_SCOPE` |
| result write-back/versioning | source process clues only | local pending/result graph variants | absent | `BLOCKED_BY_FIXTURE` |

## 6. 投影链设计

后续若有明确授权，建议的职责链是：

```text
Source-visible evidence
  -> VisibleCatalogItem
  -> ModelCapabilitySnapshot
  -> AuthoringDraft
  -> validated SubmissionSnapshot
  -> provider-neutral RequestDescriptor
  -> authorized Adapter
  -> Run / Result lifecycle
```

这些名称是 `DESIGN_VOCABULARY`，不是当前代码类型。

| Boundary | Responsibility | Must retain | Must not know |
|---|---|---|---|
| visible catalog | render label/estimate/premium/confirmed copy | source date and evidence status | provider credentials |
| capability snapshot | determine fields, defaults, ranges, disabled states | model + mode + capability version | live task state |
| authoring draft | mutable Prompt/reference/params | stable reference identities | provider request keys |
| submission snapshot | immutable validated input for one run | source media versions and sampled capability | later draft edits |
| request descriptor | provider-neutral operation and inputs | typed references, duration, output intent | UI geometry or labels |
| adapter | map descriptor to one authorized service | credentials, API validation, errors | React component local state |
| run/result | poll/cancel/retry/write result | run ID, result/version identity | model menu presentation |

当前可以继续设计到 submission/request descriptor 边界，但不能实现 adapter/run，也不能把 UI label 当 request enum。

## 7. Capability Rule Review

每条未来 capability rule 必须记录：

```text
Rule ID:
Source model label and observation date:
Mode:
Input requirements and reference roles:
Visible controls:
Default values:
Allowed values/ranges:
Disabled/hidden conditions:
Display-only estimate/copy:
Clone representation:
Provider-neutral projection:
Adapter evidence:
Fixture:
Verifier:
Unknowns and stop conditions:
```

Rule review 的最低问题：

1. 这是当前模型的事实，还是从 Seedance 2.5 推给其他模型的猜测；
2. 字段隐藏、disabled 和不支持是否被区分；
3. visible label 与 request value 是否分开；
4. 切换 model/mode 后旧 draft 值是保留、normalize 还是清除；
5. reference count/type 是否影响模型可选性；
6. 费用是 source-visible sample、clone estimate 还是真实 billing quote；
7. descriptor 是否捕获 source media version 和 capability version；
8. 没有 adapter 时 UI 是否明确保持 local prototype 边界。

## 8. Fixture 与验证设计

### 8.1 当前可用输入

- `LIBTV-FIX-LOCAL-VIDEO-READY-01` 可构造 selected video 和 local generation panel；
- Batch 21/22 verifier 可证明当前 clone 参数和模型菜单历史合同；
- `LIBTV-FIX-SOURCE-SHARED-01` 只允许读取已有菜单/参数状态，不提交、不生成、不改变持久偏好；
- 没有真实 adapter/task/result fixture。

### 8.2 文档态验证矩阵

| Check | Local fixture | Source evidence | Required result |
|---|---|---|---|
| visible model rows | ready/failed video | 2026-08-27 dated DOM/screenshots | 35-row order、label、estimate、premium、description、selected/current-context style separated |
| normal controls | selected Seedance 2.5 normal | live parameter dialog | field presence, options, default/sample and clone delta |
| long controls | selected Seedance 2.5 long | live parameter dialog | count absent, range/helper/audio and sample credits |
| mode switch normalization | local component | source behavior incomplete | current clone fact recorded; source decision remains open |
| model switch capability | local component uses same controls | source per-model states unavailable | no generalized capability claim |
| descriptor | current long-video metadata is clone-shaped | no source API | design only |
| adapter/run/result | none | no safe request fixture | `OUT_OF_SCOPE` / `BLOCKED_BY_FIXTURE` |

No new replacement verifier is created by this document. A future parity item must first define whether the goal is UI fidelity, capability-driven form correctness or real execution; those have different fixtures and risk.

## 9. Open Canvas 借鉴与拒绝边界

| Upstream lesson | LibTV adaptation | Rejected transplant |
|---|---|---|
| registry and selectable capability can be data-driven | use an evidence-backed capability snapshot if repeated conditionals become risky | copy Open Canvas provider/model IDs |
| typed inputs project late into descriptor | keep Auto Link/media identity outside UI labels | copy scene names or input buckets as LibTV API |
| current runner coverage must be traced separately | require adapter/run/result evidence for execution claims | infer support from registry or settings form |
| unsupported audio is explicit in current runner | distinguish visible toggle from executed audio output | claim LibTV audio generation because toggle is visible |
| provider settings and route drift are auditable | maintain UI/descriptor/adapter/run crosswalk | copy BYOK cookie/key handling |

## 10. 未决问题

| Question | Evidence needed | Current state |
|---|---|---|
| current dialog 在七项之后是否还有模型 | 2026-08-27 scroll/DOM audit | resolved for current fixture：35 loaded rows |
| 35 行是否跨账号/输入条件永久完整 | account/fixture matrix and product contract | unknown；不得泛化 |
| 每个模型支持哪些 mode | model-by-model source selection audit | unknown; do not generalize |
| 每个模型的 ratio/resolution/duration/audio/count | model/mode parameter snapshots | only Seedance 2.5 known |
| estimate text semantics | source copy/help or API | UI text only |
| normal credits formula | multiple current source samples | clone calibration only |
| long credits formula | multiple durations/current source samples | only `300s=14700` sampled |
| request enum and validation | stable business/API contract | unavailable |
| provider, billing and result write-back | new backend scope and authorization | `OUT_OF_SCOPE` |

## 11. 当前决策

1. 以 2026-08-27 的 35 行作为 current loaded DOM catalog，以七项保留 2026-08-25 历史顶部样本；两者都不称执行支持表；
2. 保持 Seedance 2.5 normal/long 为当前最成熟 authoring contract；
3. 不把 clone credits 公式、ratio/resolution strings 或 model IDs 视为 API；
4. 不为其他模型推断 mode/control capability；
5. 不因 Open Canvas 有 registry/runner 就在当前项目引入同类基础设施；
6. 只有多个获批 slice 确实需要共享 capability rule 时，才评审数据驱动抽象；
7. adapter、真实生成、上传、计费、轮询和结果回写继续由 `LIBTV-PAR-012` 拦截。

本文完成 `OC-BP-006` 的文档态三层审计。它没有创建实现 backlog，也没有授权任何代码或源站操作。
