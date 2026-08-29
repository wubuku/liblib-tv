# Batch 95 实施记录：Director 画布媒体入口与全景环境预览

> 状态：`SCRIPT_RECORDED_PASS`
>
> 实施日期：2026-08-29。
>
> 计划 checkpoint：`564e0e8`。
>
> 代码实现 checkpoint：`8b82dd9`；本文件记录其后的验证修复与收口。

## 1. 实施结论

本批完成了普通 LibTV 画布图片节点到 Director 当前 session 环境预览的
clone-owned 纵向切片：

- 当前画布中，当前 `script-execution` Director 节点的直接入边图片会被收集为
  typed `DirectorCanvasMediaInputV1`；
- Director Inspector 可选择、切换和清除直接上游图片；
- 有效图片 URL 会在 R3F 场景中以不可交互的反向 sphere 作为环境预览；
- 选择、加载状态和错误状态都可观察；
- 环境输入保持 session-only，不写入 Director project document、history、
  localStorage 或普通画布 graph；
- source stale 时自动清除，环境球不拦截对象选择和 TransformControls。

这不是 LibTV 原站 source-exact 的 panorama 实现，也不证明原站使用 Three.js、
R3F、同样的 sphere 投影或同样的 Inspector 入口。

## 2. 证据与决策边界

| 分类 | 本批记录 |
|---|---|
| `LIBTV_SOURCE_FACT` | 复用既有 2026-08-27 媒体入口、全景节点和资源分域研究；本批没有新增认证源站 DOM/CSS 事实。 |
| `CLONE_FACT` | 普通图片节点携带 `imageUrl`；Director 由 `script-execution` 节点打开；Director 使用独立 R3F viewport/store。 |
| `STORYAI_FACT` | StoryAI 的资源/场景分层只提供边界启发，不作为 LibTV 行为证据。 |
| `DECISION` | 采用当前 Director 节点直接上游、session-only、非交互环境球和显式 Inspector 选择。 |
| `INFERENCE` | 这条链路适合验证 host handoff、stale cleanup 和纹理失败隔离，但不能推出源站实现。 |
| `SOURCE_UNKNOWN` | LibTV 是否存在同样的 Director panorama session 投影、R3F runtime 或项目持久化字段仍未知。 |

## 3. 代码变更

### 3.1 Typed ingress

新增 [`src/lib/directorCanvasMediaIngress.ts`](../../../src/lib/directorCanvasMediaIngress.ts)：

- `collectDirectorCanvasMediaInputs(canvas, directorNodeId)` 只读取当前 canvas；
- 只接受目标为当前 Director 节点的直接入边；
- 只接受 `type === "image"` 且有非空 `imageUrl` 的节点；
- `editorVariant === "panorama"` 或 `placeholderKind === "panorama"` 时标记
  `sourceKind: "panorama"`；
- 没有真实 URL 的 panorama placeholder 不会被伪装成可加载资源。

### 3.2 Director session projection

[`src/components/director/DirectorDesk.tsx`](../../../src/components/director/DirectorDesk.tsx)
维护当前 Director mount 的 `panoramaSourceId`：

- 默认选择第一个可用直接上游图片；
- source 消失或 URL 失效时自动清除；
- 选择不进入 `DirectorProjectDocumentV1`、Director history 或 localStorage；
- 仍保留普通 canvas graph 的原有 owner 和 mutation 边界。

### 3.3 Inspector 与 R3F runtime

[`src/components/director/DirectorInspector.tsx`](../../../src/components/director/DirectorInspector.tsx)
增加环境图片选择、清除和四态反馈：

- `empty`
- `loading`
- `ready`
- `error`

[`src/components/director/DirectorViewport.tsx`](../../../src/components/director/DirectorViewport.tsx)
新增 `DirectorPanoramaRuntime`：

- 用 `TextureLoader` 读取有效 URL；
- 通过 `BackSide` 反向 sphere 显示环境；
- `raycast={() => undefined}`，不抢占对象选择或 TransformControls；
- URL 变化和卸载时释放 texture；
- 加载失败只更新可见错误反馈，不阻断其他 Director 对象。

