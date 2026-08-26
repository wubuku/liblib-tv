# Batch 57 计划：普通画布连接事务 Slice A/B

> 建档日期：2026-08-27
> 对应 backlog：`LIBTV-PAR-008`
> 对应 verifier：`LIBTV-VR-009`
> 风险等级：中高。连接会直接改变 graph 和 history，但本批只处理结构规则。

## 1. 缺口与价值

| 项目 | 当前 clone | 已有证据 | 价值 | 本批决策 |
|---|---|---|---:|---|
| 方向归一化 | `onConnect` 直接使用收到的 `source/target` | 当前源站 bundle 静态审计确认 target-start 会规范为 source -> target | 5 | 实现纯 normalizer |
| 重复 pair | `addEdge` 无 guard | 当前源站拒绝同向、反向和仅 Handle 不同的 parallel pair | 5 | 实现 unordered pair guard |
| self-loop | `addEdge` 无 guard | 当前源站 programmatic path 显式拒绝 equal node ID | 4 | 实现显式 self guard |
| directed cycle | `addEdge` 无 guard | 当前源站普通非 Reference source 使用 adjacency + DFS guard | 4 | 实现普通有向 cycle guard |
| reject history | 任何 edge 都进入 history | 连接合同要求 reject 零 mutation | 5 | 校验先于 store commit |
| accepted history | 现有 addEdge 一次追加一条 edge | 当前 clone history 可复用，但提交前需稳定 descriptor | 5 | accepted 只产生一个 history snapshot |

## 2. Source fact / Clone fact / Clone decision

### Source fact

- 2026-08-27 production bundle 静态审计确认普通连接存在方向归一化；
- 同向、反向和仅 Handle 不同的 unordered node pair 会被拒绝；
- equal node ID 有显式拒绝分支；
- 普通非 `REFERENCE` source 有 DFS cycle guard；
- 校验失败不会进入 source bundle 的 edge submit 分支。

这些事实来自既有静态审计，不是本批对共享源站画布执行 graph mutation。

### Clone fact

- `src/app/page.tsx` 目前只检查 source/target 非空，然后直接调用
  `canvasStore.addEdge`；
- `src/store/canvasStore.ts` 当前 `addEdge` 直接追加 edge 并写入一次 history；
- React Flow route 当前没有 `isValidConnection`、`onConnectStart` 或
  `onConnectEnd`；
- 所有普通节点都使用左右 `target/source` Handle。

### Clone decision

- 新增单一纯函数模块 `src/lib/libtvGraphConnection.ts`；
- `isValidConnection` 和 `onConnect` 共用同一 validation result；
- store `addEdge` 在当前 canvas 上再次调用同一 pure validator，避免 route
  校验与提交之间出现旁路；
- accepted edge 保留 normalized node/handle identity，使用一次现有 graph history；
- reject/unknown 不调用 store，不产生 edge、selection 或 history 变化；
- domain stage 在本批显式标记为未评估，不对未建模 node action 猜测 allow。

## 3. Fixture 与隔离

### 3.1 本地 fixture

`LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01`：

- 每个 browser scenario 使用新 Page；
- 进入 `canvas-1` 空画布，确认 `0 nodes / 0 edges`；
- 只通过本地 Add Node UI 创建需要的普通 text/image nodes；
- accepted 场景通过真实 React Flow Handle drag；
- pure scenarios 使用合成 Node/Edge payload 调用只读 validator debug hook，
  不写 store；
- 不调用共享源站，不上传、生成、保存、下载或修改远程 graph。

### 3.2 稳定 aliases

| Alias | 本批最小角色 |
|---|---|
| `A_SOURCE` | 普通 source-capable node |
| `B_TARGET` | 普通 target-capable node |
| `C_TARGET` | cycle path 的第三个 node |

aliases 只属于 verifier 报告，生产 runtime ID 继续动态生成。

## 4. 实施步骤与结果

1. 新增 `libtvGraphConnection.ts`，定义 proposed/normalized/result/reason 类型；**已完成**。
2. 实现 missing/dangling/invalid-handle/duplicate/self/cycle 的确定性顺序；**已完成**。
3. 将 `canvasStore.addEdge` 改为只提交通过 pure validator 的 normalized edge；**已完成**。
4. 在 LibTV route 挂载 `onConnectStart`、`onConnectEnd`、
   `isValidConnection` 和共用的 `onConnect` validator；**已完成**。
5. 增加 verifier-only `window.__libtv_store` 与
   `window.__libtv_validate_connection` 诊断入口，便于可重复验证，不提供
   产品 UI 或持久化能力；**已完成**。
6. 新增 desktop/mobile focused Playwright verifier；**已完成**。
7. 记录截图识别结果、runtime audit、失败与修正；**已完成**。
8. 运行 focused、Batch 4-8 graph regressions、相关 image/video regressions、
   `npm run check` 和 `python3 scripts/verify-docs.py`；**已完成**。

## 5. 验收标准

### Pure validator

- source-start 和 target-start 都归一化为 source -> target；
- missing endpoint 返回 `MISSING_ENDPOINT`；
- 不存在 node 返回 `DANGLING_ENDPOINT`；
- 反向或不同 Handle 的已有 pair 返回 `DUPLICATE_NODE_PAIR`；
- equal node ID 返回 `SELF_LOOP`；
- 候选 edge 关闭普通有向路径返回 `DIRECTED_CYCLE`；
- 每个 reject 结果可检查 reason，不返回 silent boolean；
- Reference/domain 未建模保持显式未评估，不伪造 source parity。

### Browser transaction

- accepted real Handle drag 增加 1 edge，保留 normalized handles；
- accepted connection 不改变 selection；
- 一次 undo 删除该 edge，一次 redo 恢复该 edge；
- duplicate/self/cycle rejected 后 nodes、edges、selection 和 history 不变；
- rejected request 不消耗新的 edge identity；
- 不产生 console/page/request errors；
- desktop 与 mobile 不出现 document/body 横向溢出；
- Handle、connection line、DeletableEdge 视觉保持现状。

## 6. 本批结果与停止条件

### 6.1 当前结果

- `scripts/verify-liblib-batch57.py` 已通过；
- 真实 source -> target Handle drag 在 desktop `929x874` 与 mobile
  `390x844` 均增加一条 normalized edge 和一个 history step；
- target-start gesture 的最终 edge 被规范化为 source -> target；
- duplicate、reverse duplicate、parallel-handle duplicate、self-loop 和
  directed cycle 都返回稳定 reject reason；
- rejected store submit 保持 nodes、edges、selection、history 不变；
- 一次 undo 删除 accepted edge，一次 redo 恢复 edge；当前 clone history
  合同下 redo 后 selection 清空；
- overflow、console error、page error 和 request failure 检查通过。

### 6.2 停止条件

- 如果必须决定 Reference、node action、capacity、model switch 才能判断普通
  结构连接，则停止在 `unknown`，把未知写回实施记录；
- 如果 React Flow 的真实 target-start payload 与已有 source 静态证据冲突，
  记录 payload 并停止扩大 swap 规则；
- 如果 rejected path 仍产生 history 或 selection residue，先修事务边界，
  不扩展其他 graph hardening；
- 不因 verifier 难以操作而通过 `addEdge` 直接注入来伪造 Handle drag 成功。

### 6.3 仍未关闭的边界

- source-side invalid line cleanup、toast、cursor、focus 和 timeout；
- `REFERENCE` source exception；
- node action/type compatibility、target capacity、model capability 和
  `switchToModel`；
- import/paste/batch/sync/collaboration 入口；
- 真实后端 persistence。
