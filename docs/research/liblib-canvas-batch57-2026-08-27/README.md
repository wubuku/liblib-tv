# Batch 57：普通画布连接事务 Slice A/B

> 状态：计划中。
> 对应 backlog：`LIBTV-PAR-008` / `LIBTV-VR-009`。
> 本批只实现结构性连接校验和 React Flow 提交边界，不扩展到
> Reference、domain compatibility、导入同步、持久化或源站错误反馈。

## 目标

把普通 LibTV 画布的连接从“收到 `onConnect` 就追加 edge”收敛为一个可审计的
事务边界：

```text
raw React Flow connection
  -> direction/handle normalization
  -> endpoint / pair / self-loop / cycle validation
  -> accepted one-step edge history
  -> rejected zero graph/history mutation
```

## 本批子范围

| Slice | 内容 | 状态 |
|---|---|---|
| A | 纯连接 normalizer、稳定 reason/result、duplicate/self/cycle guard | 待实施 |
| B | `isValidConnection`、`onConnectStart`、`onConnect`、store commit boundary | 待实施 |

## 明确不做

- 不改变 `<Handle>` 的视觉、尺寸、`+` affordance 或 `DeletableEdge` flow；
- 不实现 Reference source、node action/type、capacity、model switch 或 provider；
- 不实现 import/paste/batch/sync/collaboration；
- 不添加未从源站确认的 toast、invalid color、cursor、focus trap 或反馈时序；
- 不修改 FrameOS route/store；
- 不把 `LibTVGraphDocument.contract.md` 的 document/persistence 设计带入本批；
- 不把 accepted local edge 写成真实 LibTV backend/save 语义。

## 接力入口

- [`PLAN.md`](PLAN.md)：执行步骤和验收标准；
- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：source fact、clone fact 和边界；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实际代码、验证和提交历史；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：本批截图首次识别结果；
- [`../../components/LibTVGraphConnection.contract.md`](../components/LibTVGraphConnection.contract.md)：长期连接合同。
