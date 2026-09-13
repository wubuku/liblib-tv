# Batch 454 — VR-021 Slice D：生成历史/注册资产引用 attach（稳定引用 + 按面来源）

> 状态：`IMPLEMENTATION_RECORDED`（media ingress/resource lifecycle 合同
> Slice D；本地 fixture 数据、无账户/后端声明；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch454-asset-references-929-2026-09-13.png`、
> `scripts/verify-liblib-batch454.py`。

## 变更

- **`canvasStore.attachAssetReferences(profileId, assets, expectedGeneration)`
  （新动作）**：GENERATED_HISTORY_ATTACH / REGISTERED_ASSET_ATTACH 两面的
  引用附加——每资产创建一个 `STABLE_ASSET_REFERENCE` 节点，data 携带
  `mediaReference {assetId, locatorClass, provenance}`（来源按面保留，
  不互相污染）；**每次 attach 恰好一条 graph 历史**；已在画布中引用的
  assetId 跳过（零变更）；校验仅画布/世代（引用 attach 无字节转移，
  §8.1 文件上传顺序不适用——已在实现注记声明）。
- 基数守卫：GENERATED_HISTORY_ATTACH 上界 10 → `MEDIA_CARDINALITY_EXCEEDED`。

## 验收（verify-liblib-batch454.py，SCRIPT_RECORDED_PASS）

- **registered_attach_accepted**：三资产 → 三节点、provenance 单一、
  恰好 +1 历史；
- **resubmit_skips_referenced**：三旧 + 一新 → 跳过三个、仅附新的，
  仍一次事务 +1 历史；
- **cardinality / stale-generation 拒绝**：稳定 reason、零变更；
- console/pageerror/requestfailed 为 0；无溢出。

## 后续（VR-021）

Slice E（Shot 源生命周期：LOCAL_PREVIEW/DURABLE_READY 状态机）、
Slice F（Director data/blob 收敛）。AddNodePanel 的生成历史/资产
picker UI 仍为诚实「未连接」态（该面源站未采样）。
