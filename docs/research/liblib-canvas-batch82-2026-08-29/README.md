# Batch 82：Director 本地资源生命周期纵切

> 状态：`PLANNED`。
>
> 建档日期：2026-08-29。

## 1. 目标

基于现有 Director `my-models` 本地文件入口，补齐一个有界、诚实的本地资源
生命周期纵切：

```text
File metadata
  -> validate
  -> session materialization
  -> loading
  -> ready / failed / canceled
  -> retry or release
```

本批优先解决“资源当前处于什么状态、谁拥有它、失败后怎么恢复、删除时能否
安全释放”的 clone reliability 问题。它不是 LibTV 原站资源实现的 source-exact
复刻，也不是后端上传系统。

## 2. 当前事实

- `readDirectorLocalModelFiles` 当前过滤 `.fbx/.obj`，然后用 `FileReader` 生成
  `dataUrl`；
- `DirectorLocalModelLibraryItem` 当前只有文件名、data URL、视觉分类和颜色；
- 场景对象始终渲染 `LibraryPropPrimitive`，不解析 OBJ/FBX 文件；
- local model catalog 使用独立的 browser `localStorage` key；
- Director project document 只保存 stable resource reference，不保存 `File`、
  `Blob`、`Object3D` 或 capture bytes；
- 删除已有 resource 会按引用闭包阻断或级联，并在不可达时释放本地模型 catalog
  descriptor。

## 3. 本批边界

### 纳入

- typed local resource descriptor 与 provenance；
- loading/ready/failed/canceled 状态；
- attempt identity、retry、cancel 和 release；
- local model library 的状态反馈与安全删除；
- ready 资源使用真实本地 bytes 做有限的 OBJ/FBX materialization；
- materialization 失败时保留 proxy 或空状态，不伪造成功；
- fresh browser verifier、跨批 gate 和零诊断检查。

### 不纳入

- 远程 provider、云上传、账号资产、跨设备同步；
- 将 data URL 写入 portable Director project JSON；
- 把 data URL 或 Blob URL 称为 durable/stable production asset；
- panorama、视频/音频资源解析；
- Three.js loader 的完整生产级缓存、纹理/材质后处理和大文件优化；
- LibTV 原站 source-exact 资源 UI 或内部协议结论。

## 4. 证据边界

| 类别 | 本批结论 |
|---|---|
| `CLONE_FACT` | 当前 local model 入口与 proxy renderer 的静态事实 |
| `CLONE_DECISION` | 用 typed lifecycle 明确 session-only materialization 与 release |
| `SOURCE_FACT` | 当前没有新增 LibTV Director 资源 source-exact 证据 |
| `UPSTREAM_INSPIRATION` | StoryAI 的 loader/asset ref 分层只作为架构启发 |

## 5. 完成标准

- 不合法或过期的 local resource completion 不得改变当前场景；
- loading 不得显示为 ready；
- failed 可重试，canceled 可重新开始；
- 资源删除在仍有实例引用时按既有 BLOCK/CASCADE 合同处理；
- 释放只发生在没有 live project 引用且没有当前 materialization lease 时；
- ready OBJ/FBX 至少能以真实解析结果替换 proxy；
- parse failure 有可发现反馈且保留上一次可用 proxy；
- 运行专项 verifier、`npm run check`、`npm run docs:check`；
- 更新 current verifier manifest、fixture catalog、verification ledger 和
  Director authority contract，并 commit/push。

