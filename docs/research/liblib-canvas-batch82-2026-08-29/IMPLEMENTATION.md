# Batch 82 实施与验证记录

> 状态：`RECORDED_PASS`。
>
> 实施日期：2026-08-29。
>
> 代码 checkpoint：`8c959de`。

## 1. 实施范围

本批是 `LOCAL_RESOURCE_MATERIALIZATION_FOCUSED_PASS`，目标是为 Director
`my-models` 本地模型入口补齐一个有界、可观察且诚实的本地资源 lifecycle。
它扩展了 Batch 48 的 browser-local descriptor/proxy 路径，但没有把该路径升级
为 LibTV 原站或生产资产系统。

已实施：

- `src/lib/directorLocalResourceLifecycle.ts`
  - typed descriptor/provenance/status；
  - `idle/loading/ready/failed/canceled/released` 状态；
  - attempt/request freshness；
  - retry、cancel、lease retain/release 和安全 release。
- `src/lib/directorLocalModelMaterializer.ts`
  - data URL bytes 解码；
  - Three.js `OBJLoader`/`FBXLoader` 有限本地解析；
  - 可渲染 mesh 检查与尺寸归一化；
  - 失败不伪造 ready，仍保留 proxy；
  - 解析对象的 geometry/material dispose。
- `directorStore`、`DirectorViewport` 和模型库卡片
  - 将资源状态接入场景对象与 UI；
  - 失败/取消后提供 retry；
  - 不把 `File`、`Blob`、`Object3D`、data URL 或 capture bytes 写入 portable
    Director project JSON。

## 2. 验证结果

```bash
node --experimental-strip-types scripts/verify-liblib-batch82.mjs
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch82.py
npm run check
```

以上命令均通过。Batch 82 Playwright fixture 覆盖：

| Slice | 结果 |
|---|---|
| descriptor/provenance | `PASS` |
| valid OBJ materialization | `PASS` |
| loading duplicate guard | `PASS` |
| stale attempt ignored | `PASS` |
| parse failure keeps scene object | `PASS` |
| retry creates a new attempt | `PASS` |
| unsupported extension zero mutation | `PASS` |
| cancel/release | `PASS` |
| model-library status feedback | `PASS` |
| console/page/request diagnostics | `0 / 0 / 0` |

结构化结果见 [`runtime-audit.json`](runtime-audit.json)。

## 3. 合同边界

### 已关闭的 clone-owned slice

- 当前本地 resource 有 typed identity 和 provenance；
- stale completion、duplicate load 和 invalid extension 不污染当前状态；
- failed/canceled 状态可发现并可重新尝试；
- ready OBJ 至少可以替换 proxy 为真实解析 `Object3D`；
- lease 未释放时不会标记 resource `released`；
- portable project JSON 仍只保存稳定 descriptor/reference。

### 仍明确未实现

- 生产级 loader/cache、纹理/材质依赖图和大文件优化；
- 复杂 FBX/纹理/外部依赖的完整 materialization；
- 远程上传、云端资产、跨设备同步和 durable local bytes；
- ordinary LibTV media ingress 的共同 provider/resource registry；
- LibTV 原站 Director 的 source-exact loader、UI、协议和持久化语义。

## 4. 历史关系

Batch 48 是历史的 local catalog/proxy pass，记录“真实 mesh loading 尚未实现”
在当时的正确边界。Batch 82 在不改写历史结果的前提下补齐了有限 OBJ/FBX
materialization；因此后续文档应将两者解释为连续 slices，而不是把 Batch 48
的旧表述当作当前实现事实。
