# Batch 58：节点绑定浮层失效收口

> 状态：`SCRIPT_RECORDED_PASS`，实施与 checkpoint 已完成。目标是让图片预览、图片标注、图片元素编辑和 Director
> owner 在节点删除或 active canvas 切换后自动关闭。该批不改变 graph/history、
> Director 内部状态、既有浮层几何或源站未确认的产品反馈。
>
> 对应 backlog：`LIBTV-PAR-011` / `LIBTV-VR-013` 的 UI owner slice。

## 背景

当前 clone 已有多类节点绑定 UI surface，但 ownership 不完整：

- `uiStore` 只保存 `nodeId`，没有保存所属 `canvasId`；
- 图片标注和元素编辑有 selection mismatch 清理；
- 图片预览和 Director 没有统一的节点删除/换画布失效收口；
- graph 删除只负责 descendants、incident edges、selection 和 history；
- UI cleanup 不应伪装成 graph mutation，也不应进入 graph history。

这会导致 owner 节点被删除后仍看到旧预览/Director，或切换画布后旧 surface
残留在新画布上。尤其当不同画布未来出现相同 runtime node ID 时，仅比较
`nodeId` 不足以证明 ownership 仍然有效。

## 本批目标

```text
active canvas id + active node ids + UI owner snapshot
  -> pure invalidation decision
  -> close invalid owners
  -> graph/history unchanged
```

覆盖：

| Owner | 失效条件 | 预期 |
|---|---|---|
| image preview | owner canvas 非 active，或 owner node 不存在 | 关闭预览 |
| image annotate | 同上；并保留已有 selection mismatch 规则 | 关闭标注 |
| image element edit | 同上；并保留已有 selection mismatch 规则 | 关闭元素编辑 |
| Director | 同上 | 关闭 Director |

## 不在本批

- 不把 preview 改成 detached media snapshot；
- 不删除或合并 `uiStore` 的兼容字段；
- 不修改 FrameOS route/store；
- 不修改图片上下浮层的 anchor、尺寸、层级和 action set；
- 不修改 Director 的 R3F、timeline、camera、model library、capture/export；
- 不推断 LibTV 源站的删除确认、媒体资源回收或后端 persistence 语义；
- 不把 UI cleanup 写入 graph history。

## 接力入口

- [`PLAN.md`](PLAN.md)：本批范围、决策和验收标准；
- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：已有源站证据与 clone 边界；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、失败修正、验证和 checkpoint；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：截图识别台账；
- [`runtime-audit.json`](runtime-audit.json)：focused verifier 的 DOM/store 结果。
