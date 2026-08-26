# Batch 58 计划：节点绑定浮层失效收口

> 建档：2026-08-27（沿用当前批次目录命名）
> 风险：中。修改普通 LibTV route 的 UI lifecycle，但不修改 graph transaction。
> 目标 verifier：`LIBTV-VR-013` 的 node-bound UI slice。

## 1. 缺口与价值

| 缺口 | 当前 clone | 用户影响 | 决策 |
|---|---|---|---|
| preview owner 失效 | preview 只保存 nodeId，删除后可能保留 | 看到已不存在素材的旧预览 | 关闭失效 preview |
| annotate owner 失效 | 只按 selection mismatch 清理 | 删除/换画布后可能残留编辑 surface | 统一按 canvas+node 清理 |
| element-edit owner 失效 | 只按 selection mismatch 清理 | 同上 | 统一按 canvas+node 清理 |
| Director owner 失效 | 只保存 activeDirectorNodeId | 节点删除后全屏工作区仍显示 | 关闭失效 Director |
| canvas identity 缺失 | owner 只有 nodeId | 跨画布同 ID 有误认风险 | owner state 增加 canvasId |
| cleanup 副作用不明确 | route effect 与 graph action 分散 | 可能误写 history 或 graph | pure decision + UI-only close |

## 2. 证据边界

### 已有直接证据

- 当前 clone overlay runtime catalog 已记录四类 owner 的 mount owner 和关闭
  路径；
- delete impact matrix 已把 preview、annotate、element edit、Director 列为
  UI invalidation 关系；
- Batch 52-54 已建立 preview/annotate/element-edit 的 clone fixture；
- Batch 35-50 已建立 Director workspace 的 clone fixture。

### 本批不新增的源站主张

- 本批不是对共享 LibTV 源站执行 destructive delete；
- 不声明源站删除节点后一定关闭 preview 或 Director；
- 不声明源站的 canvas persistence、资源回收或确认文案；
- 本批只修复 clone 的本地 ownership 正确性，并把它标成
  `CLONE_DECISION` / `LOCAL_RUNTIME_INVARIANT`。

## 3. 实施设计

### Slice A：纯 reconciliation

新增 `src/lib/libtvUiOwnerReconciliation.ts`：

- 输入 active canvas ID、active node IDs 和 owner snapshot；
- 输出失效 owner 集合；
- 不访问 Zustand、DOM、history、URL 或浏览器；
- 同一输入得到稳定、可序列化结果；
- canvas mismatch 优先于 node existence，避免跨画布同 ID 误复用。

### Slice B：owner state identity

为 `ImagePreviewState`、`ImageAnnotateState` 和 `ImageElementEditState` 增加
`canvasId`。Director 继续使用 `activeDirectorNodeId`，由 route reconciliation
把它解释为当前 active canvas owner；为避免 store API 扩散，Director 打开时在
route 侧传入 owner snapshot。

### Slice C：普通 LibTV route lifecycle

在 `src/app/page.tsx` 监听 active canvas/node 集合与四类 owner：

1. 运行纯 reconciliation；
2. 只对明确失效 owner 调用对应 close action；
3. 不调用 `setNodes`、`setEdges`、`removeNode`、`setViewport` 或 history action；
4. 保留已有 annotate/element-edit 的单选约束；
5. active canvas 切换和 node 删除都覆盖。

### Slice V：focused Playwright

使用本地 fixture：

- canvas-2 的已有图片节点：preview、annotate、element-edit owner；
- canvas-2 的已有 `script-execution` 节点：Director owner；
- 通过真实 UI 打开 owner；
- 通过 verifier-only store action 删除 owner或切换 active canvas；
- 断言 surface 消失，graph/history/selection 没有被 UI cleanup 改写；
- 覆盖 desktop、mobile、console/page/request errors 和横向溢出。

## 4. 验收标准

### Pure

- owner canvas 与 active canvas 不同：返回 invalid；
- owner node 不在 active canvas：返回 invalid；
- owner canvas 相同且 node 存在：返回 valid；
- null owner 不产生 invalidation；
- 多 owner 输入结果顺序稳定；
- 不对 node label、media URL、selection 或 DOM 做推断。

### Browser

- 删除 preview owner 后 overlay detached；
- 删除 annotate owner 后 annotate surface detached；
- 删除 element-edit owner 后 element-edit surface detached；
- 删除 Director owner 后 Director workspace detached；
- 切换 active canvas 后四类 surface 都 detached；
- cleanup 前后 graph nodes/edges、selection、history 长度不变；
- 现有 image toolbar/edit panel 和 Director 内部既有回归继续通过；
- desktop/mobile 无 overflow，无 console/page/request error。

## 5. 停止条件

- 如果需要决定 source delete confirmation 或 backend resource ownership，保持
  `unknown`，不扩展本批；
- 如果 UI cleanup 触发 graph/history mutation，先修复事务边界；
- 如果现有 node ID/owner shape 无法无损升级，保留兼容边界并记录，不用隐式
  fallback 猜测 canvas；
- 不为证明 cleanup 而新增产品可见 toast、modal 或源站未确认反馈。
