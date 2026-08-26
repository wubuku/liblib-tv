# Batch 57 源站与 clone 证据：普通画布连接事务

> 建档日期：2026-08-27
> 证据状态：结构规则有 source static evidence；invalid UI feedback 和
> disposable source interaction 仍未确认。

## 1. 直接可复用的源站证据

本批不重复操作共享源站。复用以下已落档审计：

- [`../open-canvas-2026-08-26/LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md`](../open-canvas-2026-08-26/LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md)
- [`../components/LibTVGraphConnection.contract.md`](../components/LibTVGraphConnection.contract.md)
- [`../LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../LIBTV_GRAPH_TRANSACTION_CATALOG.md)

Source fact：

1. 普通 target-start gesture 会被规范化为 source -> target；
2. unordered node pair 的同向、反向和不同 Handle parallel connection 被拒绝；
3. equal node ID 有 explicit guard；
4. 普通非 `REFERENCE` source 使用 adjacency + DFS 进行 cycle guard；
5. 校验失败不会提交 edge。

这些事实是 bundle/DOM 静态审计结果，不证明 source invalid feedback 的文案、
颜色、cursor、focus 或 timeout。

## 2. 当前 clone 事实（2026-08-27 closeout）

- `page.tsx` 的 `onConnect` 先调用共享 pure validator，再提交 normalized edge；
- React Flow route 已挂载 `isValidConnection`、`onConnectStart` 和 `onConnectEnd`；
- `canvasStore.addEdge` 在 active canvas 上再次执行同一 validator，reject 时直接
  返回且不改变 graph/history；
- accepted addEdge 一次追加 normalized edge，并压入一次 graph history；
- `window.__libtv_store` 与 `window.__libtv_validate_connection` 只用于
  verifier/诊断，不是产品 UI 或后端 persistence API。
- FrameOS route 已有自己的 connection boundary，本批不触碰。

## 3. 本批可推出的 clone 行为

本批只把结构性 source shape 投影到本地 clone：

- normalized source/target/handle identity；
- structural reject reason；
- accepted one-edge/one-history transaction；
- rejected zero graph/history mutation。

本批不能推出：

- LibTV 的真实错误提示、invalid target 样式、连线颜色或交互时序；
- Reference source 的例外；
- source node action/type/capacity/model compatibility；
- import、paste、batch、sync、collaboration；
- real backend edge persistence。

## 4. 截图识别边界

本批截图只用于记录 clone runtime 的 accepted connection 状态；rejected cases
使用 state/history 与 pure validator 断言，避免用截图替代事务证据。
截图首次识别结果写入 [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)；
后续 verifier 复跑应先读该文件，不重复识别相同区域。
