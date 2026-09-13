# Batch 456 — VR-021 Slice F：Director data/blob 收敛（字节预算 + 租约组合）

> 状态：`IMPLEMENTATION_RECORDED`（media ingress/resource lifecycle 合同
> Slice F；clone-only 字节预算，无 provider/存储/网络；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch456-director-blob-convergence-929-2026-09-14.png`、
> `scripts/verify-liblib-batch456.py`。

## 变更

- **`estimateLibTVDataUrlBytes` / `LIBTV_DIRECTOR_EXPORT_BUDGET_BYTES`
  （libtvMediaLease.ts 新增）**：dataURL base64 → 解码字节估算（含
  padding 变体）；DIRECTOR_BROWSER_EXPORT 克隆专用预算 8 MiB
  （显式非源站限制，§8.2）。
- **`createDirectorCapture` 预算守卫 + 租约获取**：解码字节超预算 →
  拒绝（无节点无租约）；通过则获取 `LOCAL_BYTES` /
  `DIRECTOR_WORKSPACE` 租约，owner 键定为 `${canvasId}/${nodeId}`。
- **delete/lifecycle 组合**：`removeNode` 对被移除节点（含后代）的
  Director 租约执行 **releaseForOwner 恰好一次释放**；undo 恢复图内
  字节但不复活租约（租约不随历史回滚——合同 §10 图历史边界）。
- **诊断暴露**：`__libtv_estimate_data_url_bytes`（page.tsx）、
  `__libtv_director_lease_release_counts`（canvasStore window 块，
  与台账同实例）。

## 验收（verify-liblib-batch456.py，SCRIPT_RECORDED_PASS —— 单 evaluate 原子化）

- 预算内捕获接受（dataURL 在图内）+ 恰好一条 DIRECTOR_WORKSPACE 租约；
- 超预算（8 MiB+1 解码字节）捕获拒绝、零产物；
- 删除节点 → 该 owner 租 releasedCount 恰好 1（ledgerBefore 0 →
  after 1）、租约仍计数 1（不复活）；undo 恢复图内字节；
- 估算器 padding 变体精确（3/0/2 字节）；
- console/pageerror/requestfailed 为 0；无溢出。

## 环境注记

场景与断言合并为单次 evaluate：并行开发者的频繁文件保存会触发
dev server 重编译 + 页面重载，跨 evaluate 的模块级状态（台账）可能
被重置——原子化后不再受影响。

## 后续（VR-021）

Slice G 为授权后真实 materializer adapter。至此 VR-021 clone 侧
runtime 切片 A–F 全部关闭。
