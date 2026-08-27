# Batch 75: Director Clipboard Identity Remap

> 状态：`PLANNED / CLIPBOARD_REMAP_PENDING`。
>
> 建档日期：2026-08-27；上游 checkpoint：`ce7b883`。

## 1. 背景

Batch 67-74 已关闭 Director strict document、owner/session、
authored/runtime、command/history、pointer lifecycle、reference-aware delete、
async result authority 和 browser-local persistence 的 focused slices。

当前最高价值的剩余编辑可靠性缺口是 copy/paste identity remap。StoryAI 上游
已经证明 `Cmd/Ctrl+C`、`Cmd/Ctrl+V` 和 ID map 对重复摆位有直接 UX 价值，
Open Canvas 也提供 two-pass ID map 与内部关系闭包的方法；但两者都不能直接
覆盖当前 clone 的 typed group、track、motion path、camera relation、resource
reference 和 project-local history。

## 2. 本批边界

本批实现 clone-owned、同一 Director project 内的 session clipboard：

- copy 读取 canonical portable document，不读取 runtime projection；
- selected group 复制 group closure；普通 object selection 复制显式对象；
- object-local track/path 和内部 camera relation 进入 packet；
- paste 为 object/group/track/path/keyframe/anchor 分配新 ID 并 two-pass remap；
- external camera relation detach/freeze；
- stable resource reference alias，local/session bytes 不进入 clipboard；
- capture、`sentNodeId`、selection UI、playhead、panel、history 和 persistence
  metadata 不进入 packet；
- accepted paste 只产生一条 Director history，selection 指向新实体；
- clipboard 只在同一 project 有效，跨 project paste 为 zero-mutation stale。

这不是 LibTV source-exact copy/paste 结论，也不实现系统级跨浏览器 clipboard、
跨 project resource transfer、普通 React Flow graph copy 或 Option-drag。

## 3. 入口

- [`STATIC_AUDIT_2026-08-27.md`](STATIC_AUDIT_2026-08-27.md)：当前代码与上游方法审计；
- [`PLAN.md`](PLAN.md)：实施切片、fixture、验证和停止条件；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施和回归记录；
- [`../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)：正式 identity/history 合同；
- [`../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)：current gate 入口。