### 3.4 非法媒体失败隔离修复

首轮故障隔离验证发现：非法 base64 图片同时触发 Director `TextureLoader` 和
普通 `ImageNode` 的浏览器加载错误。为保持失败路径可观察且不污染浏览器诊断，
新增 [`src/lib/mediaUrl.ts`](../../../src/lib/mediaUrl.ts)：

- 预检明显格式错误的 `data:image/*;base64,...`；
- 普通 `ImageNode` 在预检失败时显示占位态，不发起 `<img>` 加载；
- Director 环境运行时在预检失败时直接进入 `error`，不调用 `TextureLoader`；
- 远程 URL 和格式正确的 data URL 仍走原有加载路径。

这里的预检只处理明显非法输入，不等同于完整 MIME、字节签名或图像解码器
验证；生产级 media ingress/resource provider 仍不在本批范围。

### 3.5 选择状态与 React hooks lint 收口

最终质量门发现 `DirectorDesk` 用 effect 同步修正失效环境输入，会触发
`react-hooks/set-state-in-effect`。修复后选择状态区分三种情况：

- `undefined`：session 尚未被用户明确设置，派生第一个可用候选；
- `null`：用户明确清除，不自动重新选择；
- `string`：保留用户选择；source 失效时派生为空态。

这样保留了默认选择、显式清除和 stale source 清理语义，同时消除了 cascading
render lint error。该修复没有把 session-only 选择写入 Director document、
history 或 localStorage。

## 4. 验证结果

专项脚本：

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch95.py
```

最终结果：`SCRIPT_RECORDED_PASS`。

| 场景 | 结果 |
|---|---|
| Desktop `1440x900` | 4 个直接图片输入；默认投影、切换、清除、stale source 自动清除通过 |
| Mobile `390x844` | Inspector 输入可发现、环境预览 ready、无横向溢出 |
| 项目导出 | session-only panorama 选择不出现在导出的 `scene` keys |
| 非法图片 | Director 对象数量与工作区保持；错误反馈可见；不触发 console/page/request error |
| Desktop diagnostics | `console/page/request = 0/0/0` |
| Mobile diagnostics | `console/page/request = 0/0/0` |
| Failure diagnostics | `console/page/request = 0/0/0` |
| 截图 | `screenshotsWritten=false`；未执行截图识别 |

结构化结果见 [`runtime-audit.json`](runtime-audit.json)。

### 4.1 邻接回归

在上述专项验证后，以下现有 current gates 重新通过：

- Batch 94：Director workspace/drawer focus containment；
- Batch 59：Director asset-library search/preview/add；
- Batch 82：Director local model materialization；
- Batch 92：Director resource owner/lease lifecycle；
- Batch 93：Director final desktop/mobile and cross-batch regression。

Batch 93 刷新了其既有 `runtime-audit.json`，记录了本次 fresh desktop/mobile
owner、project/session snapshot 和 `0/0/0` diagnostics；它仍是 cross-batch
reliability evidence，不是新的 source-exact 证据。

## 5. 与既有边界的关系

- Batch 82/92 的 Director local model resource lifecycle 仍是独立的 session-local
  resource island；本批不把普通画布图片纳入该 lease/provider。
- Batch 93 的 desktop/mobile final regression 和 Batch 94 的 focus containment
  仍是相邻可靠性基线；本批只补媒体 host handoff。
- 普通画布上传、真实文件/Blob ingress、远程资源校验、持久化 asset registry、
  panorama 生成和真实 3D 资源加载均保持未完成。
- 不应把本批通过写成“LibTV 原站已确认的 panorama UI”或“LibTV 使用 R3F 的证据”。

## 6. 停止条件

本批已满足计划中的实现、专项验证和文档落档条件。完成最终质量门并将
checkpoint 推送后，本轮停止；不在本批记录或启动 Batch 96。
