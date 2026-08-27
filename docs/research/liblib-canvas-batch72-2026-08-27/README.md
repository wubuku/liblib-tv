# Batch 72: Director Reference-Aware Delete

> 状态：`PLANNED / IMPLEMENTATION_PENDING`。
>
> 建档日期：2026-08-27。

## 1. 背景

Batch 67-71 已建立 Director strict project document、owner/session、
authored/runtime、project-local history 和 pointer lifecycle。当前最危险的剩余
缺口是删除仍分散在 object、group、track、path、capture 和 local asset action 中：
这些 action 会局部过滤数组，但没有先解析完整引用闭包，也没有保证 accepted delete
只产生一条可 undo/redo 的 Director history。

本批实现 `LIBTV-VR-024` 的 reference-aware delete slice。它是 clone-owned
reliability contract，不把 StoryAI、Open Canvas 或 clone 自身行为写成 LibTV
登录态源站的 exact delete UX。

## 2. 本批决策

```text
typed delete intent
  -> pure inverse-reference plan
  -> complete post-state repair
  -> strict V1 document validation
  -> one atomic store commit or zero mutation
  -> one Director history entry
  -> runtime/session/resource reconciliation
```

- object delete 会修复 group、camera relation、track、path、capture camera ref、
  active camera、selection 和 transient runtime；
- 删除最后一个 camera 一律拒绝为 `DIRECTOR_LAST_CAMERA_REQUIRED`；
- group delete 明确区分 `UNGROUP` 与 `CASCADE`；
- track delete 会处理绑定 path，path delete 会解绑所有 tracks；
- capture delete 不删除已发送的普通 canvas graph node；
- local asset 默认 `BLOCK` in-use 删除；显式 `CASCADE` 才删除实例闭包；
- planner 先生成完整 post-state，再调用 strict document normalizer；任何失败都
  不允许部分写入；
- accepted delete 最多一条 Director history，reject/noop 为零条；
- 普通 canvas graph/history、FrameOS store 和源站 fixture 不属于本批写入范围。

## 3. 交接入口

- [`PLAN.md`](PLAN.md)：实现切片、政策矩阵、fixture 和停止条件；
- `IMPLEMENTATION.md`：实施、失败修正和验证结果，完成后新增；
- `runtime-audit.json`：fresh-page 结构化结果，完成后新增；
- [`../../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)：
  Director command/history/delete 总合同；
- [`../liblib-canvas-batch71-2026-08-27/`](../liblib-canvas-batch71-2026-08-27/)：
  pointer lifecycle 前置实现；
- [`../../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)：
  当前 Director verifier authority。

## 4. 明确不解决

- LibTV 登录态 Director 的 source-exact 删除菜单、确认框、文案和快捷键；
- copy/paste identity remap；
- capture/export/phone async owner freshness；
- local model bytes 的 durable lease、跨项目引用计数和浏览器持久化 history；
- 真实 mesh、panorama 或远端 asset loader；
- 删除普通 canvas source node 或回流 graph result。
